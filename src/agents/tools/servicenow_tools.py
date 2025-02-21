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

    if not gr.has_next():
        return "No incidents found"

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

    response = f"Found {len(incidents)} incidents"+('\n'.join([str(r) for r in incidents]))

    return response


@tool
def tool_search_change_requests(begin_date: str, end_date: str, affected_ci: str) -> str:
    """Search for ServiceNow change requests and return their details."""
    client = get_servicenow_client(is_mock=True, mock_data_source='change_request')

    gr: GlideRecord = client.GlideRecord('change_request')
    gr.limit = 100
    gr.add_query("affected_ci", affected_ci)
    gr.add_query("start_date", begin_date)
    gr.add_query("end_date", end_date)
    
    gr.query()

    if not gr.has_next():
        return "No change requests found"

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

    response = f"Found {len(incidents)} change requests"+('\n'.join([str(r) for r in incidents]))

    return response

@tool
def tool_search_cmdb_ci(app_name: str=None, class_name: str=None, ci_id: str=None) -> str:
    """
    Search ServiceNow CMDB Configuration Item (CI) database for application and service information.
    """
    if not any([app_name, class_name, ci_id]):
        raise ValueError("At least one of app_name, class_name, or ci_id must be provided.")

    client = get_servicenow_client(is_mock=True, mock_data_source='cmdb_ci')

    gr = client.GlideRecord('cmdb_rel_ci')
    gr.limit = 20

    if app_name:
        gr.add_encoded_query(f"parent.nameLIKE{app_name}^ORchild.nameLIKE{app_name}")
    if class_name:
        gr.add_encoded_query(f"parent.sys_class_name={class_name}^ORchild.sys_class_name={class_name}")
    if ci_id:
        gr.add_encoded_query(f"parent.u_ci_id={ci_id}^ORchild.u_ci_id={ci_id}")

    gr.query()

    if not gr.has_next():
        return "No CIs found"
    
    fields = [
        "parent.name",
        "parent.sys_id",
        "parent.u_ci_id",
        "parent.sys_class_name",
        "parent.class",
        "type.parent_descriptor",
        "child.u_ci_id",
        "child.sys_id",
        "child.name",
        "child.sys_class_name",
        "child.class",
        "type.child_descriptor",
    ]

    cirels = [{field: getattr(record, field, '') for field in fields} for record in gr]

    logger.info(f"Found {len(cirels)} CIs")

    response = f"Found {len(cirels)} CIs"+('\n'.join([str(r) for r in cirels]))

    return response