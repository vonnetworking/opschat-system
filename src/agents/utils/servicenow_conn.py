from unittest.mock import patch, MagicMock
from pysnc import ServiceNowClient, TableAPI
from pysnc.record import GlideRecord
from contextlib import contextmanager
import json
import os

SERVICENOW_INSTANCE = os.getenv('SERVICENOW_INSTANCE') or 'test-instance'
SERVICENOW_USER = os.getenv('SERVICENOW_USER') or 'test-user'
SERVICENOW_PASS = os.getenv('SERVICENOW_PASS') or 'test-pass' 

class ServiceNowResponse:
    status_code: int
    text: str
    response: dict
    headers: dict

    def __init__(self, response, status_code, headers=None):
        self.status_code = status_code
        self.response = response
        self.text = str(response)
        self.headers = headers or {
            'X-Total-Count': '1',
            'Content-Type': 'application/json'
        }

    def json(self):
        if isinstance(self.response, str):
            try:
                return json.loads(self.response)
            except:
                return {}
        elif isinstance(self.response, dict):
            return self.response


class MockServiceNowClient:
    def __init__(self, mock_data: dict):
        self.mock_data = mock_data
        self._setup_mock()

    def _setup_mock(self):
        # Create mock response for the TableAPI
        mock_response = ServiceNowResponse(
            status_code=200,
            response=self.mock_data,
            headers={
                'X-Total-Count': '1',
                'Content-Type': 'application/json'
            }
        )
        
        # Create a mock TableAPI
        self.mock_table_api = MagicMock(spec=TableAPI)
        self.mock_table_api._send.return_value = mock_response
        self.mock_table_api.list.return_value = mock_response

        # Create the patcher
        self.patcher = patch('pysnc.client.TableAPI', return_value=self.mock_table_api)
        self.patcher.start()

        # Create the client
        self.client = ServiceNowClient(SERVICENOW_INSTANCE, (SERVICENOW_USER, SERVICENOW_PASS))

    def __del__(self):
        # Clean up the patch when the mock client is destroyed
        self.patcher.stop()


def get_mock_data(data_source: str):
    file_path = os.path.join(os.path.dirname(__file__), "data-templates", f"{data_source}.json")
    
    with open(file_path, "r") as file:
        lines = ''.join(file.readlines())
    
    try:
        jsonl_data = json.loads(lines)
    except Exception as e:
        raise RuntimeError(f"Error loading ServiceNow data template: {file_path}\nError: {str(e)}")

    return {'result': jsonl_data}


def get_servicenow_client(is_mock=False, mock_data_source:str=None):
    """
    Generates a ServiceNow client.
    mock_data_source is required if is_mock is True
    """
    if is_mock:
        if not mock_data_source:
            raise ValueError("mock_data_source is required if is_mock=True")
        return MockServiceNowClient(get_mock_data(mock_data_source)).client
    else:
        return ServiceNowClient(SERVICENOW_INSTANCE, (SERVICENOW_USER, SERVICENOW_PASS))

