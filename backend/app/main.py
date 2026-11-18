from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.db.db import SessionLocal
from app.controllers.rag_controller import router
from app.utils.limiter import limiter
from slowapi.errors import RateLimitExceeded
from fastapi.responses import JSONResponse

app = FastAPI(title="CodeCompass Server")
app.state.limiter = limiter
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded. Try again later."}
    )

app.include_router(router, prefix="", tags=["ask"])