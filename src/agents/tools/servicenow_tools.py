from typing import List, Dict
from langchain.tools import tool

from logging import getLogger, INFO
logger = getLogger(__name__)
logger.setLevel(INFO)

from agents.utils.servicenow_conn import get_servicenow_client, GlideRecord

@tool
def tool_search_incidents() -> str:
    """Search for recent ServiceNow incidents and return their details."""
    client = get_servicenow_client(is_mock=True, mock_data_source='incident')

    gr = client.GlideRecord('incident')
    gr.limit = 100
    #gr.add_query("active", "true")
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
                # Get field value, default to empty string if not found
                value = getattr(record, field, '')
                # Convert None to empty string for consistency
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