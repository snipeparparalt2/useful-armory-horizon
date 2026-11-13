#!/usr/bin/env python3
"""Phase 4 and 5 content data: trinkets, backpacks, the recall charm, the golem core, soul jars,
the waystone and the soul forge.

    python3 -I tools/gen_phase4.py

Writes item and block definitions, models, blockstates, recipes, loot, names and the creative
tab entries. Textures come from tools/gen_new_art.py. Run it after gen_phase1.py; it only adds
its own files and keys, so running it again changes nothing.

What works from data alone:
- Trinkets work **in the off hand** through vanilla attribute modifiers, and the tooltip shows
  them. Working anywhere in the hotbar needs Armory Lib (see docs/HANDOFF.md). The lapis
  ring's bonus experience needs it too.
- The waystone and the soul forge are placeable, glowing, mineable blocks. Teleporting and
  upgrading need Armory Lib.
- Backpacks, the recall charm, the golem core and the soul jars are craftable items whose use
  needs Armory Lib.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gen_phase1 import ASSETS, DATA, NS, edit_json, write_json  # noqa: E402

CONTENT = Path(__file__).resolve().parent.parent / "content"


def mod(attribute, amount, operation="add_value"):
    return {"type": f"minecraft:{attribute}", "id": f"{NS}:trinket_{attribute}", "amount": amount,
            "operation": operation, "slot": "offhand"}


# id: (name, lore, rarity, attribute modifiers in the off hand)
TRINKETS = {
    "aquite_ring": ("Aquite ring", "Mine at full speed and hold your breath longer under water",
                    "uncommon", [mod("submerged_mining_speed", 0.8), mod("oxygen_bonus", 1.0)]),
    "colosifite_charm": ("Colosifite charm", "Flames die down on you twice as fast",
                         "uncommon", [mod("burning_time", -0.5, "add_multiplied_base")]),
    "emerald_amulet": ("Emerald amulet", "Two more hearts", "uncommon", [mod("max_health", 4.0)]),
    "lapis_ring": ("Lapis ring", "More experience from every orb", "uncommon", []),
    "obsidian_charm": ("Obsidian charm", "Hits and blasts push you back much less",
                       "uncommon", [mod("knockback_resistance", 0.3),
                                    mod("explosion_knockback_resistance", 0.5)]),
    "quartz_ring": ("Quartz ring", "Light on your feet", "uncommon",
                    [mod("movement_speed", 0.1, "add_multiplied_total")]),
    "shadow_amulet": ("Shadow amulet", "Sneak more than twice as fast", "rare", [mod("sneaking_speed", 0.4)]),
    "ring_of_luck": ("Ring of luck", "The tarnished ring, made whole again", "rare", [mod("luck", 2.0)]),
}
HOLD = "Hold it in your off hand"

# id: (name, lore, rarity, stack size)
GEAR = {
    "backpack_small": ("Small backpack", "Carries 9 stacks", "common", 1),
    "backpack_medium": ("Backpack", "Carries 18 stacks", "uncommon", 1),
    "backpack_large": ("Large backpack", "Carries 27 stacks", "rare", 1),
    "recall_charm": ("Recall charm", "Takes you back to your bed or a waystone you have found", "rare", 1),
    "golem_core": ("Golem core", "Wakes an armory golem that follows and guards you", "rare", 1),
    "soul_jar": ("Soul jar", "Fills with the souls of what you slay", "uncommon", 1),
    "soul_jar_full": ("Full soul jar", "Souls for the soul forge", "rare", 1),
}

# id: (name, template, hardness, light, sounds, textures, glow textures, facing)
BLOCKS = {
    "waystone": ("Waystone", "minecraft:chiseled_stone_bricks", 3.0, 7, "minecraft:lodestone",
                 {"side": "waystone_side", "top": "waystone_top"},
                 {"side": "waystone_side_glow", "top": "waystone_top_glow"}, False),
    # glazed terracotta faces the player when placed (Horizon's place.rs), and has no other use
    "soul_forge": ("Soul forge", "minecraft:white_glazed_terracotta", 3.5, 10,
                   "minecraft:polished_blackstone_bricks",
                   {"front": "soul_forge_front", "side": "soul_forge_side", "top": "soul_forge_top"},
                   {"front": "soul_forge_front_glow", "top": "soul_forge_top_glow"}, True),
}

I = f"{NS}:"
RECIPES = {
    "aquite_ring": ([" N ", "NGN", " N "], {"N": "minecraft:iron_nugget", "G": I + "aquiteingot"}),
    "lapis_ring": ([" N ", "NGN", " N "], {"N": "minecraft:gold_nugget", "G": "minecraft:lapis_block"}),
    "quartz_ring": ([" N ", "NGN", " N "], {"N": "minecraft:gold_nugget", "G": "minecraft:quartz_block"}),
    "colosifite_charm": ([" S ", "NCN", " N "], {"S": "minecraft:string", "N": "minecraft:iron_nugget",
                                                "C": I + "colosifiteingot"}),
    "obsidian_charm": ([" S ", "NON", " N "], {"S": "minecraft:string", "N": "minecraft:gold_nugget",
                                              "O": I + "obsidainingot"}),
    "emerald_amulet": (["N N", "N N", " E "], {"N": "minecraft:gold_nugget", "E": "minecraft:emerald"}),
    "shadow_amulet": (["N N", "N N", " E "], {"N": "minecraft:iron_nugget", "E": I + "shadowingot"}),
    "recall_charm": ([" S ", "PCP", " A "], {"S": "minecraft:string", "P": "minecraft:ender_pearl",
                                           "C": "minecraft:compass", "A": I + "aquiteingot"}),
    "backpack_small": (["LSL", "LCL", "LLL"], {"L": "minecraft:leather", "S": "minecraft:string",
                                             "C": "minecraft:chest"}),
    "backpack_medium": (["III", "LBL", "LLL"], {"I": "minecraft:iron_ingot", "L": "minecraft:leather",
                                              "B": I + "backpack_small"}),
    "backpack_large": (["WWW", "GBG", "LLL"], {"W": "minecraft:red_wool", "G": "minecraft:gold_ingot",
                                             "B": I + "backpack_medium", "L": "minecraft:leather"}),
    "golem_core": (["IAI", "ADA", "IAI"], {"I": "minecraft:iron_block", "A": I + "aquiteingot",
                                         "D": "minecraft:diamond"}),
    "soul_jar": ([" P ", "GSG", "GGG"], {"P": "minecraft:oak_planks", "G": "minecraft:glass",
                                       "S": "minecraft:soul_sand"}),
    "waystone": (["BAB", "BPB", "BBB"], {"B": "minecraft:stone_bricks", "A": I + "aquiteingot",
                                       "P": "minecraft:ender_pearl"}),
    "soul_forge": (["BSB", "BFB", "BBB"], {"B": "minecraft:polished_blackstone_bricks",
                                         "S": I + "shadowingot", "F": "minecraft:blast_furnace"}),
}
SHAPELESS = {
    # the tarnished ring relic finally has a use
    "ring_of_luck": [I + "tarnished_ring", "minecraft:emerald", "minecraft:gold_ingot"],
}


def item(iid, name, lore, rarity, stack, modifiers=()):
    write_json(ASSETS / "models/item" / f"{iid}.json",
               {"parent": "minecraft:item/generated", "textures": {"layer0": f"{NS}:item/{iid}"}})
    write_json(ASSETS / "items" / f"{iid}.json",
               {"model": {"type": "minecraft:model", "model": f"{NS}:item/{iid}"}})
    components = {
        "minecraft:item_model": f"{NS}:{iid}",
        "minecraft:item_name": {"translate": f"item.{NS}.{iid}"},
        "!minecraft:cooking_fuel": {}, "!minecraft:repairable": {},
        "minecraft:lore": [{"text": line} for line in lore],
    }
    if modifiers:
        components["minecraft:attribute_modifiers"] = list(modifiers)
    write_json(DATA / "horizon/item" / f"{iid}.json", {
        "template": "minecraft:iron_ingot", "components": components,
        "max_stack_size": stack, "rarity": rarity})
    return {f"item.{NS}.{iid}": name}


def face(tex, side):
    return {"uv": [0, 0, 16, 16], "texture": f"#{tex}", "cullface": side}


def block(bid, name, template, hardness, light, sounds, tex, glow, facing):
    textures = {k: f"{NS}:block/{v}" for k, v in tex.items()}
    textures.update({f"{k}_glow": f"{NS}:block/{v}" for k, v in glow.items()})
    textures["particle"] = textures["side"]
    sides = {"down": "side" if facing else "top", "up": "top"}
    for side in ("north", "south", "east", "west"):
        sides[side] = "front" if (facing and side == "north") else "side"
    elements = [{"from": [0, 0, 0], "to": [16, 16, 16],
                 "faces": {s: face(t, s) for s, t in sides.items()}}]
    lit = {s: face(f"{t}_glow", s) for s, t in sides.items() if t in glow and s != "down"}
    elements.append({"from": [-0.005] * 3, "to": [16.005] * 3, "shade": False,
                     "light_emission": 15, "faces": lit})
    write_json(ASSETS / "models/block" / f"{bid}.json",
               {"parent": "minecraft:block/block", "textures": textures, "elements": elements})
    if facing:
        variants = {f"facing={d}": {"model": f"{NS}:block/{bid}", **({"y": y} if y else {})}
                    for d, y in (("north", 0), ("east", 90), ("south", 180), ("west", 270))}
    else:
        variants = {"": {"model": f"{NS}:block/{bid}"}}
    write_json(ASSETS / "blockstates" / f"{bid}.json", {"variants": variants})
    write_json(ASSETS / "models/item" / f"{bid}.json", {"parent": f"{NS}:block/{bid}"})
    write_json(ASSETS / "items" / f"{bid}.json",
               {"model": {"type": "minecraft:model", "model": f"{NS}:item/{bid}"}})
    write_json(DATA / "horizon/block" / f"{bid}.json", {
        "template": template,
        "properties": {"hardness": hardness, "light": light, "sounds": sounds},
        "item": True,
        "components": {"minecraft:item_model": f"{NS}:{bid}",
                       "minecraft:item_name": {"translate": f"block.{NS}.{bid}"},
                       "minecraft:max_stack_size": 64, "minecraft:rarity": "uncommon"}})
    write_json(DATA / "loot_table/blocks" / f"{bid}.json", {
        "type": "minecraft:block",
        "pools": [{"rolls": 1, "entries": [{"type": "minecraft:item", "name": f"{NS}:{bid}"}],
                   "conditions": [{"condition": "minecraft:survives_explosion"}]}]})
    return {f"block.{NS}.{bid}": name}


def recipes():
    for rid, (pattern, key) in RECIPES.items():
        write_json(DATA / "recipe" / f"{rid}.json", {
            "group": NS, "type": "minecraft:crafting_shaped", "pattern": pattern, "key": key,
            "result": {"id": f"{NS}:{rid}", "count": 1}})
    for rid, ingredients in SHAPELESS.items():
        write_json(DATA / "recipe" / f"{rid}.json", {
            "group": NS, "type": "minecraft:crafting_shapeless", "ingredients": ingredients,
            "result": {"id": f"{NS}:{rid}", "count": 1}})


def main():
    names, tab = {}, []
    for iid, (name, lore, rarity, mods) in TRINKETS.items():
        names.update(item(iid, name, [lore, HOLD] if mods else [lore], rarity, 1, mods))
        tab.append(f"{NS}:{iid}")
    for iid, (name, lore, rarity, stack) in GEAR.items():
        names.update(item(iid, name, [lore], rarity, stack))
        tab.append(f"{NS}:{iid}")
    for bid, spec in BLOCKS.items():
        names.update(block(bid, *spec))
        tab.append(f"{NS}:{bid}")
    recipes()

    blocks = [f"{NS}:{b}" for b in BLOCKS]

    def add_all(tag):
        tag["values"] = tag["values"] + [b for b in blocks if b not in tag["values"]]
    for tag in (CONTENT / "data/minecraft/tags/block/mineable/pickaxe.json",
                DATA / "tags/block/all_blocks.json"):
        edit_json(tag, add_all)
    edit_json(ASSETS / "lang/en_us.json", lambda lang: lang.update(names))
    edit_json(DATA / "horizon/creative_tab/armory.json",
              lambda t: t.__setitem__("items", t["items"] + [i for i in tab if i not in t["items"]]))
    print(f"{len(TRINKETS)} trinkets, {len(GEAR)} gear items, {len(BLOCKS)} blocks, "
          f"{len(RECIPES) + len(SHAPELESS)} recipes")


if __name__ == "__main__":
    main()
