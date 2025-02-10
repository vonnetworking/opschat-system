import os, sys
import argparse

# Source paths
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../"))
if src_path not in sys.path:
   sys.path.insert(0,src_path)

from main_agent import Agent

# Logging
import logging
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO  # This will ensure INFO level logs are captured
)
logger = logging.getLogger(__name__)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Query the agent for a response.")
    parser.add_argument("query", type=str, help="The query to send to the agent.")
    
    args = parser.parse_args()

    agent = Agent()
    
    print(f"\n\nRESPONSE:\n{agent.generate_response(args.query)}")