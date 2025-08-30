import csv
import requests
import json

INPUT_FILE = "items.csv"
OUTPUT_FILE = "missing_assets.csv"

SPECIAL_EQ_TYPES = {13, 14, 17, 21, 22, 23, 26}
BASE_URL = "http://localhost:3001/modelviewer/classic"

def fetch_json(url: str):
    """Fetch JSON and return dict or None."""
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            return r.json()
        return None
    except requests.RequestException:
        return None

def check_url(url: str) -> bool:
    """Return True if URL exists, False if missing/error."""
    try:
        r = requests.get(url, timeout=5)
        return r.status_code == 200
    except requests.RequestException:
        return False

def extract_filedatas(json_data: dict):
    """Yield (type, filedataid) tuples from TextureFiles and ModelFiles."""
    results = []

    # Model (like "Model": {"2": 148298})
    if json_data.get("Model"):
        for key, fileid in json_data["Model"].items():
            if isinstance(fileid, int):
                results.append(("model", fileid))

    # Textures (like "Textures": {"2": 148298})
    if json_data.get("Textures"):
        for key, fileid in json_data["Textures"].items():
            if isinstance(fileid, int):
                results.append(("texture", fileid))

    # TextureFiles
    if json_data.get("TextureFiles"):
        for key, entries in json_data["TextureFiles"].items():
            for entry in entries:
                if "FileDataId" in entry:
                    results.append(("texture", entry["FileDataId"]))

    # ModelFiles
    if json_data.get("ModelFiles"):
        for key, entries in json_data["ModelFiles"].items():
            for entry in entries:
                if "FileDataId" in entry:
                    results.append(("model", entry["FileDataId"]))

    return results

def main():
    missing = []

    with open(INPUT_FILE, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            disp_id = int(row["DISP_ID"])
            eq_type = int(row["EQ_TYPE"])

            if disp_id <= 0:
                continue

            # Pick correct JSON URL
            if eq_type in SPECIAL_EQ_TYPES:
                json_url = f"{BASE_URL}/meta/item/{disp_id}.json"
            else:
                json_url = f"{BASE_URL}/meta/armor/{eq_type}/{disp_id}.json"

            json_data = fetch_json(json_url)
            if not json_data:
                missing.append({
                    "DISP_ID": disp_id,
                    "EQ_TYPE": eq_type,
                    "Missing": "json",
                    "URL": json_url
                })
                continue

            # Extract FileDataIds
            for filetype, fileid in extract_filedatas(json_data):
                if filetype == "texture":
                    asset_url = f"{BASE_URL}/textures/{fileid}.webp"
                else:  # model
                    asset_url = f"{BASE_URL}/mo3/{fileid}.mo3"

                if not check_url(asset_url):
                    missing.append({
                        "DISP_ID": disp_id,
                        "EQ_TYPE": eq_type,
                        "Missing": filetype,
                        "FileDataId": fileid,
                        "URL": asset_url
                    })

    # Save missing records
    if missing:
        fieldnames = ["DISP_ID", "EQ_TYPE", "Missing", "FileDataId", "URL"]
        with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as outcsv:
            writer = csv.DictWriter(outcsv, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(missing)

        print(f"⚠️ Saved {len(missing)} missing assets to {OUTPUT_FILE}")
    else:
        print("✅ All assets accounted for")

if __name__ == "__main__":
    main()

