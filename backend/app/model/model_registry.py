import os
from dotenv import load_dotenv
from app.model.llama_cpp import LlamaCppModel
from app.model.gemini import GeminiModel

load_dotenv()
MODEL_PROVIDER = os.getenv("MODEL_PROVIDER", "llama_cpp")
LLAMA_MODEL = os.getenv("LLAMA_MODEL", "models/microsoft_Phi-4-mini-instruct-Q4_K_M.gguf")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", None)

_model = None

def get_model():
    global _model
    if _model is None:
        if MODEL_PROVIDER == "llama_cpp":
            _model = LlamaCppModel(LLAMA_MODEL)
        elif MODEL_PROVIDER == "gemini":
            if not GEMINI_API_KEY:
                raise ValueError("GEMINI_API_KEY not set")
            _model = GeminiModel(GEMINI_API_KEY, GEMINI_MODEL)
        else:
            raise ValueError(f"Unknown model provider {MODEL_PROVIDER}")
    return _model
