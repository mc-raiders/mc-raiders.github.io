import csv
import re
import requests
import json

input_file = "dungeon_drops.csv"
output_file = "dungeon_drops2.csv"

# Regex to capture the tooltip HTML inside .tooltip_enus = "..."
tooltip_pattern = re.compile(r'\.tooltip_enus\s*=\s*"(.+?)";', re.DOTALL)
# Regex to capture icon name inside Icon.create("ability_rogue_ambush")
#icon_pattern = re.compile(r'Icon\.create\(\s*"([^"]+)"')

# Regex to capture the icon name inside WH.Gatherer.addData JSON-like structure
#icon_pattern = re.compile(r'WH\.Gatherer\.addData\(\d+,\s*\d+,\s*\{.*?"icon":"([^"]+)"', re.DOTALL)
def create_icon_pattern(item_id):
    return re.compile(r'WH\.Gatherer\.addData\(\d+,\s*\d+,\s*\{.*?"' + re.escape(item_id) + r'":\{.*?"icon":"([^"]+)"', re.DOTALL)

def create_disp_pattern(item_id):
    return re.compile(r'WH\.Gatherer\.addData\(\d+,\s*\d+,\s*\{.*?"' + re.escape(item_id) + r'":\{.*?"displayid":(\d+)', re.DOTALL)

rows = []
with open(input_file, newline='', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)
    fieldnames = reader.fieldnames
    
    for row in reader:
        if row.get("ICON_NAME", "").strip():
            rows.append(row)
            continue

        spell_id = row["DB_ID"]
        url = f"https://www.wowhead.com/classic/item={spell_id}"
        
        try:
            # Get the raw HTML/JS source
            response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
            response.raise_for_status()
            html = response.text
            
            icon_pattern = create_icon_pattern(spell_id)
            icon_match = icon_pattern.search(html)
            if icon_match:
                row["ICON_NAME"] = icon_match.group(1)
                print(f"✔️ Found {icon_match.group(1)}.jpg")
            else:
                row["ICON_NAME"] = ""
                print(f"⚠️ No icon found for DB_ID {spell_id}")

            if row.get("EQ_TYPE", "").strip() in ["11", "12", "2"]:
              print("skipping DISPID for {row.get(""EQ_TYPE"", "").strip()}")
            else:
              disp_pattern = create_disp_pattern(spell_id)
              disp_match = disp_pattern.search(html)
              if disp_match:
                row["DISP_ID"] = disp_match.group(1)
                print(f"✔️ Found DispID: {disp_match.group(1)}")
              else:
                row["DISP_ID"] = ""
                print(f"⚠️ No DISPID for DB_ID {spell_id}")
           
        except Exception as e:
            print(f"❌ Error fetching {url}: {e}")
            row["ICON_NAME"] = ""
            row["DISP_ID"] = ""
        
        rows.append(row)

# Write out updated CSV
with open(output_file, "w", newline='', encoding="utf-8") as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"✅ Done! Output saved to {output_file}")

