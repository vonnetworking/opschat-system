"""
Add fields to the mock data
"""

import json
import os
import uuid
import random
from typing import Dict, List

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data-templates"))

def load_data_file(file_path: str) -> List[Dict]:
    """
    Load the data from a JSON file
    """
    print(f">> Loading {file_path}")
    with open(file_path, "r") as f:
        data = json.load(f)
    print(f">> {len(data)} items loaded")
    return data


def save_data_file(file_path: str, data: List[Dict]) -> None:
    """
    Save the data to a JSON file
    """
    print(f">>> saing {file_path}")
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)


def main():
    data_file = "change_request.json"
    data_file_path = os.path.join(DATA_DIR, data_file)
    data = load_data_file(data_file_path)

    # Add the new fields to the data
    for item in data:
        item["number"] = str(uuid.uuid4())[:8]
        item["parent"] = str(uuid.uuid4())[:6].upper()
        item["u_environment"] = ["dev", "test", "prod"][random.randint(0, 2)]
        item["cmdb_ci"] = str(uuid.uuid4())[:6].upper()

    # Save the updated data to the file
    save_data_file(data_file_path, data)

if __name__ == "__main__":
    main()