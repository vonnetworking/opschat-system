import json
import requests
from typing import List, Dict, Any
from logging import getLogger, INFO, WARNING

logger = getLogger(__name__)
logger.setLevel(WARNING)


class OpsChatLLM:
    def __init__(self, api_base: str): 
        logger.info(f">> KnowChatLLM > api_base: {api_base}")
        self.api_base = api_base

    def chat(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        logger.info(f">>> kwargs: {kwargs}")
        
        # Prepare the request payload
        payload = {
            "model": "openai/opschat-agent-backend",
            "messages": [{"role": m.get("role"), "content": m.get("content")} for m in messages],
            "stream": False
        }
        
        # Set headers
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer mock-data"
        }
        
        # Make the HTTP request
        response = requests.post(
            f"{self.api_base}/v1/chat/completions",
            headers=headers,
            data=json.dumps(payload)
        )
        
        # Raise an exception if the request failed
        response.raise_for_status()
        
        # Return the JSON response
        try:
            return response.json()
        except:
            return response.text