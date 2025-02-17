import pytest
from langchain_core.messages.tool import ToolCall, ToolMessage

from agents.tools.servicenow_tools import (
    tool_search_incidents,
    tool_search_change_requests
)


def test_tool_search_incidents():
    args = {
        "affected_ci": "mock-affected-ci"
    }
    tool_call = ToolCall(
        name="tool_search_incidents",
        args = args,
        id="tool-call-id",
        type="tool_call"
    )
    result: ToolMessage = tool_search_incidents.invoke(tool_call)

    assert isinstance(result, ToolMessage), f"Expected a ToolMessage, got {type(result)}"

    content = result.content

    assert content
    assert type(content) is str


def test_tool_search_change_request():
    args = {
        "begin_date": "mock-begin-date",
        "end_date": "mock-end-date",
        "affected_ci": "mock-affected-ci"
    }
    tool_call = ToolCall(
        name="tool_search_change_requests",
        args = args,
        id="tool-call-id",
        type="tool_call"
    )
    result: ToolMessage = tool_search_change_requests.invoke(tool_call)

    assert isinstance(result, ToolMessage), f"Expected a ToolMessage, got {type(result)}"

    content = result.content

    assert content
    assert type(content) is str