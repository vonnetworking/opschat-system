
from agents.utils.elasticsearch_conn import get_elasticsearch_client, ElasticsearchMock

def test_get_elasticsearch_client_mock():
    client = get_elasticsearch_client(True)
    assert isinstance(client, ElasticsearchMock)
    assert hasattr(client, 'search')
    assert callable(getattr(client, 'search', None))