import uuid
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.dto.ask import AskRequest
from app.dto.response import Response
from app.dto.conversation import map_to_dto, ConversationResponse
from app.services import rag_service
from app.db.db import SessionLocal
from app.utils.limiter import limiter
from app.utils.logger import logger
from app.utils.utils import make_response

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/ask", response_model=Response)
@limiter.limit("10/minute")
def ask(query: AskRequest, request: Request, db: Session = Depends(get_db)):
    session_id = request.cookies.get("X-Session-Id")
    if not session_id:
        session_id = str(uuid.uuid4())
        logger.info(f"[Session {session_id}] New session created")
    logger.info(f"[Session {session_id}] Received request")

    rag_service.save_conversation(db, session_id, "User", query.prompt)
    logger.info(f"[Session {session_id}] Save user prompt")

    try:
        result = rag_service.handle_query(db, session_id, query)
        logger.info(f"[Session {session_id}] Retrieved assistant response")
    except Exception as e:
        logger.error(f"[Session {session_id}] Error retrieving assistant response: {e}")
        return make_response(Response(success = False, error = str(e)), session_id, 500)

    # Either handle_query return ConversationHistory or save_conversation return it, migrations
    conversation = rag_service.save_conversation(db, session_id, "Assistant", result.response, result.citations)
    logger.info(f"[Session {session_id}] Save assistant response")
    return make_response(Response(success=True, data=map_to_dto(conversation).model_dump(mode="json")), session_id)

@router.get("/conversations", response_model=Response)
@limiter.limit("20/minute")
def get_all_conversations(request: Request, db: Session = Depends(get_db)):
    session_id = request.cookies.get("X-Session-Id")
    if not session_id:
        session_id = str(uuid.uuid4())
        logger.info(f"[Session {session_id}] New session created")
    logger.info(f"[Session {session_id}] Received request")

    try:
        conversations = rag_service.get_all_conversations(db, session_id)
        logger.info(f"[Session {session_id}] Retrieved {len(conversations)} conversations")
    except Exception as e:
        logger.error(f"[Session {session_id}] Error retrieving conversations: {e}")
        return make_response(Response(success = False, error = str(e)), session_id, 500)
    
    return make_response(Response(
        success=True,
        data=[map_to_dto(conv).model_dump(mode="json") for conv in conversations],
    ), session_id)
