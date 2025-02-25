import pytest
from unittest.mock import patch
from agents.utils.elasticsearch_conn import get_elasticsearch_client, ElasticsearchMock

# Mock data for Elasticsearch search
def get_mock_data():
    return [
        {"field1": "value1", "field2": "value2"},
        {"field1": "value3", "field2": "value4"},
        {"field1": "value5", "field2": "value6"},
    ]

@pytest.fixture
def es_mock():
    es = ElasticsearchMock()
    es.mock_data = get_mock_data()  # Assuming a way to store mock data
    return es

# Fixed patch path to include the full module path
@patch('agents.utils.elasticsearch_conn.get_mock_data', return_value=get_mock_data())
def test_search(mock_get_data, es_mock):
    body = {"query": {"bool": { "must": [{"match": {"field1": "value1"}}]}}}  # Elasticsearch query DSL
    response = es_mock.search(index="test-index", body=body)
    
    expected_response = {"field1": "value1", "field2": "value2"}

    assert response['hits']['total'] == 1
    assert response['hits']['hits'][0]['_source'] == expected_response


def test_get_elasticsearch_client_mock():
    client = get_elasticsearch_client(True)
    assert isinstance(client, ElasticsearchMock)
    assert hasattr(client, 'search')
    assert callable(getattr(client, 'search', None))