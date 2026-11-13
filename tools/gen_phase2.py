#!/usr/bin/env python3
"""Phase 2 ("gear that does things"): the content side of the native half's abilities.

    python3 tools/gen_phase2.py

For each item the native half (native/useful_armory) gives an ability, adds one plain lore line
saying what it does to content/data/useful_armory/horizon/item/<id>.json: "Full set: ..." on
each armour piece, one short line on the tools and weapons. Lore already there is kept; the
script's own line is replaced, not added again, so it can run any number of times.

Halberds get their extra block of reach as data: an `minecraft:entity_interaction_range`
attribute modifier in the main hand, added to the item's `minecraft:attribute_modifiers` list
(once, by its id).

The ids are the content mod's own legacy names; keep them in step with runtime.rs.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ITEMS = ROOT / "content" / "data" / "useful_armory" / "horizon" / "item"

SETS = {
    "Full set: water breathing and faster swimming":
        ["aquitehelmet", "aquitebody", "aquitelegs", "aquiteboots"],
    "Full set: fire resistance":
        ["colosifitearmorhelmet", "colosifitearmorbody", "colosifitearmorlegs", "colosifitearmorboots"],
    "Full set: luck":
        ["emeraldarmorhelmet", "emeraldarmorbody", "emeraldarmorlegs", "emeraldarmorboots"],
    "Full set: 25% more experience":
        ["lapisarmorhelmet", "lapisarmorbody", "lapisarmorlegs", "lapisarmorboots"],
    "Full set: knockback resistance, half explosion damage":
        ["obsidainarmorhelmet", "obsidainarmorbody", "obsidainarmorlegs", "obsidainarmorboots"],
    "Full set: speed":
        ["quartzamorhelmet", "quartzamorbody", "quartzamorlegs", "quartzamorboots"],
    "Full set: haste":
        ["redstonearmorhelmet", "redstonearmorbody", "redstonearmorlegs", "redstonearmorboots"],
    "Full set: night vision":
        ["shadowhelmet", "shadowbody", "shadowlegs", "shadowboots"],
    "Full set: regeneration, no fall damage":
        ["ultimateahelmet", "ultimateabody", "ultimatealegs", "ultimateaboots"],
}

HALBERDS = ["aquitehalbert", "colosifitehalbert", "emeraldhalbert", "lapishalbert", "quartzhalber",
            "shadowotehrweapon"]

TOOLS = {
    "Sneak: mines the whole ore vein": ["colosifitepickaxe", "emeraldpickaxe", "shadowpickaxe"],
    "Sneak: digs 3 x 3": ["obsidianpickaxe", "obsidianshovel"],
    "Sneak: fells the whole tree": ["aquiteaxe", "emeraldaxe", "shadowaxe"],
    "Harvests and replants grown crops 3 x 3":
        ["aquitehoe", "colosifitehoe", "emeraldhoe", "lapishoe", "obsidianhoe", "quartzhoe",
         "redstonehoe", "shadowhoe"],
    "Harvests crops 5 x 5; kills may drop heads": ["reaperscyth"],
    "Double damage from behind":
        ["aquitedagger", "colosifitedagger", "emeralddagger", "lapisdagger", "quartzdagger",
         "shadowdagger"],
    "Hits also hurt mobs next to the target":
        ["aquitegreatsword", "colosifitegreatsword", "emeraldgreatsword", "lapisgreatsword",
         "quartzgreatsword", "shadowgreatsword"],
    "One more block of reach": HALBERDS,
    "Sets targets on fire": ["lavasword"],
    "Heals a heart on each kill": ["souleater"],
    "50% more damage to piglins and hoglins": ["pigmansword"],
    "50% more damage in the Nether": ["thenetherlegacy"],
}

# Lines earlier versions of this script wrote, taken out too when the wording changes.
RETIRED = []

REACH = {
    "type": "minecraft:entity_interaction_range",
    "amount": 1,
    "id": "useful_armory:halberd_reach",
    "operation": "add_value",
    "slot": "mainhand",
}


def lines():
    out = {}
    for table in (SETS, TOOLS):
        for line, ids in table.items():
            for item in ids:
                if item in out:
                    raise SystemExit(f"{item} has two lines")
                out[item] = line
    return out


def save(path, raw, data):
    text = json.dumps(data, indent=2, ensure_ascii=raw.isascii())
    if raw.endswith("\n"):
        text += "\n"
    if text != raw:
        path.write_text(text, encoding="utf-8", newline="")
        return True
    return False


def main():
    own = set(lines().values()) | set(RETIRED)
    changed = 0
    for item, line in sorted(lines().items()):
        path = ITEMS / f"{item}.json"
        if not path.is_file():
            raise SystemExit(f"no item file {path.relative_to(ROOT)}")
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
        components = data.setdefault("components", {})
        lore = [x for x in components.get("minecraft:lore", [])
                if not (isinstance(x, dict) and set(x) == {"text"} and x["text"] in own)]
        lore.append({"text": line})
        components["minecraft:lore"] = lore
        if item in HALBERDS:
            modifiers = components.setdefault("minecraft:attribute_modifiers", [])
            if not any(m.get("id") == REACH["id"] for m in modifiers):
                modifiers.append(dict(REACH))
        if save(path, raw, data):
            changed += 1
            print(f"updated {path.relative_to(ROOT)}")
    print(f"{changed} item files changed")


if __name__ == "__main__":
    main()
