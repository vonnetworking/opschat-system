
import pytest
from unittest.mock import patch

from agents.tools.servicenow_tools import tool_search_incidents

def test_tool_search_incidents():
    response = tool_search_incidents.invoke(None)

    assert response
    assert type(response) is str
    assert "Found" in response and "incidents" in response