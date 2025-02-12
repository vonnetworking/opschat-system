from unittest.mock import patch, MagicMock
from pysnc import ServiceNowClient, TableAPI
from pysnc.record import GlideRecord
from contextlib import contextmanager
import json

MOCK_DATA = {
    'result': [
        {
            'description': 'ASDF 12:12:12 OPCODE JOBFAIL TRACEID Completed Abnormally - Event(ID123) Ver(123.0001) MAXIMUM CONDITION CODE CIID: ABCD; System Name=ABC1; Jobname=JOBTRAC; System Date=12/12/12; System Time=12:12:12;',
            'short_description': 'ASDF 12:12:12 OPCODE JOBFAIL TRACEID Completed Abnormally - Event(ID) Ver(123.0001) MAXIMUM CONDITION CODE CIID: ABCD',
            'state': '7', # can we get a state-value map?
            'u_current_business_impact': '',
            'u_current_status': ''
        },
        {
            'description': 'ASDE 12:12:12 OPCODE JOBFAIL TRACEID Completed Abnormally - Event(ID124) Ver(123.0001) MAXIMUM CONDITION CODE CIID: ABCD; System Name=ABC1; Jobname=JOBTRAC; System Date=12/12/12; System Time=12:12:12;',
            'short_description': 'ASDF 12:12:12 OPCODE JOBFAIL TRACEID Completed Abnormally - Event(ID) Ver(123.0001) MAXIMUM CONDITION CODE CIID: ABCD',
            'state': '7', # can we get a state-value map?
            'u_current_business_impact': '',
            'u_current_status': ''
        }
    ]
}

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
        
        # # Patch the TableAPI constructor
        # with patch('pysnc.client.TableAPI') as MockTableAPI:
        #     MockTableAPI.return_value = mock_table_api
        #     client = ServiceNowClient('mock-instance', ('admin', 'password'))
        #     yield client

        # Create the patcher
        self.patcher = patch('pysnc.client.TableAPI', return_value=self.mock_table_api)
        self.patcher.start()

        # Create the client
        self.client = ServiceNowClient('mock-instance', ('admin', 'password'))

    def __del__(self):
        # Clean up the patch when the mock client is destroyed
        self.patcher.stop()


def get_servicenow_client(is_mock=False):
    if is_mock:
        return MockServiceNowClient(MOCK_DATA).client
    else:
        return ServiceNowClient('test-instance', ('user','pass'))

