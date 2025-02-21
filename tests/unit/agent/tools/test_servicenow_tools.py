import pytest
from langchain_core.messages.tool import ToolCall, ToolMessage

from agents.tools.servicenow_tools import (
    tool_search_incidents,
    tool_search_change_requests,
    tool_search_cmdb_ci
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

@pytest.mark.parametrize(
    "app_name, class_name, ci_id",
    [
        ("mock-app-name", "mock-class-name", "mock-ci-id"),
        ("mock-app-name", "mock-class-name", None),
        ("mock-app-name", None, None),
    ]
)
def test_tool_search_cmdb_ci(app_name, class_name, ci_id):
    args = {
        "app_name": app_name,
        "class_name": class_name,
        "ci_id": ci_id
    }
    tool_call = ToolCall(
        name="tool_search_cmdb_ci",
        args = args,
        id="tool-call-id",
        type="tool_call"
    )
    result: ToolMessage = tool_search_cmdb_ci.invoke(tool_call)

    assert isinstance(result, ToolMessage), f"Expected a ToolMessage, got {type(result)}"

    content = result.content

    assert content
    assert type(content) is str
