import logging
import os
from time import time
from uuid import uuid4
from fastapi import FastAPI, HTTPException, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from tiktoken import get_encoding

import dotenv
from server.schemas import ChatMessage, ChatRequest, ChatCompletionDelta, ChatCompletionChoice, ChatCompletionChunk
from typing import List, Generator

import uvicorn

from agents.main_agent import MainAgent


MAX_HISTORY_TOKENS = os.getenv("MAX_HISTORY_TOKENS", 4096)


# ------------------------------------------------------------------
# Logging Setup
# ------------------------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

main_agent = MainAgent()

# ------------------------------------------------------------------
# FastAPI Setup
# ------------------------------------------------------------------
app = FastAPI(title="OpsChat API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
router = APIRouter()


def summarize_history(history: str) -> str:
    """Summarizes the conversation history using the LLM."""
    if history:
        return main_agent.generate_conversation_summary({"messages": [{"role": "user", "content": history}]})
    return ""


def truncate_history(messages: list) -> str:
    """Truncates the conversation history to fit within the token budget."""
    history = ""
    history_tokens = 0
    ENCODING = get_encoding("cl100k_base")
 
    for message in messages:
        content = f"{message.role}: {message.content}\n"

        num_tokens = len(ENCODING.encode(content))

        if history_tokens + num_tokens > MAX_HISTORY_TOKENS:
            logger.info("History exceeds token limit, summarizing...")
            return history, True  # Indicate that summarization is needed

        history += content
        history_tokens += num_tokens

    return history, False  # Indicate that summarization is not needed


# Modify extract_message to use ChatRequest
def extract_message(chat_req: ChatRequest) -> str:
    messages = chat_req.messages[:-1]  # Exclude the last message
    history, needs_summary = truncate_history(messages)

    if needs_summary:
        history = summarize_history(history)

    last_message = chat_req.messages[-1]
    logger.info("last_message: %s", last_message)
    if (last_message.role != "user"):
        raise HTTPException(
            status_code=400,
            detail="The last message must be from the user."
        )
    query = last_message.content
    if not query or isinstance(query, list):
        raise HTTPException(status_code=400, detail="The last message does not have text content.")
    assert isinstance(query, str)
    
    # Include history in the query
    final_query = f"{history}\nuser: {query}"
    return final_query


def openai_stream_generator(response_gen: Generator[str, None, None]):
    gen_id: str = uuid4().hex
    logger.info("Beginning to generate streaming response %s", gen_id)

    # Initial payload using Pydantic model
    init_payload = ChatCompletionChunk(
        id=gen_id,
        object="chat.completion.chunk",
        created=int(time()),
        model="opschat",
        system_fingerprint="opschat",
        choices=[
            ChatCompletionChoice(
                index=0,
                delta=ChatCompletionDelta(role="assistant", content=""),
                finish_reason=None
            )
        ]
    )
    yield f"data: {init_payload.model_dump_json()}\n\n"

    # Process response chunks
    for chunk in response_gen:
        logger.info("streaming response chunk: %s", chunk)
        logger.info("type(chunk): %s", type(chunk))

        content = " "
        if isinstance(chunk, str):
            content = chunk
        elif isinstance(chunk, tuple):
            (chunk_type, chunk_content) = chunk
            logger.info("chunk_type: %s", chunk_type)
            logger.info("chunk_content: %s", chunk_content)
            if chunk_type == "updates":
                if "agent" in chunk_content:
                    content = chunk_content["agent"]["messages"][-1].content
                    if chunk_content["agent"]["messages"][-1].tool_calls:
                        for tool_call in chunk_content["agent"]["messages"][-1].tool_calls:
                            content += f"\n### Going to use tool `{tool_call['name']}`."
                elif "tools" in chunk_content:
                    logger.info("tools: %s", chunk_content["tools"])
                    for tool in chunk_content["tools"]["messages"]:
                        content += f"\n### Finished using tool `{tool.name}`."
                logger.info("message: %s", content)

        # Yield the updated chunk using Pydantic model.
        event_payload = ChatCompletionChunk(
            id=gen_id,
            object="chat.completion.chunk",
            created=int(time()),
            model="opschat",
            system_fingerprint="opschat",
            choices=[
                ChatCompletionChoice(
                    index=0,
                    delta=ChatCompletionDelta(content=content),
                    finish_reason=None
                )
            ]
        )
        yield f"data: {event_payload.model_dump_json()}\n\n"

    # Terminate streaming response with a stop message using Pydantic model.
    stop_payload = ChatCompletionChunk(
        id=gen_id,
        object="chat.completion.chunk",
        created=int(time()),
        model="opschat",
        system_fingerprint="opschat",
        choices=[
            ChatCompletionChoice(
                index=0,
                delta=ChatCompletionDelta(),
                finish_reason="stop"
            )
        ]
    )
    yield f"data: {stop_payload.model_dump_json()}\n\n"
    yield "data: [DONE]\n\n"


# Modify helper to summarize conversation by delegating to the agent.
def generate_conversation_title(chat_req: ChatRequest) -> str:
    return main_agent.generate_conversation_summary(chat_req)

@app.post("/v1/chat/completions")
async def chat(chat_req: ChatRequest):
    logger.info('Received chat request: %s', chat_req.model_dump())
    assert chat_req.stream

    if chat_req.max_tokens == 15:
        summary = main_agent.generate_conversation_summary(chat_req)
        gen: Generator = (lambda x: (yield x))(summary)
        return StreamingResponse(
            content=openai_stream_generator(gen),
            media_type="text/event-stream",
            headers={"Transfer-Encoding": "chunked"}
        )

    query: str = extract_message(chat_req)
 
    response_stream = main_agent.stream(
        {"messages": [("user", query)]},
        stream_mode=["updates"],
        config={"configurable": {"thread_id": "dummy"}}
    )
    return StreamingResponse(
        content=openai_stream_generator(response_stream),
        media_type="text/event-stream",
        headers={"Transfer-Encoding": "chunked"}
    )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=1234)