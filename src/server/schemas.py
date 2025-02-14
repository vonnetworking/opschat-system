# this is server_schemas.py
from typing import Optional, List, Union
from pydantic import BaseModel

class ChatMessage(BaseModel):
    role: str
    content: Union[str, List[dict]]

class ChatRequest(BaseModel):
    stream: bool
    max_tokens: Optional[int] = 0
    messages: List[ChatMessage]

class ChatCompletionDelta(BaseModel):
    role: Optional[str] = None
    content: Optional[str] = None

class ChatCompletionChoice(BaseModel):
    index: int
    delta: ChatCompletionDelta
    finish_reason: Optional[str] = None

class ChatCompletionChunk(BaseModel):
    id: str
    object: str
    created: int
    model: str
    system_fingerprint: str
    choices: List[ChatCompletionChoice]