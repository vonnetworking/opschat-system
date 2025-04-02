import os
import sys
import pytest
import json
import yaml
from unittest.mock import patch, MagicMock

from dotenv import load_dotenv
load_dotenv()

src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..","..","..", "src"))
if src_path not in sys.path:
   sys.path.insert(0, src_path)
from evals.evaluate_agent import run_completions, load_config_file, load_data_file, save_data_file
from evals.litellm_custom import OpsChatLLM

@pytest.fixture
def mock_config():
    return {
        "name": "test_completion",
        "version": "1.0",
        "questions": {
            "input_filename": "test_questions.json"
        },
        "completions": {
            "save_period": 1,
            "api_base": os.getenv("API_BASE")
        },
        "evaluations": {
            "save_period": 1
        }
    }

@pytest.fixture
def mock_questions():
    return [
        {"question": "What is the capital of France?"},
        {"question": "Who wrote 'To Kill a Mockingbird'?"}
    ]

@pytest.fixture
def mock_responses():
    return [
        {"question": "What is the capital of France?", "response": "The capital of France is Paris."},
        {"question": "Who wrote 'To Kill a Mockingbird'?", "response": "Harper Lee wrote 'To Kill a Mockingbird'."}
    ]

@patch('evals.evaluate_agent.load_config_file')
@patch('evals.evaluate_agent.load_data_file')
@patch('evals.evaluate_agent.save_data_file')
def test_run_completions(mock_save_data, mock_load_data, mock_load_config, 
                         mock_config, mock_questions):
    # Set up mocks
    mock_load_config.return_value = mock_config
    mock_load_data.side_effect = [None, mock_questions]  # First None for existing responses, then questions

    # Run the function
    run_completions(mock_config)

    # Assertions
    assert mock_load_data.call_count > 0
    assert mock_save_data.call_count > 0

    # Check if the final saved data matches the expected responses
    final_call_args = mock_save_data.call_args_list[-1][0]
    
    # Output data
    assert all([type(m) is dict for m in final_call_args[0]])
    assert all(['question' in m and 'response' in m for m in final_call_args[0]])
    assert all(['<!doctype' not in m.get('response') for m in final_call_args[0]])
    
    # Output file name
    assert mock_config['name'] in final_call_args[1]

    
if __name__ == '__main__':
    pytest.main([__file__])