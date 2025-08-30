import csv
import os
import requests

input_file = "dungeon_drops.csv"
icons_dir = "./icons"
base_url = "https://wow.zamimg.com/images/wow/icons/large"

# ensure icons folder exists
#os.makedirs(icons_dir, exist_ok=True)

with open(input_file, newline="", encoding="utf-8") as csvfile:
    reader = csv.DictReader(csvfile)
    for idx, row in enumerate(reader, start=1):
        icon_name = row.get("ICON_NAME", "").strip()
        if not icon_name:
            print(f"⏭️ Skipping row {idx}, no ICON_NAME")
            continue

        local_path = os.path.join(icons_dir, f"{icon_name}.jpg")

        if os.path.exists(local_path):
            print(f"✅ Exists: {icon_name}.jpg")
            continue

        url = f"{base_url}/{icon_name}.jpg"
        try:
            print(f"⬇️ Downloading {icon_name}.jpg ...")
            resp = requests.get(url, stream=True, timeout=20)
            resp.raise_for_status()
            with open(local_path, "wb") as f:
                for chunk in resp.iter_content(1024):
                    f.write(chunk)
            print(f"✔️ Saved {icon_name}.jpg")
        except Exception as e:
            print(f"❌ Failed {icon_name}.jpg: {e}")

