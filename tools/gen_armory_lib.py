#!/usr/bin/env python3
"""Writes content/data/useful_armory/armory_lib.json: what Useful Armory's items and creatures
do beyond data, for Armory Lib (https://github.com/snipeparparalt2/armory_lib) to carry out.

    python3 tools/gen_armory_lib.py

Useful Armory has no code of its own. With Armory Lib installed, this file gives the mod its
settings page, the glow of its glowing gear, its creatures' looks and rules, the armour set
bonuses, the tool abilities, the hoes' harvest sweep and the weapon effects. Without the
library the file is ignored and the items, ores, creatures and places still work.
The format is in Armory Lib's README.
"""
import json
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NS = "useful_armory"
ITEMS = sorted(p.stem for p in (ROOT / "content/data" / NS / "horizon/item").glob("*.json"))
MOBS = sorted(p.stem for p in (ROOT / "content/data" / NS / "horizon/entity_type").glob("*.json"))


def ids(*names):
    """Full ids of items that must exist."""
    missing = [n for n in names if n not in ITEMS]
    if missing:
        raise SystemExit(f"no such items: {missing}")
    return [f"{NS}:{n}" for n in names]


def ending(suffix):
    return ids(*[i for i in ITEMS if i.endswith(suffix)])


# Item -> glow colour. These are the sprites gen_textures.py marks as glowing (its GLOW table).
GLOW = [
    ("aquiteaxe", 0x8cffe2),
    ("aquitebody", 0x8cffe2),
    ("aquiteboots", 0x8cffe2),
    ("aquitedagger", 0x8cffe2),
    ("aquitegreatsword", 0x8cffe2),
    ("aquitehalbert", 0x8cffe2),
    ("aquitehelmet", 0x8cffe2),
    ("aquitehoe", 0x8cffe2),
    ("aquitelegs", 0x8cffe2),
    ("aquitepickaxe", 0x8cffe2),
    ("aquiteshovel", 0x8cffe2),
    ("aquitesword", 0x8cffe2),
    ("erottenflesh", 0xb4ff46),
    ("lavasword", 0xff8c1e),
    ("shadowaxe", 0x9e60ff),
    ("shadowbody", 0x9e60ff),
    ("shadowboots", 0x9e60ff),
    ("shadowdagger", 0x9e60ff),
    ("shadowgreatsword", 0x9e60ff),
    ("shadowhelmet", 0x9e60ff),
    ("shadowhoe", 0x9e60ff),
    ("shadowlegs", 0x9e60ff),
    ("shadowotehrweapon", 0x9e60ff),
    ("shadowpickaxe", 0x9e60ff),
    ("shadowshovel", 0x9e60ff),
    ("shadowsword", 0x9e60ff),
    ("souleater", 0xe8aaec),
    ("soulednetherstar", 0x96f0ff),
    ("thenetherlegacy", 0x50e6f0),
]

# Head, chest, legs, feet (the ids are the mod's legacy names), then what the whole set does.
SETS = [
    (["aquitehelmet", "aquitebody", "aquitelegs", "aquiteboots"],
     {"effects": ["minecraft:water_breathing", "minecraft:dolphins_grace"]}),
    (["colosifitearmorhelmet", "colosifitearmorbody", "colosifitearmorlegs", "colosifitearmorboots"],
     {"effects": ["minecraft:fire_resistance"]}),
    (["emeraldarmorhelmet", "emeraldarmorbody", "emeraldarmorlegs", "emeraldarmorboots"],
     {"effects": ["minecraft:luck"]}),
    (["lapisarmorhelmet", "lapisarmorbody", "lapisarmorlegs", "lapisarmorboots"],
     {"experience_bonus": 0.25}),
    (["obsidainarmorhelmet", "obsidainarmorbody", "obsidainarmorlegs", "obsidainarmorboots"],
     {"knockback_taken": 0.5, "explosion_taken": 0.5}),
    (["quartzamorhelmet", "quartzamorbody", "quartzamorlegs", "quartzamorboots"],
     {"effects": ["minecraft:speed"]}),
    (["redstonearmorhelmet", "redstonearmorbody", "redstonearmorlegs", "redstonearmorboots"],
     {"effects": ["minecraft:haste"]}),
    (["shadowhelmet", "shadowbody", "shadowlegs", "shadowboots"],
     {"effects": ["minecraft:night_vision"]}),
    (["ultimateahelmet", "ultimateabody", "ultimatealegs", "ultimateaboots"],
     {"no_fall_damage": True, "regen": {"every_ticks": 80, "health": 1.0}}),
]

