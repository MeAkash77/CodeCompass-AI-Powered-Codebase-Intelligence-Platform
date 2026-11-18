from langchain_text_splitters import RecursiveCharacterTextSplitter
from crawler.items import DocChildItem
import re

class ChunkPipeline:
    def __init__(self, chunk_size: int = 800, chunk_overlap: int = 100):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ".", "!", "?"],
        )

    def split_code_blocks(self, text: str):
        """
        Split text into code and normal text blocks.
        Returns list of tuples: (block_text, is_code)
        """
        blocks = text.split("```")
        result = []
        for i, block in enumerate(blocks):
            # Even index = normal text, Odd index = code block
            is_code = i % 2 == 1
            block_text = block.strip()
            if block_text:
                if is_code:
                    # Preserve code block formatting
                    block_text = "```\n" + block_text + "\n```"
                result.append((block_text, is_code))
        return result
    
    def is_valid_chunk(self, chunk: str, min_chars: int = 20) -> bool:
        """Filter out trivial or punctuation-only chunks."""
        clean = re.sub(r"[^\w]", "", chunk)
        return len(clean) >= min_chars

    def process_item(self, item, spider):
        parent = item
        children = []

        blocks = self.split_code_blocks(item["content"])
        chunk_index = 0
        for block_text, is_code in blocks:
            if is_code:
                # Treat entire code block as one chunk
                if self.is_valid_chunk(block_text):
                    children.append(DocChildItem(
                        parent_url=item["url"],
                        chunk_index=chunk_index,
                        content=block_text,
                        metadata={"parent_url": item["url"], "chunk_index": chunk_index}
                    ))
                    chunk_index += 1
            else:
                # Split normal text recursively
                text_chunks = self.splitter.split_text(block_text)
                for tc in text_chunks:
                    if self.is_valid_chunk(tc):
                        children.append(DocChildItem(
                            parent_url=item["url"],
                            chunk_index=chunk_index,
                            content=tc,
                            metadata={"parent_url": item["url"], "chunk_index": chunk_index}
                        ))
                        chunk_index += 1
        return {"parent": parent, "children": children}