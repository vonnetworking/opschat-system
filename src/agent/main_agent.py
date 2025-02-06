from typing import List
import socket

from langchain.tools import tool
from langchain_aws import ChatBedrock
from langchain_core.language_models import BaseChatModel
from langchain_core.tools.base import BaseTool

from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
import boto3

from logging import getLogger, INFO
logger = getLogger(__name__)
logger.setLevel(INFO)

MODEL_NAME_DEFAULT = 'anthropic.claude-3-5-sonnet-20240620-v1:0'

# Define the tools for the agent to use
@tool
def tool_local_ip():
    """
    Retrieves the local system host name and IP address
    """
    logger.info("tool_local_ip")
    hostname = socket.gethostname()
    ip = socket.gethostbyname(hostname)
    return f"Host info: {hostname}, {ip}"


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
        self.tools = [tool_local_ip]
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
    