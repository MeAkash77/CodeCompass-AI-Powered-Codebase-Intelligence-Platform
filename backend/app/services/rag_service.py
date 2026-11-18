import torch
from app.dto.ask import AskRequest, Ask
from app.model.model_registry import get_model
from app.model.model_loader import get_embedder, get_reranker, get_summarizer
from app.repository.conversation_repository import ConversationRepository
from app.utils.logger import logger
from app.utils.utils import load_config
from sentence_transformers import util
from app.model.model import Model
from sqlalchemy.orm import Session
from sqlalchemy import text


EMBEDDER = get_embedder()
RERANKER = get_reranker()
SUMMARIZER = get_summarizer()
PROMPT_TEMPLATE = load_config("prompt_config.yaml")
TOP_RETR = 20
TOP_RANK = 3

def save_conversation(db: Session, session_id: str, role: str, content: str, citations: list[dict] = []):
    """ Save conversation to repository """
    repo = ConversationRepository(db)
    return repo.save_conversation(session_id, role, content, citations)

def refine_query(llm: Model, user_input: str):
    """ Use LLM to rewrite and expand the user query for better document retrieval """
    template = PROMPT_TEMPLATE["query_rewrite"]
    prompt = f"""
    {template['system_instructions']}

    {template['example']}

    Original: "{user_input}
    Rewritten (faithful and expanded):"
    """ 
    result = llm(prompt, max_tokens=64)
    return result.strip()

def summarize_conversation_history(conversations, max_sentences: int = 4) -> str:
    """ Summarize user-LLM conversation efficiently using embeddings.
    Selects representative sentences to preserve meaning with low memory usage """
    if not conversations:
        return ""
    text = "\n".join([f"{c['role']}: {c['content']}" for c in conversations])
    sentences = [s.strip() for s in text.replace("\n", ". ").split(". ") if len(s.strip()) > 10]
    if not sentences:
        return text

    embeddings = SUMMARIZER.encode(sentences, convert_to_tensor=True, normalize_embeddings=True)
    sim_matrix = util.cos_sim(embeddings, embeddings)
    scores = sim_matrix.mean(dim=1)

    top_indices = torch.topk(scores, k=min(max_sentences, len(sentences))).indices
    summary = ". ".join([sentences[i] for i in sorted(top_indices.tolist())])
    return summary.strip() + "."

def search_similar_documents(db: Session, query: str, top_k: int = 30):
    """ Embed the query and fetch top-k similar docs """

    query_embedding = EMBEDDER.encode(query, normalize_embeddings=True).tolist()
    query_embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"
    
    sql = text("""
        WITH dense AS (
            SELECT
                c.parent_id,
                c.parent_url,
                1 - (c.embedding <=> :embedding) AS dense_score
            FROM rag_doc_chunk c
            ORDER BY c.embedding <=> :embedding ASC
            LIMIT :wide_limit
        ),
        combined AS (
            SELECT
                d.parent_id,
                d.parent_url,
                MAX(d.dense_score) AS hybrid_score
            FROM dense d
            GROUP BY d.parent_id, d.parent_url
            ORDER BY hybrid_score DESC
            LIMIT :limit
        )
        SELECT
            p.title,
            p.url,
            p.content,
            p.meta_data
        FROM combined c
        JOIN rag_doc_parent p ON c.parent_id = p.id
        ORDER BY c.hybrid_score DESC;
    """)
    result = db.execute(sql, {
            "embedding": query_embedding_str,
            "wide_limit": top_k * 3,
            "limit": top_k
        })
    return result.mappings().all()

def rerank_documents(query: str, docs: list[dict], top_k: int = 5):
    """ Rerank retrieved documents using a cross-encoder """
    if not docs:
        return []

    def make_text_for_reranking(doc: dict) -> str:
        meta_text = ""
        if "meta_data" in doc and doc["meta_data"]:
            meta_items = [f"{key}: {val}" for key, val in doc["meta_data"].items()]
            meta_text = " | ".join(meta_items)
        content = doc.get("content", "")
        return f"{meta_text}\n{content}"

    pairs = [(query, make_text_for_reranking(doc)) for doc in docs]
    scores = RERANKER.predict(pairs)
    ranked = sorted(zip(scores, docs), key=lambda x: x[0], reverse=True)

    reranked = [{**doc, "rerank_score": float(score)} for score, doc in ranked[:top_k]]
    return reranked


def handle_query(db: Session, session_id: str, query: AskRequest):
    try:
        llm = get_model()
    except Exception as e:
        raise ValueError(e)
    
    # 1. Refine and expand query
    refined_query = refine_query(llm, query.prompt)
    
    # 2. Retrieve documents
    retrieved_docs = search_similar_documents(db, refined_query, top_k=TOP_RETR)
    reranked_docs = rerank_documents(refined_query, [dict(doc) for doc in retrieved_docs], top_k=TOP_RANK)

    # 3. Build context from reranked docs
    docs_dict = [dict(r) for r in reranked_docs]
    context = "\n\n".join([
        f"{doc['content']}\n\nSource: [{doc['title']}]({doc['url']})"
        for doc in docs_dict
    ])

    # 4. Retrieve and summarize last few conversations
    repo = ConversationRepository(db)
    latest_conversations = repo.get_top_n_conversations(session_id, n=5)
    latest_conv_summary = summarize_conversation_history(
        [conv.__dict__ for conv in latest_conversations]
    )

    # 5. Apply style hint detection 
    q = query.prompt.lower().strip()
    hints = PROMPT_TEMPLATE['style_hints']
    if any(word in q for word in {"example", "how", "show", "create", "plot", "save"}):
        style_hint = hints['example']
    elif any(word in q for word in {"difference", "vs", "compare"}):
        style_hint = hints['comparison']
    elif any(word in q for word in {"define", "what", "explain"}):
        style_hint = hints['definition']
    elif "list" in q or "available" in q or "options" in q:
        style_hint = hints['list']
    else:
        style_hint = hints['default']

    full_prompt = f"""
    {PROMPT_TEMPLATE['system_instructions']}

    {PROMPT_TEMPLATE['format_instructions']}

    LATEST CONVERSATION SUMMARY:
    {latest_conv_summary}

    FORMATTING GUIDANCE:
    {style_hint}

    DOCUMENTS:
    {context}

    USER QUESTION (original):
    {query.prompt}

    REFINED QUESTION (for context understanding):
    {refined_query}

    {PROMPT_TEMPLATE['answer_guidance']}
    """
    response = llm(full_prompt, query.max_tokens)
    logger.info(f"[Session {session_id}] {refined_query}")

    return Ask(
            response=str(response),
            citations=docs_dict,
            )


def get_all_conversations(db: Session, session_id: str):
    """ Get all conversation history from repository """
    repo = ConversationRepository(db)
    conversations = repo.get_all_conversations(session_id)
    return conversations