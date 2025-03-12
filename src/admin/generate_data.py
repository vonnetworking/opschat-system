import os
import sys
import json
import requests
import argparse

import logging
logging.basicConfig(level=logging.INFO)


GENERATOR_API_URL = "http://localhost:8082/snow/generate"
DATA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data-templates"))


def request_new_data(data_type: str, return_qty: int, seed_app_id: str, seed_count: int):
    """ Requests new mock data from the generator API """
    if data_type not in ["change_request", "incident", "cmdb"]:
        raise ValueError("Invalid data_type. Must be one of 'change_request', 'incident', or 'cmdb'")

    header = {"Content-Type": "application/json"}
    payload = {
        "type": data_type,
        "return_number": return_qty,
        "seeded_app_id": seed_app_id,
        "number_of_seeds": seed_count
    }

    response = requests.post(GENERATOR_API_URL, headers=header, json=payload)
    response.raise_for_status()
    
    data = response.json()

    return list(data['generated_data'].values())[0]


def save_new_data(data_type: str, data: dict):
    """ Save new mock data to a file """
    file_path = os.path.join(DATA_PATH, f"{data_type}.json")
    with open(file_path, "w") as f:
        f.write(json.dumps(data, indent=4))


def main(data_type, return_qty, seed_app_id, seed_count):

    logging.info(f"Generating {return_qty} new {data_type} records with app_id {seed_app_id} and {seed_count} seeds")
    new_data = request_new_data(data_type, return_qty, seed_app_id, seed_count)

    logging.info(f"Saving new data to file")
    save_new_data(data_type, new_data)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate mock data for the service now agent")
    parser.add_argument("--data_type", type=str, default="change_request", help="The type of data to generate. Must be one of 'change_request', 'incident', or 'cmdb'")
    parser.add_argument("--return_qty", type=int, default=10, help="The number of records to generate")
    parser.add_argument("--seed_app_id", type=str, default="mock-app-id", help="The app_id to seed into the data")
    parser.add_argument("--seed_count", type=int, default=2, help="The number of seeds to use")

    args = parser.parse_args()

    data_type = args.data_type
    return_qty = args.return_qty
    seed_app_id = args.seed_app_id
    seed_count = args.seed_count

    main(data_type, return_qty, seed_app_id, seed_count)