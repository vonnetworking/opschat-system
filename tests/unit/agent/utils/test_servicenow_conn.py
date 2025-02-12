import pytest
from unittest.mock import patch

from agent.utils.servicenow_conn import ServiceNowClient, MockServiceNowClient, get_servicenow_client
from pysnc.record import GlideRecord


@pytest.mark.parametrize(
    "is_mock",
    [True, False]
)
def test_get_servicenow_client_mock(is_mock):
    client = get_servicenow_client(is_mock=is_mock)

    assert client
    assert type(client) is ServiceNowClient

def test_mock_client_query():
    client = get_servicenow_client(is_mock=True)

    gr = client.GlideRecord('incident')
    gr.add_query("active", "true")
    gr.query()

    assert gr.has_next()

    for r in gr:
        assert type(r) is GlideRecord