# Creature -> rules beyond "stays what it is and doesn't burn in daylight".
MOB_RULES = {
    "ember_brute": {"fire_proof": True},
    "lost_pigman": {"fire_proof": True},
    "tide_lurker": {"on_hit": [{"effect": "minecraft:slowness", "amplifier": 1, "ticks": 100}]},
}

PIGLIN_FAMILY = ["minecraft:piglin", "minecraft:piglin_brute", "minecraft:hoglin",
                 "minecraft:zoglin", "minecraft:zombified_piglin"]


def build():
    manifest = tomllib.loads((ROOT / "content/horizon-mod.toml").read_text())
    by_colour = {}
    for item, rgb in GLOW:
        by_colour.setdefault(rgb, []).extend(ids(item))
    textures = ROOT / "content/assets" / NS / "textures/entity"
    looks, rules = [], []
    for mob in MOBS:
        if not (textures / mob / f"{mob}.png").is_file():
            raise SystemExit(f"no texture for {mob}")
        look = {"kind": f"{NS}:{mob}", "rig": "zombie", "texture": f"{NS}:entity/{mob}/{mob}"}
        if (textures / mob / f"{mob}_e.png").is_file():
            look["emissive"] = f"{NS}:entity/{mob}/{mob}_e"
        looks.append(look)
        # Copies of a zombie: daylight must not light them, nor water turn them into drowned.
        rules.append({"kind": f"{NS}:{mob}", "no_conversion": True, "no_sunburn": True,
                      **MOB_RULES.get(mob, {})})
    hoes = [h for h in ending("hoe")]
    return {
        "schema": 1,
        "page": {
            "title": f"{manifest['name']} {manifest['version']}",
            "description": "Glowing gear lights up the world; full armour sets give bonuses; "
                           "sneak to vein mine, dig 3 x 3 or fell trees; hoes harvest an area; "
                           "weapons have effects. Each part can be switched off here.",
            "switches": [
                {"key": "glow", "label": "Glow"},
                {"key": "set_bonuses", "label": "Set bonuses"},
                {"key": "vein_mining", "label": "Vein mining"},
                {"key": "wide_dig", "label": "Wide dig"},
                {"key": "tree_felling", "label": "Tree felling"},
                {"key": "harvest_sweep", "label": "Harvest sweep"},
                {"key": "weapon_effects", "label": "Weapon effects"},
            ],
        },
        "gear_lights": [{"items": items, "color": f"#{rgb:06x}", "setting": "glow"}
                        for rgb, items in sorted(by_colour.items())],
        "mob_looks": looks,
        "mob_rules": rules,
        "armor_sets": [{"pieces": ids(*pieces), "setting": "set_bonuses", **bonus}
                       for pieces, bonus in SETS],
        "tools": [
            {"items": ids("colosifitepickaxe", "emeraldpickaxe", "shadowpickaxe"),
             "ability": "vein_mine", "setting": "vein_mining"},
            {"items": ids("obsidianpickaxe", "obsidianshovel"),
             "ability": "wide_dig", "setting": "wide_dig"},
            {"items": ids("aquiteaxe", "emeraldaxe", "shadowaxe"),
             "ability": "fell_tree", "setting": "tree_felling"},
        ],
        # The mod's ores, which no ore tag lists.
        "ores": [f"{NS}:{b}" for b in ("aquiteore", "colosifiteore", "shadowore",
                                       "deepslate_aquite_ore", "deepslate_colosifite_ore",
                                       "deepslate_shadow_ore")],
        "harvest": [
            {"items": hoes, "radius": 1, "setting": "harvest_sweep"},
            {"items": ids("reaperscyth"), "radius": 2, "setting": "harvest_sweep"},
        ],
        "weapons": [
            {"items": ending("dagger"), "setting": "weapon_effects", "backstab": 2.0},
            {"items": ending("greatsword"), "setting": "weapon_effects",
             "splash": {"radius": 1.5, "share": 0.5}},
            {"items": ids("lavasword"), "setting": "weapon_effects", "fire_ticks": 80},
            {"items": ids("souleater"), "setting": "weapon_effects", "heal_on_kill": 2.0},
            {"items": ids("pigmansword"), "setting": "weapon_effects",
             "bonus_against": {"kinds": PIGLIN_FAMILY, "multiplier": 1.5}},
            {"items": ids("thenetherlegacy"), "setting": "weapon_effects",
             "bonus_in": {"dimension": "minecraft:the_nether", "multiplier": 1.5}},
            {"items": ids("reaperscyth"), "setting": "weapon_effects", "heads": True},
        ],
    }


if __name__ == "__main__":
    out = ROOT / "content/data" / NS / "armory_lib.json"
    out.write_text(json.dumps(build(), indent=2) + "\n")
    print(out.relative_to(ROOT))
