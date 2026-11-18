import os
import psycopg2
import scrapy
from urllib.parse import urlparse
from crawler.items import DocItem
from dotenv import load_dotenv

class DocSpider(scrapy.Spider):
    name = 'doc_spider'
    custom_settings = {
        "CONCURRENT_REQUESTS": 2,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 2,
        "DOWNLOAD_DELAY": 0.1,
        "RANDOMIZE_DOWNLOAD_DELAY": True,
        "HTTPCACHE_ENABLED": True,
        "HTTPCACHE_EXPIRATION_SECS": 86400,
        "HTTPCACHE_STORAGE": "scrapy.extensions.httpcache.FilesystemCacheStorage",
        "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        "MEMUSAGE_LIMIT_MB": 500, 
        "REACTOR_THREADPOOL_MAXSIZE": 10,
        "LOG_LEVEL": "WARNING",
        "DEPTH_LIMIT": 3
    }
    page_map = {}

    def __init__(self, urls_file=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not urls_file:
            raise ValueError("Must provide -a urls_file=<path-to-file>")
        
        if not os.path.exists(urls_file):
            raise FileNotFoundError(f"File not found: {urls_file}")
        
        with open(urls_file, "r", encoding="utf-8") as f:
            urls = []
            self.page_map = {}
            for line in f:
                if "|" in line:
                    page, url = line.strip().split("|")
                    self.page_map[urlparse(url).netloc] = page
                    urls.append(url)
                else:
                    urls.append(line.strip())

        print(f"Starting crawl from: {urls}")
        self.start_urls = urls
        self.allowed_domains = [urlparse(url).netloc for url in urls]
        self.visited = set()

    def load_existing_urls(self, domain):
        """Fetch all existing URLs from the rag_doc_parent table."""
        existing = set()
        try:
            load_dotenv()
            conn = psycopg2.connect(
                dbname=os.getenv("POSTGRES_DB", "rag_doc"),
                user=os.getenv("POSTGRES_USER", "postgres"),
                password=os.getenv("POSTGRES_PASSWORD", "postgres"),
                host=os.getenv("POSTGRES_HOST", "localhost"),
                port=os.getenv("POSTGRES_PORT", "5432"),
            )
            cur = conn.cursor()
            cur.execute(
                """
                SELECT url FROM rag_doc_parent
                WHERE url LIKE %s;
                """,
                (f"%{domain}%",)
            )
            rows = cur.fetchall()
            existing = {r[0] for r in rows}
            cur.close()
            conn.close()
            self.logger.info(f"Loaded {len(existing)} URLs for {domain}")
        except Exception as e:
            self.logger.error(f"Failed to load existing URLs from DB: {e}")
        return existing

    def parse(self, response):
        current_domain = urlparse(response.url).netloc
        # Load domain-specific URLs if not already cached
        if not hasattr(self, "domain_cache"):
            self.domain_cache = {}

        if current_domain not in self.domain_cache:
            self.domain_cache[current_domain] = self.load_existing_urls(current_domain)
            self.logger.info(f"Domain cache created for {current_domain}")
        domain_existing_urls = self.domain_cache[current_domain]

        links = response.css('a::attr(href)').getall()
        for link in links:
            full_url = response.urljoin(link)
            if urlparse(full_url).netloc != urlparse(response.url).netloc:
                continue
            if full_url in self.visited or full_url in domain_existing_urls:
                continue
            self.visited.add(full_url)
            yield response.follow(full_url, callback=self.parse_doc)

    def parse_doc(self, response):
        domain_existing_urls = self.domain_cache.get(urlparse(response.url).netloc, set())

        title_text = response.css('title::text').get(default='').strip()
        section_text = response.css('h1::text').get(default='').strip()
        subsections = response.xpath('//h2 | //dl[contains(@class, "py")]/dt')

        for subsection in subsections:
            subsection_text = subsection.xpath("string()").get(default='').strip()

            # Handle autodoc anchors
            anchor_href = subsection.xpath("./a[@class='headerlink']/@href").get()
            if not anchor_href:
                anchor_href = subsection.attrib.get("id", "")
                if anchor_href:
                    anchor_href = f"#{anchor_href}"
            
            if anchor_href:
                subsection_url = response.url.split('#')[0] + anchor_href
            else:
                subsection_url = response.url

            if subsection_url in domain_existing_urls:
                continue

            # Extract the content following the section or autodoc definition
            subsection_content = []
            for sibling in subsection.xpath("following-sibling::*"):
                if sibling.xpath("self::h2 | self::dl[contains(@class,'py')]/dt"):
                    break
                subsection_content.append(sibling.get())

            content = ''.join(subsection_content).strip()
            
            # Extract all internal cross-page links
            links = []
            for href in subsection.xpath("following-sibling::*//a/@href").getall():
                full = response.urljoin(href)
                # Skip external links (only keep same-domain links)
                if urlparse(full).netloc != urlparse(response.url).netloc:
                    continue
                # Skip non-HTML or irrelevant links
                if not ("#" in href):
                    continue
                # Skip media and static files
                if full.endswith((".png", ".jpg", ".jpeg", ".svg", ".pdf", ".css", ".js")):
                    continue
                links.append(full)

            if content: 
                yield DocItem(
                    url=subsection_url,
                    title=title_text,
                    section=section_text,
                    subsection=subsection_text,
                    content=content,
                    metadata={
                        "page_name": self.page_map[urlparse(subsection_url).netloc],
                        "url": subsection_url,
                        "title": title_text,
                        "section": section_text,
                        "subsection": subsection_text,
                        "linked_urls": list(set(links)),
                    }
                )
            yield from self.parse(response)