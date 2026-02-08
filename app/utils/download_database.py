import json
import logging
import os
import re
from typing import Any

from bs4 import BeautifulSoup

# Configuration
INPUT_DIRECTORY = "countries_html"
OUTPUT_DATABASE = "plonkit_database.json"

# Logging Setup
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class CountryParser:
    def __init__(self):
        # Regex to clean Markdown links: [Text](url) -> Text
        self.link_pattern = re.compile(r"\[([^\]]+)\]\([^)]+\)")

    def parse_html(self, html_content: str) -> dict[str, Any] | None:
        """
        Extracts preloaded JSON data from the Plonkit HTML structure.
        """
        soup = BeautifulSoup(html_content, "html.parser")
        script_tag = soup.find("script", id="__PRELOADED_DATA__")

        if not script_tag:
            return None

        try:
            raw_json = json.loads(script_tag.string)
        except (json.JSONDecodeError, TypeError):
            return None

        if not raw_json.get("success") or "data" not in raw_json:
            return None

        root_data = raw_json["data"]
        # Handle cases where data might be nested under 'public' or at root
        public_data = root_data.get("public", root_data) if isinstance(root_data, dict) else None

        if not public_data:
            return None

        parsed_entry = {
            "country": public_data.get("title"),
            "code": public_data.get("code"),
            "sections": [],
        }

        steps = public_data.get("steps", [])
        for step in steps:
            section_title = step.get("title", "Information")
            section_lines = []

            items = step.get("items", [])
            for item in items:
                item_data = item.get("data", {})
                text_content = item_data.get("text", [])

                # Normalize text content to string
                full_text = (
                    " ".join(text_content) if isinstance(text_content, list) else str(text_content)
                )

                if full_text:
                    cleaned_text = self.link_pattern.sub(r"\1", full_text).strip()
                    if cleaned_text:
                        section_lines.append(f"- {cleaned_text}")

            if section_lines:
                parsed_entry["sections"].append(
                    {"title": section_title, "description": "\n".join(section_lines)}
                )

        return parsed_entry


def process_files():
    if not os.path.exists(INPUT_DIRECTORY):
        logging.error(f"Directory '{INPUT_DIRECTORY}' not found.")
        return

    parser = CountryParser()
    files = [f for f in os.listdir(INPUT_DIRECTORY) if f.endswith(".html")]
    all_results = []

    logging.info(f"Initiating batch processing for {len(files)} files...")

    for filename in files:
        file_path = os.path.join(INPUT_DIRECTORY, filename)

        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            data = parser.parse_html(content)

            if data:
                all_results.append(data)
                logging.info(f"Processed: {filename}")
            else:
                logging.warning(f"No valid data extracted from: {filename}")

        except Exception as e:
            logging.error(f"Error processing {filename}: {str(e)}")

    # Save to Master Database
    with open(OUTPUT_DATABASE, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=4, ensure_ascii=False)

    logging.info(f"Task Complete. {len(all_results)} entries compiled into '{OUTPUT_DATABASE}'.")


if __name__ == "__main__":
    process_files()
