from typing import Any, Optional
from pydantic import BaseModel

class Response(BaseModel):
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None