from sentence_transformers import SentenceTransformer, CrossEncoder

_embedder = None
_reranker = None
_summarizer = None

def get_embedder():
    global _embedder
    if _embedder is None:
        _embedder = SentenceTransformer("BAAI/bge-base-en-v1.5")
    return _embedder

def get_reranker():
    global _reranker
    if _reranker is None:
        _reranker = CrossEncoder("BAAI/bge-reranker-base")
    return _reranker


def get_summarizer():
    global _summarizer
    if _summarizer is None:
        _summarizer = SentenceTransformer("all-MiniLM-L6-v2")
    return _summarizer
