import csv
import re
import requests
import json

input_file = "spells.csv"
output_file = "spells2.csv"

# Regex to capture the tooltip HTML inside .tooltip_enus = "..."
tooltip_pattern = re.compile(r'\.tooltip_enus\s*=\s*"(.+?)";', re.DOTALL)

rows = []
with open(input_file, newline='', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)
    fieldnames = reader.fieldnames + ["TOOLTIP"] if "TOOLTIP" not in reader.fieldnames else reader.fieldnames
    
    for row in reader:
        spell_id = row["SPELLID"]
        url = f"https://www.wowhead.com/classic/spell={spell_id}"
        
        try:
            # Get the raw HTML/JS source
            response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
            response.raise_for_status()
            html = response.text
            
            match = tooltip_pattern.search(html)
            if match:
                # Decode escaped sequences like \" and \/
                #tooltip_html = match.group(1).encode("utf-8").decode("unicode_escape")
                tooltip_html = json.loads(f'"{match.group(1)}"')
                row["TOOLTIP"] = tooltip_html
            else:
                row["TOOLTIP"] = ""
                print(f"⚠️ No tooltip found for SPELLID {spell_id}")
        
        except Exception as e:
            print(f"❌ Error fetching {url}: {e}")
            row["TOOLTIP"] = ""
        
        rows.append(row)

# Write out updated CSV
with open(output_file, "w", newline='', encoding="utf-8") as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"✅ Done! Output saved to {output_file}")

