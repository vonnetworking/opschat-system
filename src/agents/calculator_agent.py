import re
import boto3
from langchain_aws import ChatBedrock
from langchain_core.prompts import PromptTemplate
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.tools.base import BaseTool
from typing import AsyncGenerator
import anyio

ALLOWED_EXPR_PATTERN = re.compile(r'^[0-9+\-*/(). ]+$')

def safe_eval(expr: str) -> str:
    if not ALLOWED_EXPR_PATTERN.match(expr):
        return "Error: Invalid characters."
    try:
        return str(eval(expr, {"__builtins__": {}}, {}))
    except Exception as e:
        return f"Error: {e}"

class CalculatorTool(BaseTool):
    name: str = "calculator"
    description: str = "Evaluates arithmetic expressions safely."
    
    def _run(self, query: str) -> str:
        return safe_eval(query)

def get_llm():
    bedrock_client = boto3.client("bedrock-runtime", region_name="us-east-1")
    return ChatBedrock(
        client=bedrock_client,
        model_id="anthropic.claude-3-5-sonnet-20240620-v1:0",
        model_kwargs={"max_tokens": 2048, "temperature": 0.1},
    )

class CalculatorAgent:
    def __init__(self):
        self.tools = [CalculatorTool()]
        self.model = get_llm()
        prompt = PromptTemplate.from_template("You are a calculator assistant. Evaluate the expression and return the result.")
        self.app = create_react_agent(self.model, self.tools, prompt=str(prompt), checkpointer=MemorySaver())

    def generate_response(self, message: str) -> str:
        final_state = self.app.invoke(
            {"messages": [{"role": "user", "content": message}]},
            config={"configurable": {"thread_id": "dummy"}}
        )
        return final_state["messages"][-1].content

    def stream(self, request: dict, stream_mode=None, config=None):
        if stream_mode is None:
            stream_mode = ["updates"]
        if config is None:
            config = {"configurable": {"thread_id": "dummy"}}
        return self.app.stream(request, stream_mode=stream_mode, config=config)

    async def generate_stream(self, message: str) -> AsyncGenerator[str, None]:
        def sync_stream():
            return list(self.app.stream(
                {"messages": [{"role": "user", "content": message}]},
                config={"configurable": {"thread_id": "dummy"}}
            ))
        chunks = await anyio.to_thread.run_sync(sync_stream)
        for chunk in chunks:
            yield chunk
