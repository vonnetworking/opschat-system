from langchain.tools import tool

from logging import getLogger, INFO
logger = getLogger(__name__)
logger.setLevel(INFO)


@tool
def tool_local_ip() -> str:
    """
    Retrieves the local system host name and IP address
    """
    logger.info(">> TOOL USE: tool_local_ip")

    import socket 
    hostname = socket.gethostname()
    ip = socket.gethostbyname(hostname)
    return f"Host info: {hostname}, {ip}"


@tool
def tool_system_time() -> str:
    """
    Retrieves the local system time
    """
    logger.info(">> TOOL USE: tool_system_time")

    from datetime import datetime
    return(f"System time: {str(datetime.now())}")


@tool
def tool_query_program_logs(begin_date: str, end_date: str, prompt: str, application: str=None, ip: str=None, change_id: str=None) -> str:
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
    
    from agents.utils.qdrant import QdrantUtil

    vector_store_util = QdrantUtil()
    intent = {}
    if application:
        intent['application'] = application
    if ip:
        intent['ip'] = ip
    if change_id:
        intent['change_id'] = change_id

    logger.info(">> querying qdrant...")
    try:
        results = vector_store_util.query_data(
            collection_name='opschat_data',
            prompt=prompt,
            intent=intent,
            begin_date=begin_date,
            end_date=end_date
        )
    except Exception as e:
        logger.error(f"ERROR: tool_query_program_logs > error running qdrant query .... {str(e)}")
        return f"ERROR: tool_query_program_logs > error running qdrant query .... {str(e)}"

    return str(results)

        