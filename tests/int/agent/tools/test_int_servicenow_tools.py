import pytest
from langchain_core.messages.tool import ToolCall, ToolMessage

from agents.tools.servicenow_tools import (
    tool_search_incidents
)


