import requests
from bs4 import BeautifulSoup
import csv
import re
import json
import uuid

def parse_js_to_json(js_str):
    # Quote only unquoted keys:
    # Look for { or , followed by optional spaces, then a bareword (not quoted) before colon
    js_str = re.sub(
        r'([{,]\s*)([A-Za-z_]\w*|\d+)\s*:',
        lambda m: f'{m.group(1)}"{m.group(2)}":',
        js_str
    )

    # Remove trailing commas
    js_str = re.sub(r',(\s*[}\]])', r'\1', js_str)

    # Replace WH.TERMS placeholders
    js_str = re.sub(r'WH\.TERMS\.\w+', '"WH_TERMS_placeholder"', js_str)

    # Normalize quotes
    js_str = js_str.replace('’', "'").replace('‘', "'").replace('`', "'")

    # Handle pctstack objects
    js_str = re.sub(
        r'"pctstack":"\{([^}]*)\}"',
        lambda m: '"pctstack":{' + re.sub(r'(\d+):', r'"\1":', m.group(1)) + '}',
        js_str
    )

    # Escape special characters in string values (e.g., colons, quotes)
    try:
        # Test JSON validity
        json.loads(js_str)
        return js_str
    except json.JSONDecodeError as e:
        print(f"JSON parsing failed: {e}")
        print(f"Problematic JSON string near error (char {e.pos}):")
        start = max(0, e.pos - 50)
        end = min(len(js_str), e.pos + 50)
        print(js_str[start:end])
        raise

def extract_drops_data(html):
    soup = BeautifulSoup(html, 'html.parser')
    for script in soup.find_all('script'):
        script_text = script.text
        if "new Listview" in script_text and "template: 'item'" in script_text and ("id: 'drops'" in script_text or "id: 'contains'" in script_text):
            #print("\nFound Listview with template: 'item' and id: 'drops'. Raw Script Text:")
            #print(script_text[:2000] + "..." if len(script_text) > 2000 else script_text)
            # Use a more flexible regex to capture the data array
            # Match from 'data:' until the closing ']' of the array, allowing nested structures
            # Function to find the full data array using bracket counting
            def find_data_array(text):
                start = text.find('data:[')
                if start == -1:
                    return None
                start += 6  # Move past 'data: ['
                bracket_count = 1
                i = start
                while i < len(text):
                    char = text[i]
                    if char == '[':
                        bracket_count += 1
                    elif char == ']':
                        bracket_count -= 1
                    if bracket_count == 0:
                        return text[start:i]
                    i += 1
                return None

            data_str = find_data_array(script_text)
            if data_str:
                #print("\nMatched Listview Data Array:")
                #print(data_str[:1000000] + "..." if len(data_str) > 1000 else data_str)
                json_str = parse_js_to_json('[' + data_str + ']')  # Wrap in array for valid JSON
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError as e:
                    print(f"\nError parsing Listview JSON: {e}")
                    print(f"Problematic JSON string: {json_str[:1000]}...")
                    return None
            else:
                print("\nNo match found for data array in Listview script.")
    print("\nNo Listview with template: 'item' and id: 'drops' found.")
    return None

def main(input_file='dungeon_bosses.csv', output_file='drops.csv'):
    drops_list = []
    with open(input_file, 'r', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            loot = row['loot'].strip()
            npc_id = row['npc_id'].strip()
            prefix = row['prefix'].strip()
    #npc_id = '13280'
    #prefix = 'npc'
    #loot = '1'
            #print(loot)
            if loot == '1':
              url = f"https://www.wowhead.com/classic/{prefix}={npc_id}"
              print(f"Processing NPC ID: {npc_id} ({url})")
              npc_drops = []
              try:
                  response = requests.get(url)
                  response.raise_for_status()
                  drops_data = extract_drops_data(response.text)
                  #print("\nDrops Data:")
                  #print(json.dumps(drops_data, indent=2))
                  if drops_data:
                      for item in drops_data:
                          if 'slot' in item and item['slot'] > 0:  # Equippable items have slot > 0
                              #count = item.get('count', 0)
                              #outof = item.get('outof', 0)
                              count = 0
                              outof = 1
                              # Prioritize mode 0 for drop chance, as Wowhead uses it
                              if 'modes' in item and '0' in item['modes']:
                                  mode = item['modes']['0']
                                  count = mode.get('count', 0)
                                  outof = mode.get('outof', 1)
                              if outof > 0:
                                  drop_chance = count / outof
                                  if drop_chance >= 0.01:
                                      npc_drops.append({
                                          'npc_id': npc_id,
                                          'item_id': item['id'],
                                          'name': item['name'],
                                          'slot': item['slot'],
                                          'quality': item['quality'],
                                          'count': count,
                                          'outof': outof,
                                          'drop_chance': drop_chance
                                      })
                  if npc_drops:
                      # Find the highest 'outof' for this NPC
                      max_outof = max(item['outof'] for item in npc_drops)
                      threshold = max_outof * 0.25
                      print(f"NPC {npc_id} - Highest outof: {max_outof}, Threshold (25%): {threshold}")
                      
                      # Filter drops for this NPC to keep only items with outof >= 25% of max_outof
                      filtered_npc_drops = [item for item in npc_drops if item['outof'] >= threshold and item['quality'] >= 3]
                      print(f"NPC {npc_id} - Filtered {len(npc_drops)} items to {len(filtered_npc_drops)} items with outof >= {threshold}")
                      
                      # Append filtered drops to overall drops_list
                      drops_list.extend(filtered_npc_drops)
                  else:
                      print(f"No drops found for NPC {npc_id} meeting the initial criteria.")
              except requests.RequestException as e:
                  print(f"Error fetching {url}: {e}")

    if drops_list:       
        with open(output_file, 'w', newline='') as csvfile:
            fieldnames = ['npc_id', 'item_id', 'name', 'slot', 'quality', 'count', 'outof', 'drop_chance']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(drops_list)
        print(f"Output written to {output_file}")
    else:
        print("No drops found meeting the criteria.")

if __name__ == "__main__":
    main()
