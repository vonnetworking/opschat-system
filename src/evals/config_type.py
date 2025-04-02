import os
from pydantic import BaseModel, Field
from typing import Optional


class LLMProvider(BaseModel):
    api_base: Optional[str] = Field(default=os.getenv("API_BASE"))
    model: Optional[str] = Field(default="")
    

class Questions(BaseModel):
    input_filename: str


class Completions(BaseModel):
    save_period: int = Field(default=5)
    llm_provider: LLMProvider


class Evaluations(BaseModel):
    passing_threshold: float = Field(default=4)
    save_period: int = Field(default=5)
    llm_provider: LLMProvider


class ConfigSchema(BaseModel):
    name: Optional[str] = Field(default="")
    version: str
    questions: Questions
    completions: Completions
    evaluations: Evaluations