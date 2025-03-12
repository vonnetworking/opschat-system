import pytest
from langchain_core.messages.tool import ToolCall, ToolMessage

from agents.tools.elasticsearch_tools import (
    tool_query_program_logs,
    tool_query_program_metrics
)


@pytest.mark.parametrize(
    "begin_date, end_date, application, ip, change_id",
    [
        ("2025-02-01", "2025-02-06", "web_back_end", None, None),
        ("2025-02-01", "2025-02-06", None, "192.168.0.100", None),
        ("2025-02-01", "2025-02-06", None, None, "change-id-123")
    ]
)
def test_tool_query_program_logs(begin_date, end_date, application, ip, change_id):
    args = {
        "begin_date": begin_date,
        "end_date": end_date
    }
    if application:
        args["application"] = application
    if ip:
        args["ip"] = ip
    if change_id:   
        args["change_id"] = change_id
    tool_call = ToolCall(
        name="tool_query_program_logs",
        args=args,
        id="tool-call-id",
        type="tool_call"
    )
    result: ToolMessage = tool_query_program_logs.invoke(tool_call)

    assert isinstance(result, ToolMessage), f"Expected a ToolMessage, got {type(result)}"

    content = result.content
    
    assert content
    assert type(content) is str


def test_tool_query_program_metrics():
    begin_date = "2025-02-01"
    end_date = "2025-02-28"
    application_ci_id = "app-ci-id-123"
    tool_call = ToolCall(
        name="tool_query_program_metrics",
        args={
            "begin_date": begin_date,
            "end_date": end_date,
            "application_ci_id": application_ci_id
        },
        id="tool-call-id",
        type="tool_call"
    )
    result: ToolMessage = tool_query_program_metrics.invoke(tool_call)

    assert isinstance(result, ToolMessage), f"Expected a ToolMessage, got {type(result)}"

    content = result.content
    
    assert content
    assert type(content) is str
    assert "Found" in content