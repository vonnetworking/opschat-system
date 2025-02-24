import os
import json

def get_mock_data(data_source: str):
    file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "data-templates", f"{data_source}.json"))
    
    with open(file_path, "r") as file:
        lines = ''.join(file.readlines())
    
    try:
        jsonl_data = json.loads(lines)
    except Exception as e:
        raise RuntimeError(f"Error loading ServiceNow data template: {file_path}\nError: {str(e)}")

    return {'result': jsonl_data}