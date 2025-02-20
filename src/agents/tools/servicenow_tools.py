from typing import List, Dict
from langchain.tools import tool

from logging import getLogger, INFO
logger = getLogger(__name__)
logger.setLevel(INFO)

from agents.utils.servicenow_conn import get_servicenow_client, GlideRecord

@tool
def tool_search_incidents(affected_ci: str) -> str:
    """Search for recent ServiceNow incidents and return their details."""
    client = get_servicenow_client(is_mock=True, mock_data_source='incident')

    gr = client.GlideRecord('incident')
    gr.limit = 100
    gr.add_query("affected_ci", affected_ci)
    gr.query()

    assert gr.has_next()

    fields = [
        "description",
        "short_description",
        "state",
        "u_current_business_impact",
        "u_current_status"
    ]

    incidents = []
    for record in gr:
        incident = {}
        for field in fields:
            try:
                value = getattr(record, field, '')
                incident[field] = str(value) if value is not None else ''
            except Exception as e:
                logger.warning(f"Failed to get field {field}: {str(e)}")
                incident[field] = ''
        
        # Add incident number for reference
        incident['number'] = getattr(record, 'number', '')
        incidents.append(incident)
        
        logger.info(f"Processed incident {incident['number']}")

    logger.info(f"Found {len(incidents)} incidents")

    response = f"Found {len(incidents)} incidents\n{'\n'.join([str(r) for r in incidents])}"

    return response


@tool
def tool_search_change_requests(begin_date: str, end_date: str, affected_ci: str) -> str:
    """Search for ServiceNow change requests and return their details."""
    client = get_servicenow_client(is_mock=True, mock_data_source='change_request')

    gr = client.GlideRecord('change_request')
    gr.limit = 100
    gr.add_query("affected_ci", affected_ci)
    gr.add_query("start_date", begin_date)
    gr.add_query("end_date", end_date)
    gr.query()

    assert gr.has_next()

    fields = [
        "description",
        "short_description",
        "start_date",
        "end_date",
        "work_start",
        "work_end",
        "u_down_time",
        "u_environment",
        "u_status_reason",
    ]

    incidents = []
    for record in gr:
        incident = {}
        for field in fields:
            try:
                value = getattr(record, field, '')
                incident[field] = str(value) if value is not None else ''
            except Exception as e:
                logger.warning(f"Failed to get field {field}: {str(e)}")
                incident[field] = ''
        
        incidents.append(incident)

    logger.info(f"Found {len(incidents)} change requests")

    response = f"Found {len(incidents)} change requests\n{'\n'.join([str(r) for r in incidents])}"

    return response

@tool
def tool_search_cmdb(app_name: str=None, class_name: str=None, ci: str=None):
    """
    Search ServiceNow CMDB database for application and service information.
    """
    pass