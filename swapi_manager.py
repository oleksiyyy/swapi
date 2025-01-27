import argparse
import pandas as pd
import requests
import logging
import json
import os


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class SWAPIClient:
    def __init__(self, base_url: str):
        self.base_url = base_url

    def fetch_json(self, endpoint: str) -> list:
        all_data = []
        url = f"{self.base_url}{endpoint}/"
        while url:
            logger.info(f"Fetching data from: {url}")
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            all_data.extend(data["results"])
            url = data.get("next")
        return all_data


class SWAPIDataManager:
    def __init__(self, client: SWAPIClient):
        self.client = client
        self.data = {}

    def fetch_entity(self, endpoint: str):
        logger.info(f"Fetching data for endpoint: {endpoint}")
        self.data[endpoint] = pd.DataFrame(self.client.fetch_json(endpoint))

    def apply_filter(self, endpoint: str, columns_to_drop: list):
        if endpoint in self.data:
            logger.info(f"Applying filters to {endpoint}: {columns_to_drop}")
            self.data[endpoint].drop(columns=columns_to_drop, inplace=True, errors="ignore")

    def save_to_excel(self, filename: str):
        logger.info(f"Saving data to Excel file: {filename}")
        with pd.ExcelWriter(filename) as writer:
            for endpoint, df in self.data.items():
                df.to_excel(writer, sheet_name=endpoint.capitalize(), index=False)


def main():
    parser = argparse.ArgumentParser(description="SWAPI Data Manager CLI")
    parser.add_argument("--endpoint", type=str, required=True, help="Comma-separated list of endpoints (e.g., people,planets,films).")
    parser.add_argument("--output", type=str, required=True, help="Output Excel file name (e.g., data.xlsx).")
    parser.add_argument("--filters-file", type=str, help="Path to JSON file with filters for each endpoint.")

    args = parser.parse_args()
    endpoints = args.endpoint.split(",")
    output_file = args.output
    filters_file = args.filters_file

    filters = {}
    if filters_file:
        if os.path.exists(filters_file):
            logger.info(f"Loading filters from file: {filters_file}")
            with open(filters_file, "r") as file:
                filters = json.load(file)
        else:
            logger.error(f"Filters file not found: {filters_file}")
            return

    client = SWAPIClient(base_url="https://swapi.dev/api/")
    manager = SWAPIDataManager(client)

    for endpoint in endpoints:
        manager.fetch_entity(endpoint)
        if endpoint in filters:
            manager.apply_filter(endpoint, filters[endpoint])

    manager.save_to_excel(output_file)
    logger.info("Process completed successfully.")


if __name__ == "__main__":
    main()
