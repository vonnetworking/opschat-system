from typing import List
import os
from datetime import datetime

from langchain_aws import ChatBedrock
from langchain_core.language_models import BaseChatModel
from langchain_core.tools.base import BaseTool
from langchain_core.prompts import PromptTemplate

from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
import boto3

from agent.tools import (
    tool_local_ip,
    tool_system_time,
    tool_query_program_logs
)

MODEL_NAME_DEFAULT = 'anthropic.claude-3-5-sonnet-20240620-v1:0'
PROMPT_FILE_DEFAULT = 'MAIN.txt'

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

        prompt = PromptTemplate.from_template(
            template=self.get_prompt_text()
        #).format(system_time=str(datetime.now()))
        # Fixed date to work with the application log
        ).format(system_time='2025-02-01T15:35:31.051465')

        self.app = create_react_agent(self.model, self.tools, prompt=str(prompt), checkpointer=MemorySaver())


    def get_prompt_text(self, file_name=PROMPT_FILE_DEFAULT):
        config_path = os.path.join(os.path.dirname(__file__), "config", file_name)
        with open(config_path, "r") as file:
            return file.read()
        

    def generate_response(self, message: str):
        # Use the agent
        final_state = self.app.invoke(
            {"messages": [{"role": "user", "content": message}]},
            config={"configurable": {"thread_id": 12}}
        )
        response = final_state["messages"][-1].content

        return response
    