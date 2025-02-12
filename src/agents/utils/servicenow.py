from unittest.mock import patch, MagicMock
from pysnc import ServiceNowClient, TableAPI
from contextlib import contextmanager
import json

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
            'X-Total-Count': '1',  # Default to 1 for single result
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

@contextmanager     # Allows us to use the function using `with`
def mock_servicenow():
    # Create mock response for the TableAPI
    mock_response = ServiceNowResponse(
        status_code=200,
        response={
            'result': [
                {
                    'sys_id': '1234',
                    'number': 'INC0001',
                    'active': 'true'
                },
                {
                    'sys_id': '1235',
                    'number': 'INC0002',
                    'active': 'false' 
                }
            ]
        },
        headers={
            'X-Total-Count': '1',
            'Content-Type': 'application/json'
        }
    )
    
    # Create a mock TableAPI
    mock_table_api = MagicMock(spec=TableAPI)
    mock_table_api._send.return_value = mock_response
    mock_table_api.list.return_value = mock_response
    
    # Patch the TableAPI constructor
    with patch('pysnc.client.TableAPI') as MockTableAPI:
        MockTableAPI.return_value = mock_table_api
        client = ServiceNowClient('mock-instance', ('admin', 'password'))
        yield client

# Usage:
with mock_servicenow() as client:
    gr = client.GlideRecord('incident')
    gr.add_query("active", "true")
    gr.query()
    for r in gr:
        print(f"\n\n>> R: {type(r)} {r}")