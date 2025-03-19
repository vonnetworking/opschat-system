from pydantic import BaseModel, Field
from typing import Optional


class LLMProvider(BaseModel):
    api_base: Optional[str]
    

class Questions(BaseModel):
    input_filename: str


class Evaluations(BaseModel):
    passing_threshold: float = Field(default=4)
    save_period: int = Field(default=10)
    llm_provider: LLMProvider


class ConfigSchema(BaseModel):
    name: str
    version: str
    save_period: int = Field(default=5)
    questions: Questions
    evaluations: Evaluations