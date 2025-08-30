import csv
import re
import requests
import json

input_file = "items3.csv"
output_file = "items4.csv"

# Regex to capture the tooltip HTML inside .tooltip_enus = "..."
tooltip_pattern = re.compile(r'\.tooltip_enus\s*=\s*"(.+?)";', re.DOTALL)
# Regex to capture icon name inside Icon.create("ability_rogue_ambush")
#icon_pattern = re.compile(r'Icon\.create\(\s*"([^"]+)"')

# Regex to capture the icon name inside WH.Gatherer.addData JSON-like structure
#icon_pattern = re.compile(r'WH\.Gatherer\.addData\(\d+,\s*\d+,\s*\{.*?"icon":"([^"]+)"', re.DOTALL)
def create_icon_pattern(item_id):
    return re.compile(r'WH\.Gatherer\.addData\(\d+,\s*\d+,\s*\{.*?"' + re.escape(item_id) + r'":\{.*?"displayid":(\d+)', re.DOTALL)

rows = []
with open(input_file, newline='', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)
    fieldnames = reader.fieldnames
    
    for row in reader:
        # Skip rows where EQ_TYPE is 11, 12, or 2
        if row.get("EQ_TYPE", "").strip() in ["11", "12", "2"]:
            rows.append(row)
            continue
        if row.get("DISP_ID", "").strip():
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
                row["DISP_ID"] = icon_match.group(1)
                print(f"✔️ Found DIPLAYID: {icon_match.group(1)}")
            else:
                row["DISP_ID"] = ""
                print(f"⚠️ No displayid found for DB_ID {spell_id}")
        except Exception as e:
            print(f"❌ Error fetching {url}: {e}")
            row["DISP_ID"] = ""
        
        rows.append(row)

# Write out updated CSV
with open(output_file, "w", newline='', encoding="utf-8") as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"✅ Done! Output saved to {output_file}")

