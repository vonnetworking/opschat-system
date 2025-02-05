from typing import List

from langchain.agents import create_react_agent
from langchain.tools import tool
from langchain_aws import ChatBedrock
from langchain_core.language_models import BaseChatModel
from langchain_core.tools.base import BaseTool

from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
import boto3

MODEL_NAME_DEFAULT = 'anthropic.claude-3-5-sonnet-20240620-v1:0'

# Define the tools for the agent to use
@tool
def search(query: str):
    """Call to surf the web."""
    # This is a placeholder, but don't tell the LLM that...
    if "sf" in query.lower() or "san francisco" in query.lower():
        return "It's 60 degrees and froggy."
    return "It's 90 degrees and sunny."

def get_llm():
    bedrock_client = boto3.client(
        service_name="bedrock-runtime",
        region_name="us-east-1",
    )
    bedrock_llm = ChatBedrock(
        model=MODEL_NAME_DEFAULT,
        client=bedrock_client,
        model_kwargs={'temperature': 0}
    )
    return bedrock_llm


class Agent:
    tools: List[BaseTool]
    model: BaseChatModel

    def __init__(self):
        self.tools = [search]
        self.model = get_llm()

        self.app = create_react_agent(self.model, self.tools, checkpointer=MemorySaver())

    def generate_response(self, message: str):
        # Use the agent
        final_state = self.app.invoke(
            {"messages": [{"role": "user", "content": message}]},
            config={"configurable": {"thread_id": 0}}
        )
        response = final_state["messages"][-1].content

        return response
    