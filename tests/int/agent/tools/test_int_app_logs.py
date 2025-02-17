import pytest
from langchain_core.messages.tool import ToolCall, ToolMessage

from agents.tools.common import (
    tool_query_program_logs
)


@pytest.mark.parametrize(
    "begin_date, end_date, prompt, application, ip",
    [
        ("2025-02-01", "2025-02-06", "application status", "web_back_end", None),
        ("2025-02-01", "2025-02-06", "application status", None, "192.168.1.1"),
        ("mock-data", "mock-data", "mock-data", None, None)
    ]
)
def test_tool_query_program_logs(begin_date, end_date, prompt, application, ip):
    # Call the actual function
    args = {
            "begin_date": begin_date,
            "end_date": end_date,
            "prompt": prompt
    }
    if application:
        args["application"]=application
    if ip:
        args["ip"]=ip
    tool_call = ToolCall(
        name="tool_query_program_logs",
        args=args,
        id="tool-call-id",
        type="tool_call"
    )
    result: ToolMessage = tool_query_program_logs.invoke(tool_call)

    # Assertions
    assert isinstance(result, ToolMessage), f"Expected a ToolMessage, got {type(result)}"

    content = result.content
    
    assert content
    assert type(content) is str