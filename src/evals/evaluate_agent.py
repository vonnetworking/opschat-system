import os
import sys
import yaml
import json
from tqdm import tqdm

from dotenv import load_dotenv
load_dotenv()

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

from llama_index.core.evaluation import CorrectnessEvaluator
from llama_index.llms.litellm import LiteLLM
from llama_index.core.llms.llm import LLM


# Paths needed to import app source and config files
data_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "eval-data"))
config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "eval-config"))
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if src_path not in sys.path:
   sys.path.insert(0, src_path)

from evals.config_type import ConfigSchema
from evals.litellm_custom import OpsChatLLM


API_BASE = os.getenv("API_BASE")

def load_config_file(config_file: str) -> dict:
    file_path = os.path.join(config_path, config_file)
    with open(file_path, "r") as f:
        config = yaml.safe_load(f)

    try:
        validated_config = ConfigSchema(**config).model_dump()
        if not validated_config.get("name"):
            validated_config["name"] = config_file.replace(".yaml", "")
        if not validated_config["completions"].get("api_base"):
            validated_config["completions"]["api_base"] = API_BASE
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


def _score_file_name(test_config) -> str:
    return f"scores/{test_config["name"]}.{test_config.get("version")}.scores.json"

def _scorecard_file_name(test_config) -> str:
    return f"summary/{test_config["name"]}.{test_config.get("version")}.summary.json"

def get_llm(provider_config: dict) -> LLM:
    return LiteLLM(
        model=f"bedrock/{provider_config.get("model")}"
    )


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
    llm_client = OpsChatLLM(test_config["completions"]["api_base"])

    save_period = test_config["completions"]["save_period"]
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


def run_evaluations(test_config: dict):
    response_data_file = test_config["completions"]["output_filename"]
    score_file = _score_file_name(test_config)
    test_config["evaluations"]["output_filename"] = score_file

    logger.info(f">> Running evaluations for {response_data_file} -> {score_file}")

    # Continue or Start fresh
    qa_data = load_data_file(score_file)
    if qa_data:
        logger.info(f" >> CONTINUE - Score file exists. Loading from {score_file}")
    else:
        logger.info(f" >> START - Score file does not exist. Loading from {response_data_file}")
        qa_data = load_data_file(response_data_file)
        save_data_file(qa_data, score_file)
    
    llm = get_llm(test_config["evaluations"]["llm_provider"])
    evaluator = CorrectnessEvaluator(
        llm=llm,
        score_threshold=test_config["evaluations"]["passing_threshold"]
    )

    for i, qa in enumerate(tqdm(qa_data)):
        if "score" in qa and "passing" in qa:
            continue
        
        result = evaluator.evaluate(
            query=qa.get("question", ""), 
            response=qa.get("response", ""),
            reference=qa.get("truth")
        )

        qa["passing"] = result.passing
        qa["score"] = result.score
        qa["feedback"] = result.feedback

        # Save to file periodically
        if i % test_config["evaluations"]["save_period"] == 0:
            save_data_file(qa_data, score_file)
                
    save_data_file(qa_data, score_file)


def generate_scorecard(test_config: dict):
    score_file = _score_file_name(test_config)
    qa_data = load_data_file(score_file)

    # Group by score
    score_groups = [str(i) for i in range(1,6)]
    qa_groups = {score: [qa for qa in qa_data if str(qa["score"])[0] == score] for score in score_groups}

    # sort by id
    for score in score_groups:
        qa_groups[score] = sorted(qa_groups[score], key=lambda x: x.get("id"))
    
    # Generate scorecard
    scores={
        score: [qa.get("id") for qa in qa_groups[score]] for score in score_groups
    }

    save_data_file(scores, _scorecard_file_name(test_config))
    return scores


def run_llm_test(config_file_name):
    logger.info(f">>> Running LLM test config {config_file_name}")
    test_config = load_config_file(config_file_name)

    if "name" not in test_config:
        test_config["name"] = config_file_name.replace(".yaml", "")

    run_completions(test_config)

    run_evaluations(test_config)

    score = generate_scorecard(test_config)
    print(json.dumps(score, indent=4))


if __name__ == '__main__':
    if len(sys.argv) < 2:
        config_file = "golden-nuggets.yaml"
    else:
        config_file = sys.argv[1]
    print( run_llm_test(config_file) )