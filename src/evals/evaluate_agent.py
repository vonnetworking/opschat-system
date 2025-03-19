import os
import sys
import argparse
import yaml
import json
from tqdm import tqdm

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

from dotenv import load_dotenv
load_dotenv()

# Paths needed to import app source and config files
data_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src", "evals", "data"))
config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src", "evals", "test-config"))
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if src_path not in sys.path:
   sys.path.insert(0, src_path)

from server.main import app
from evals.config_type import ConfigSchema
from evals.litellm_custom import OpsChatLLM


def load_config_file(config_file: str) -> dict:
    file_path = os.path.join(config_path, config_file)
    with open(file_path, "r") as f:
        config = yaml.safe_load(f)

    try:
        validated_config = ConfigSchema(**config).model_dump()
        if not validated_config.get("name"):
            validated_config["name"] = config_file.replace(".yaml", "")
        if not validated_config["completions"].get("api_base"):
            validated_config["completions"]["api_base"] = os.getenv("API_BASE")
        logger.info(">> Config file is valid")
        return validated_config
    except Exception as e:
        logger.error(">> Invalid config file", e)
        raise e


def load_data_file(source_file: str):
    file_path = os.path.join(data_path, source_file)
    try:
        with open(file_path, 'r') as f:
            file_data = f.read()
            qt_data = json.loads(file_data)
            return qt_data
    except:
        return None


def save_data_file(data, target_file):
    file_path = os.path.join(data_path, target_file)
    
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)
        
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)


def run_completions(test_config):
    qt_data_file=test_config["questions"]["input_filename"]
    response_file = f'responses/{test_config["name"]}.{test_config.get("version")}.responses.json'

    if not test_config.get("completions"):
        test_config["completions"] = {}
    test_config["completions"]["output_filename"] = response_file

    logger.info(f" >> Running completions for {qt_data_file} -> {response_file}")

    # Continue or Start fresh
    qt_data = load_data_file(response_file)
    if qt_data:
        logger.info(f" >> CONTINUE - Response file exists. Loading from {response_file}")
    else:
        logger.info(f" >> START - Response file does not exist. Loading from {qt_data_file}")
        qt_data = load_data_file(qt_data_file)
        save_data_file(qt_data, response_file)

    # Perform completions on one question at a time
    from langchain_core.prompts import ChatPromptTemplate

    llm_client = OpsChatLLM(test_config["completions"]["api_base"])

    save_period = test_config["save_period"]
    for i, qt in enumerate(tqdm(qt_data)):
        if "response" in qt:
            continue
    
        payload =[dict(role="user", content=qt.get('question'))]
        
        response = llm_client.chat(messages=payload)

        try:
            message = response
            #logging.info(">> LLM RSESPONSE", message)
            qt["response"] = message

        except Exception as e:
            logging.error(">> ERROR: ", e)
            logging.error(">> API RESPONSE: ", response)
            continue

        # Save to file periodically
        if i % save_period == 0:
            save_data_file(qt_data, response_file)
    
    save_data_file(qt_data, response_file)


def run_evaluations(test_config):
    pass


def run_llm_test(config_file_name):
    logger.info(f">>> Running LLM test config {config_file_name}")
    test_config = load_config_file(config_file_name)

    if "name" not in test_config:
        test_config["name"] = config_file_name.replace(".yaml", "")

    run_completions(test_config)

    run_evaluations(test_config)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        config_file = "golden-questions.py"
    else:
        config_file = sys.argv[1]
    print( run_llm_test(config_file) )