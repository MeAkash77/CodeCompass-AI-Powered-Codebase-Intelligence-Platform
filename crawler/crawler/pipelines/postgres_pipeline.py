import json
import os
import psycopg2
from psycopg2.extras import execute_batch

from crawler.items import DocItem
from dotenv import load_dotenv


class PostgresPipeline:
    def open_spider(self, spider):
        load_dotenv()
        self.conn = psycopg2.connect(
            dbname=os.getenv("POSTGRES_DB", "rag_doc"),
            user=os.getenv("POSTGRES_USER", "postgres"),
            password=os.getenv("POSTGRES_PASSWORD", "postgres"),
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=os.getenv("POSTGRES_PORT", "5432"),
        )
        self.conn.set_client_encoding('UTF8')
        self.cur = self.conn.cursor()
        self.children_batch = []
        self.parent = DocItem()
        self.batch_size = 20

    def close_spider(self, spider):
        if self.parent:
            parent_id = self._comit_parent(spider)
        if self.children_batch and parent_id != None:
            self._commit_children_batch(spider, parent_id)
        self.cur.close()
        self.conn.close()

    def process_item(self, item, spider):
        self.parent = item["parent"]
        parent_id = self._comit_parent(spider)
        if parent_id != None:
            self.children_batch = item["children"]
            self._commit_children_batch(spider, parent_id)
        self.parent.clear()
        self.children_batch.clear()

    def _comit_parent(self, spider):
        try:
            self.cur.execute(
                """
                INSERT INTO rag_doc_parent
                (url, title, section, subsection, content, meta_data)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (url, subsection)
                    DO UPDATE SET
                        title = EXCLUDED.title,
                        section = EXCLUDED.section,
                        content = EXCLUDED.content,
                        meta_data = EXCLUDED.meta_data
                RETURNING id;
                """,
                (
                    self.parent.get("url"),
                    self.parent.get("title"),
                    self.parent.get("section"),
                    self.parent.get("subsection"),
                    self._clean_text(self.parent.get("content", "")),
                    json.dumps(self.parent.get("metadata")),
                )
            )
            self.conn.commit()
            row = self.cur.fetchone()
            return row[0] if row else None
        except  Exception as e:
            # Reset broken transaction and log the error
            spider.logger.error(f"Postgres insert parent failed: {e}")
            self.conn.rollback()
        return None
    
    def _commit_children_batch(self, spider, parent_id):
        try:
            execute_batch(
                self.cur,
                """
                INSERT INTO rag_doc_chunk
                (parent_id, parent_url, chunk_index, content, meta_data, embedding)
                VALUES (%(parent_id)s, %(parent_url)s, %(chunk_index)s,
                        %(content)s, %(meta_data)s, %(embedding)s)
                ON CONFLICT (parent_id, chunk_index)
                    DO UPDATE SET
                        content = EXCLUDED.content,
                        parent_url = EXCLUDED.parent_url,
                        meta_data = EXCLUDED.meta_data,
                        embedding = EXCLUDED.embedding;
                """,
                (
                    {
                        "parent_id": parent_id,
                        "parent_url": item.get("parent_url"),
                        "chunk_index": item.get("chunk_index"),
                        "content": self._clean_text(item.get("content", "")),
                        "meta_data": json.dumps(item.get("metadata")),
                        "embedding": item.get("embedding"),
                    }
                    for item in self.children_batch
                )
            )
            self.conn.commit()
        except  Exception as e:
            # Reset broken transaction and log the error
            spider.logger.error(f"Postgres insert children batch failed: {e}")
            self.conn.rollback()

    def _clean_text(self, text):
        """Ensure text is UTF-8 safe"""
        if not text:
            return ""
        return text.encode("utf-8", errors="ignore").decode("utf-8", errors="ignore")