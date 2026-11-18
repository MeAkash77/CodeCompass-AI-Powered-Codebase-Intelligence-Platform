from fastapi.responses import JSONResponse
import yaml
from app.dto.response import Response

def make_response(content: Response, session_id: str, code: int = 200):
    response = JSONResponse(
        status_code=code,
        content=content.model_dump()
    )
    response.set_cookie(
        key="X-Session-Id",
        value=session_id,
        httponly=True,
        secure=False,
        samesite="lax", 
        max_age=60 * 60 * 24 * 3,
    )
    return response


def load_config(filename):
    with open("./app/config/"+filename, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)