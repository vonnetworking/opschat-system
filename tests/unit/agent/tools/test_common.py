import pytest
from unittest.mock import patch
from datetime import datetime

from agents.tools.common import (
    tool_local_ip, 
    tool_system_time
)

def test_tool_local_ip():
    with patch('socket.gethostname') as mock_gethostname, patch('socket.gethostbyname') as mock_gethostbyname:
        # Setup the mock return values
        mock_gethostname.return_value = 'mock-hostname'
        mock_gethostbyname.return_value = '192.168.0.1'
        
        # Call the function
        result = tool_local_ip.invoke(None)
        
        # Assert the expected output
        assert type(result) is str
        expected_output = "Host info: mock-hostname, 192.168.0.1"
        assert result == expected_output
    

def test_tool_system_time():
    result = tool_system_time.invoke(None)
    
    # Expected string
    assert type(result) is str
    expected_output = "System time: "
    assert result.startswith(expected_output)
