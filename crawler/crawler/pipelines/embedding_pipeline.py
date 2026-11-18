from sentence_transformers import SentenceTransformer

class EmbeddingPipeline:
    def __init__(self, model_name: str = "BAAI/bge-base-en-v1.5"):
        self.model = SentenceTransformer(model_name)

    def process_item(self, item, spider):
        children = item["children"]
        texts = []
        for chunk_item in children:
            texts.append(chunk_item['content'].strip())

        # Generate embedding
        embeddings = self.model.encode(texts, normalize_embeddings=True).tolist()

        for chunk_item, embedding in zip(children, embeddings):
            chunk_item["embedding"] = embedding
        return item
