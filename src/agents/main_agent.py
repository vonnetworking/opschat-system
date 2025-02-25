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

from agents.tools.common import (
    tool_local_ip,
    tool_system_time,
    tool_query_program_logs
)
from agents.tools.servicenow_tools import ( 
    tool_search_incidents,
    tool_search_change_requests,
    tool_search_cmdb_ci
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


class MainAgent:
    tools: List[BaseTool]
    model: BaseChatModel

    def __init__(self):
        self.tools = [
            tool_local_ip, 
            tool_system_time, 
            tool_query_program_logs,
            tool_search_incidents,
            tool_search_change_requests,
            tool_search_cmdb_ci
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

    def generate_conversation_summary(self, chat_req) -> str:
        # Directly invoke the LLM with a specific summary prompt
        prompt = PromptTemplate.from_template(
            "Summarize this conversation in less than 15 tokens, starting with an emoji: {chat_req}"
        )
        message = prompt.format(chat_req=str(chat_req))

        # Invoke the LLM directly
        response = self.model.invoke(message)
        return response.content

    # New stream method that delegates to self.app.stream
    def stream(self, request: dict, stream_mode=None, config=None):
        if stream_mode is None:
            stream_mode = ["updates"]
        if config is None:
            config = {"configurable": {"thread_id": "dummy", "checkpoint_ns": "dummy", "checkpoint_id": "dummy"}}
        return self.app.stream(request, stream_mode=stream_mode, config=config)

    # Optional: async generate_stream method if needed by your implementation.
    async def generate_stream(self, message: str):
        import anyio
        def sync_stream():
            return list(self.app.stream(
                {"messages": [{"role": "user", "content": message}]},
                config={"configurable": {"thread_id": "dummy", "checkpoint_ns": "dummy", "checkpoint_id": "dummy"}}
            ))
        chunks = await anyio.to_thread.run_sync(sync_stream)
        for chunk in chunks:
            yield chunk
