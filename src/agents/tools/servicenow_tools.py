from typing import List, Dict
from langchain.tools import tool

from logging import getLogger, INFO
logger = getLogger(__name__)
logger.setLevel(INFO)

from agents.utils.servicenow_conn import get_servicenow_client, GlideRecord


def safe_get_value(record: GlideRecord, field):
    """
    Safely get a value from a GlideRecord
    """
    attr = getattr(record, field, None)
    if attr is not None:
        return attr.get_value()
    return ''


@tool
def tool_search_incidents(application_ci_id: str) -> str:
    """Search for recent ServiceNow incidents and return their details."""
    client = get_servicenow_client(is_mock=True, mock_data_source='incident')

    gr = client.GlideRecord('incident')
    gr.limit = 100
    gr.add_query("affected_ci", application_ci_id)
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
        if str(getattr(record, "cmdb_ci")) != application_ci_id:
            continue
        incident = {}
        for field in fields:
            try:
                incident[field] = safe_get_value(record, field)
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
def tool_search_change_requests(begin_date: str, end_date: str, change_request_number:str=None, application_ci_id: str=None) -> str:
    """
    Search for ServiceNow change requests and return their details.
    Requires a Change Request Number or an Application CI ID.
    """
    client = get_servicenow_client(is_mock=True, mock_data_source='change_request')

    gr: GlideRecord = client.GlideRecord('change_request')
    gr.limit = 100
    gr.add_query("cmdb_ci", application_ci_id)
    gr.add_query("number", change_request_number)
    gr.add_query("start_date", begin_date)
    gr.add_query("end_date", end_date)
    
    gr.query()

    if not gr.has_next():
        return "No change requests found"

    fields = [
        "number",
        "parent",
        "cmdb_ci",
        "description",
        "short_description",
        "u_environment",
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
        if application_ci_id and safe_get_value(record, "cmdb_ci") != application_ci_id:
            continue
        if change_request_number and safe_get_value(record, "number") != change_request_number:
            continue

        incident = {}
        for field in fields:
            try:
                incident[field] = safe_get_value(record, field)
            except Exception as e:
                logger.warning(f"Failed to get field {field}: {str(e)}")
                incident[field] = ''
        
        incidents.append(incident)

    logger.info(f"Found {len(incidents)} change requests")

    response = f"Found {len(incidents)} change requests"+('\n'.join([str(r) for r in incidents]))

    return response

@tool
def tool_search_cmdb_rel_ci(application_ci_id: str) -> str:
    """
    Search ServiceNow CMDB Configuration Item (CI) Relationship database for information on relationships between applications and services.
    """
    #if not any([app_name, class_name, application_ci_id]):
    #    raise ValueError("At least one of app_name, class_name, or application_ci_id must be provided.")

    client = get_servicenow_client(is_mock=True, mock_data_source='cmdb')

    gr = client.GlideRecord('cmdb_rel_ci')
    gr.limit = 20

    # if app_name:
    #     gr.add_encoded_query(f"parent.nameLIKE{app_name}^ORchild.nameLIKE{app_name}")
    # if class_name:
    #     gr.add_encoded_query(f"parent.sys_class_name={class_name}^ORchild.sys_class_name={class_name}")
    if application_ci_id:
        gr.add_encoded_query(f"parent.u_ci_id={application_ci_id}^ORchild.u_ci_id={application_ci_id}")

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

    cirels = [{field: safe_get_value(record, field) for field in fields} for record in gr]
    # cirels = [{field: getattr(record, field, '') for field in fields} for record in gr]

    # Mock data filter
    # if app_name:
    #     cirels = [r for r in cirels if app_name in r['parent.name'] or app_name in r['child.name']]
    # if class_name:
    #     cirels = [r for r in cirels if class_name in r['parent.sys_class_name'] or class_name in r['child.sys_class_name']]
    if application_ci_id:
        cirels = [r for r in cirels if application_ci_id in r['parent.u_ci_id'] or application_ci_id in r['child.u_ci_id']]

    logger.info(f"Found {len(cirels)} CIs")

    response = f"Found {len(cirels)} CIs"+('\n'.join([str(r) for r in cirels]))

    return response


@tool
def tool_search_cmdb_applications(application_ci_id: str) -> str:
    """
    Search ServiceNow CMDB Configuration Item (CI) database for information about system configurations.
    You can use this tool to find application and host information like IP addresses.
    """
    client = get_servicenow_client(is_mock=True, mock_data_source='cmdb_appl')

    gr = client.GlideRecord('cmdb_appl')
    gr.limit = 20

    gr.add_encoded_query(f"u_ci_id={application_ci_id}")

    gr.query()

    if not gr.has_next():
        return "No CIs found"
    
    fields = [
        "u_ci_id",
        "sys_class_name",
        "name",
        "short_description",
        "hosting_servers"
    ]

    appls = [{field: safe_get_value(record, field) for field in fields} for record in gr]

    # Mock data filter
    appls = [r for r in appls if application_ci_id == r['u_ci_id'] or application_ci_id in [rserv['u_ci_id'] for rserv in r['hosting_servers']]]

    logger.info(f"Found {len(appls)} CIs")

    response = f"Found {len(appls)} CIs"+('\n'.join([str(r) for r in appls]))

    return response