import csv
import requests
import os

INPUT_FILE = "items.csv"
OUTPUT_FILE = "missing_items.csv"

# EQ_TYPEs that use item/###.json
SPECIAL_EQ_TYPES = {13, 14, 17, 21, 22, 23, 26}

# Base URL
BASE_URL = "http://localhost:3001/modelviewer/classic"

def check_url(url: str) -> bool:
    """Return True if URL returns 200 OK, else False."""
    try:
        r = requests.get(url, timeout=5)
        return r.status_code == 200
    except requests.RequestException:
        return False

def main():
    missing = []

    with open(INPUT_FILE, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            disp_id = int(row["DISP_ID"])
            eq_type = int(row["EQ_TYPE"])

            if disp_id <= 0:
                continue

            # Decide which URL to check
            if eq_type in SPECIAL_EQ_TYPES:
                url = f"{BASE_URL}/meta/item/{disp_id}.json"
            else:
                url = f"{BASE_URL}/meta/armor/{eq_type}/{disp_id}.json"

            # Check URL
            if not check_url(url):
                missing.append({
                    "DISP_ID": disp_id,
                    "EQ_TYPE": eq_type,
                    "URL": url
                })

    # Save missing data
    if missing:
        fieldnames = ["DISP_ID", "EQ_TYPE", "URL"]
        with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as outcsv:
            writer = csv.DictWriter(outcsv, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(missing)

        print(f"Saved {len(missing)} missing records to {OUTPUT_FILE}")
    else:
        print("✅ All DISP_ID records found")

if __name__ == "__main__":
    main()

