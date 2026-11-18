import re
import html2text
from lxml import html


class CleanPipeline:
    def __init__(self):
        self.html2text = html2text.HTML2Text()
        self.html2text.ignore_links = False
        self.html2text.inline_links = True
        self.html2text.ignore_images = False
        self.html2text.bypass_tables = False
        self.html2text.ignore_tables = False
        self.html2text.images_to_alt = False
        self.html2text.body_width = 0  
        self.html2text.single_line_break = True
        self.html2text.mark_code = True

    def _clean_html(self, html_text: str, response_url = None) -> str:
        try:
            if response_url:
                html_text = self._make_links_absolute(html_text, response_url)

            markdown = self.html2text.handle(html_text)
            markdown = re.sub(r'\[code\]\s*', '```\n', markdown)
            markdown = re.sub(r'\s*\[/code\]', '\n```', markdown)
            return markdown.strip()

        except Exception as e:
            print(f"LangChain HTML cleaning failed for {response_url}: {e}")

        return html_text
    
    def _make_links_absolute(self, html_text, base_url) -> str:
        try:
            tree = html.fromstring(html_text)
            tree.make_links_absolute(base_url)
            return str(html.tostring(tree, encoding="unicode"))
        except Exception:
            return html_text

    def _remove_sphinx_artifacts(self, text: str) -> str:
        # Remove Sphinx auto-generated docstring artifacts
        patterns = [
            r'\*?\[\*\]:.*PEP\s*\d+',
            r'Deprecated since version [\d\.]+',
        ]
        for p in patterns:
            text = re.sub(p, '', text, flags=re.IGNORECASE)
        return text.strip()

    def process_item(self, item, spider):
        if "content" in item and item["content"]:
            text = self._clean_html(item["content"], item["url"])
            text = self._remove_sphinx_artifacts(text)
            item["content"] = text
        return item
