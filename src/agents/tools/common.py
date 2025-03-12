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

