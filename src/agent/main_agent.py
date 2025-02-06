from typing import List

from langchain_aws import ChatBedrock
from langchain_core.language_models import BaseChatModel
from langchain_core.tools.base import BaseTool

from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
import boto3

from agent.tools import (
    tool_local_ip,
    tool_system_time,
    tool_query_program_logs
)

MODEL_NAME_DEFAULT = 'anthropic.claude-3-5-sonnet-20240620-v1:0'

# Define the tools for the agent to use


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
        self.tools = [
            tool_local_ip, 
            tool_system_time, 
            tool_query_program_logs
        ]
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
    