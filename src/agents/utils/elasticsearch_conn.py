#from elasticsearch import Elasticsearch
from typing import List

from agents.utils.mock_tools import get_mock_data

class ElasticsearchMock:
    """Mock class for Elasticsearch."""

    def __init__(self):
        pass

    def search(self, index: str, body: dict):
        """Search the Elasticsearch index."""
        data = get_mock_data(index)
        result = []
        match_reqs = body['query']['bool']['must']
        for item in data:
            match = True
            for req in match_reqs:
                if 'match' in req:
                    key = list(req['match'].keys())[0]
                    if key not in item or item[key] != req['match'][key]:
                        match = False
                        break
                elif 'range' in req:
                    key = list(req['range'].keys())[0]
                    if key not in item or item[key] < req['range'][key]['gte'] or item[key] > req['range'][key]['lte']:
                        match = False
                        break
            if match:
                result.append(item)    

        return {'hits': {'hits': result}}


def get_elasticsearch_client(is_mock: bool = True):
    """Return an Elasticsearch client."""
    return ElasticsearchMock()
