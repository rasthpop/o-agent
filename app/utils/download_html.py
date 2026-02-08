import json
import logging
import os
import random
import time

from playwright.sync_api import sync_playwright

# Configuration
INPUT_FILE = "countries.json"
OUTPUT_DIRECTORY = "countries_html"
BASE_URL = "https://www.plonkit.net/"

# Logging Configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def download_country_data():
    """
    Automates the retrieval of country-specific HTML content using Playwright.
    Includes anti-bot measures and persistence checks.
    """

    # 1. Resource Validation
    if not os.path.exists(INPUT_FILE):
        logging.error(f"Input file '{INPUT_FILE}' not found. Execution aborted.")
        return

    try:
        with open(INPUT_FILE, encoding="utf-8") as f:
            countries = json.load(f)
    except json.JSONDecodeError as e:
        logging.error(f"Failed to parse input JSON: {e}")
        return

    # 2. Directory Initialization
    if not os.path.exists(OUTPUT_DIRECTORY):
        os.makedirs(OUTPUT_DIRECTORY)
        logging.info(f"Initialized output directory: {OUTPUT_DIRECTORY}")

    total_count = len(countries)
    logging.info(f"Queue initialized: {total_count} entries identified.")

    with sync_playwright() as p:
        logging.info("Initializing Chromium instance...")

        # Headless=False is maintained to bypass advanced bot detection (e.g., Cloudflare)
        browser = p.chromium.launch(headless=False)

        # User Agent rotation or static professional header
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) \
AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        )

        page = context.new_page()

        for index, slug in enumerate(countries, start=1):
            file_path = os.path.join(OUTPUT_DIRECTORY, f"{slug}.html")

            # Check for existing data to support process resumption
            if os.path.exists(file_path):
                logging.info(
                    f"[{index}/{total_count}] Skipping: '{slug}' (Resource already exists)"
                )
                continue

            target_url = f"{BASE_URL}{slug}"
            logging.info(f"[{index}/{total_count}] Requesting: {target_url}")

            try:
                page.goto(target_url, wait_until="domcontentloaded", timeout=60000)

                # Buffer for Cloudflare challenge resolution and dynamic JS rendering
                time.sleep(random.uniform(5.0, 8.0))

                html_content = page.content()

                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(html_content)

                logging.info(f"Successfully archived: {slug}")

            except Exception as e:
                logging.error(f"Failed to retrieve {slug}: {str(e)}")

            # Rate limiting to prevent IP blacklisting
            time.sleep(random.uniform(2.0, 4.0))

        logging.info("Data acquisition complete. Closing browser.")
        browser.close()


if __name__ == "__main__":
    download_country_data()
