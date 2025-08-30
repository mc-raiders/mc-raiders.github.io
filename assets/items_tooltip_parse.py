import csv
import re
from bs4 import BeautifulSoup

INPUT_FILE = "items_parsed.csv"
OUTPUT_FILE = "items_parsed2.csv"

# regex patterns keyed by CSV field
PATTERNS = {
    "ARMOR": r"<!--amr-->(\d+) Armor",
    "STAMINA": r"<!--stat7-->\+(\d+) Stamina",
    "STRENGTH": r"<!--stat4-->\+(\d+) Strength",
    "AGILITY": r"<!--stat3-->\+(\d+) Agility",
    "SPIRIT": r"<!--stat6-->\+(\d+) Spirit",
    "INTELLIGENCE": r"<!--stat5-->\+(\d+) Intellect",
    "MIN_DAMAGE": r"<!--dmg-->(\d+) - (\d+)",
    "MAX_DAMAGE": r"<!--dmg-->(\d+) - (\d+)",
    "SPEED": r"<!--spd-->([\d.]+)",
    "BLOCK_VALUE": r"<br>(\d+) Block<br>",
    "RESIST_FIRE": r"\+(\d+) Fire Resistance",
    "RESIST_SHADOW": r"\+(\d+) Shadow Resistance",
    "RESIST_NATURE": r"\+(\d+) Nature Resistance",
    "RESIST_FROST": r"\+(\d+) Frost Resistance",
    "RESIST_ARCANE": r"\+(\d+) Arcane Resistance",
    "MP5": r"Restores (\d+) mana per 5 sec",
    "HEAL_PER_5_SEC": r"Restores (\d+) health per 5 sec",
    "HIT_PCT": r"chance to hit by (\d+)%",
    "SPELL_HIT": r"hit with spells by (\d+)%",
    "CRIT_PCT": r"critical strike by (\d+)%",
    "SPELL_CRIT": r"critical strike with spells by (\d+)%",
    "ATTACK_POWER": r"\+(\d+) Attack Power",
    "R_ATTACK_POWER": r"\+(\d+) ranged Attack Power",
    "SPELL_DAMAGE": r"damage.*by up to (\d+)",
    "SPELL_HEAL": r"Increases healing.*up to (\d+)",
    "SPELL_FROST": r"damage done by Frost.*up to (\d+)",
    "SPELL_SHADOW": r"damage done by Shadow.*up to (\d+)",
    "SPELL_FIRE": r"damage done by Fire.*up to (\d+)",
    "SPELL_NATURE": r"damage done by Nature.*up to (\d+)",
    "DEFENSE": r"Increased Defense \+(\d+)",
    "DODGE_PCT": r"dodge an attack by (\d+)%",
    "PARRY_PCT": r"parry an attack by (\d+)%",
    "BLOCK_PCT": r"block attacks.*by (\d+)%",
    "SKILL_DAGGER": r"Daggers \+(\d+)",
    "SKILL_SWORD": r"Swords \+(\d+)",
    "SET": r"/classic/item-set=(\d+)/",
}

def parse_tooltip(tooltip):
    """Parse one tooltip string into a dict of extracted values."""
    data = {}
    for field, pattern in PATTERNS.items():
        match = re.search(pattern, tooltip, flags=re.IGNORECASE)
        if match:
            if field in ("MIN_DAMAGE", "MAX_DAMAGE"):
                # first group is min, second is max
                data["MIN_DAMAGE"] = match.group(1)
                data["MAX_DAMAGE"] = match.group(2)
            else:
                data[field] = match.group(1)
    # Collect anything not matched → comments
    comments = []
    soup = BeautifulSoup(tooltip, "html.parser")
    text = soup.get_text(" ", strip=True)

    if "Use:" in text:
        m = re.search(r"Use:\s*(.+)", text, re.IGNORECASE)
        if m:
            comments.append("Use: " + m.group(1).strip())

    if "Chance on hit:" in text:
        m = re.search(r"Chance on hit:\s*(.+)", text, re.IGNORECASE)
        if m:
            comments.append("Chance on hit: " + m.group(1).strip())

    if "When struck" in text:
        m = re.search(r"(When struck.+)", text, re.IGNORECASE)
        if m:
            comments.append(m.group(1).strip())

    if comments:
        data["COMMENTS"] = "; ".join(comments)

    return data


def main():
    with open(INPUT_FILE, newline="", encoding="utf-8") as infile:
        reader = list(csv.DictReader(infile))
        base_fields = reader[0].keys()

    # keep original fields, then add ours at the end
    extra_fields = list(PATTERNS.keys()) + ["COMMENTS"]
    fieldnames = list(base_fields) + [f for f in extra_fields if f not in base_fields]

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()

        for idx, row in enumerate(reader, start=1):
            #if 74 <= idx <= 541:
            tooltip = row.get("TOOLTIP", "")
            parsed = parse_tooltip(tooltip)
            row.update(parsed)
            writer.writerow(row)

    print(f"✅ Parsed rows 74–541 and wrote output to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()

