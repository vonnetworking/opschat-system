from typing import List, Dict
from langchain.tools import tool

from logging import getLogger, INFO
logger = getLogger(__name__)
logger.setLevel(INFO)

from agents.utils.elasticsearch_conn import get_elasticsearch_client


@tool
def tool_query_program_logs(begin_date: str, end_date: str, application: str=None, ip: str=None, change_id: str=None) -> str:
    """
    This tool will query program log entries based on the provided application details and date periods.
    The following must always be provided to limit the scope of the logs:
        begin_date,
        end_date,
        prompt 
    The following are additional filters that can be added to reduce the scope of the logs:
        application: name of application, 
        ip: ip address of server,
        change_id: related change_id
    """
    logger.info(">> TOOL USE: tool_query_program_logs")

    client = get_elasticsearch_client()

    query = {
        "query": {
            "bool": {
                "must": [
                    {"range": {"timestamp": {"gte": begin_date, "lte": end_date}}}
                ]
            }
        }
    }
    if application:
        query['query']['bool']['must'].append({"match": {"application": application}})
    if ip:
        query['query']['bool']['must'].append({"match": {"ip": ip}})
    if change_id:
        query['query']['bool']['must'].append({"match": {"change_id": change_id}})

    response = client.search(index='obs_app_logs', body=query)

    hits = response['hits']['hits']
    logs = []
    for hit in hits:
        log = hit['_source']
        logs.append(log)

    logger.info(f"Found {len(logs)} logs")

    return f"Found {len(logs)} logs"+('\n'.join([str(l) for l in logs]))
    

@tool
def tool_query_program_metrics(begin_date: str, end_date: str, application_ci_id: str):
    """
    This tool will query program metrics based on the provided application_ci_id and date periods.
    """
    logger.info(">> TOOL USE: tool_query_program_metrics")

    client = get_elasticsearch_client()

    query = {
        "query": {
            "bool": {
                "must": [
                    {"range": {"timestamp": {"gte": begin_date, "lte": end_date}}},
                    {"match": {"application_ci_id": application_ci_id}}
                ]
            }
        }
    }

    response = client.search(index='obs_app_metrics', body=query)

    hits = response['hits']['hits']
    metrics = []
    for hit in hits:
        metric = hit['_source']
        metrics.append(metric)

    logger.info(f"Found {len(metrics)} metrics")

    return f"Found {len(metrics)} metrics"+('\n'.join([str(m) for m in metrics]))