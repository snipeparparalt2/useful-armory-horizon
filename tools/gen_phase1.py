#!/usr/bin/env python3
"""Release 0.1.7 "Places": writes its data and art into content/.

    python3 -I tools/gen_phase1.py [--schema path/to/block_schema.json]

Everything this release adds is generated here and in the modules it imports:

  * deepslate versions of the three ores
  * six relic items that only come from loot
  * two guardian mob types (zombie-based) for spawners
  * one loot table per place, plus the guardians' drops
  * the places themselves: tools/structures/ (one module per place, built with
    tools/structkit.py) give the building files (.nbt), worldgen files and biome tags

With --schema every block of every piece is checked against the block-state schema first;
any problem stops the run (exit 1) before anything is written.

Re-running it rewrites the same files (the random choices are seeded). It needs Pillow for
the textures. The structure step owns, and empties before writing, data/useful_armory/
structure/, worldgen/structure/, worldgen/structure_set/, worldgen/template_pool/ and
tags/worldgen/biome/has_structure/. Outside those it touches nothing that existed before
0.2 except the three ore features (deepslate now gets the deepslate ore), the language
file, the creative tab and the block tags, which it adds to.
"""
import argparse
import json
import shutil
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import structkit  # noqa: E402
from structkit import CONTENT, DATA, NS  # noqa: E402

ASSETS = CONTENT / "assets" / "useful_armory"


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n")


def edit_json(path, change):
    value = json.loads(path.read_text())
    change(value)
    write_json(path, value)


# ------------------------------------------------------------------ places
OWNED = ["structure", "worldgen/structure", "worldgen/structure_set", "worldgen/template_pool",
         "tags/worldgen/biome/has_structure"]


def _q(path):
    return path if ":" in path else f"{NS}:{path}"


def height(value):
    if isinstance(value, int):
        return {"absolute": value}
    if isinstance(value, (tuple, list)):
        lo, hi = value
        return {"type": "minecraft:uniform", "min_inclusive": {"absolute": lo},
                "max_inclusive": {"absolute": hi}}
    return value


def pool_element(spec):
    """(piece, weight) or a dict (see tools/structures/__init__.py) -> a pool entry."""
    if isinstance(spec, (tuple, list)):
        spec = {"piece": spec[0], "weight": spec[1]}
    if spec.get("empty"):
        return {"weight": spec.get("weight", 1), "element": {"element_type": "minecraft:empty_pool_element"}}
    element = {"element_type": "minecraft:single_pool_element", "location": _q(spec["piece"]),
               "projection": spec.get("projection", "rigid"),
               "processors": spec.get("processors", "minecraft:empty")}
    if "guaranteed" in spec:
        element = {"element_type": "lithostitched:guaranteed", "delegate": element,
                   "count": spec["guaranteed"], "min_depth": spec.get("min_depth", 0)}
    elif "limit" in spec:
        element = {"element_type": "lithostitched:limited", "delegate": element,
                   "limit": spec["limit"], "min_depth": spec.get("min_depth", 0)}
    return {"weight": spec.get("weight", 1), "element": element}


def place_pools(place):
    """{pool path: (fallback id, [element specs])} for a jigsaw place."""
    name = place["name"]
    pools = place.get("pools") or {f"{name}/start": [(piece, 1) for piece in place["pieces"]]}
    out = {}
    for path, value in pools.items():
        if isinstance(value, dict):
            out[path] = (_q(value.get("fallback", "minecraft:empty")), list(value["elements"]))
        else:
            out[path] = ("minecraft:empty", list(value))
    return out


def _piece_of(spec):
    if isinstance(spec, (tuple, list)):
        return spec[0]
    return None if spec.get("empty") else spec["piece"]


def check_places(places, built):
    """Problems with how the places fit together (names, pools, connectors, loot, mobs)."""
    problems = []
    names = [p["name"] for p in places]
    for dup in sorted({n for n in names if names.count(n) > 1}):
        problems.append(f"place {dup} is defined twice")
    owner = {}
    for place in places:
        for key in place["pieces"]:
            if key in owner:
                problems.append(f"piece {key} belongs to {owner[key]} and {place['name']}")
            owner[key] = place["name"]
            if built[key].name != key:
                problems.append(f"piece {key}: its builder names it {built[key].name!r}")
            w, _, d = built[key].size
            if w > 48 or d > 48:
                problems.append(f"piece {key}: {w} x {d} is wider than 48 x 48")
    for place in places:
        if "add_to" in place:
            continue
        for key in ("step", "start_height", "terrain", "biomes", "spacing", "separation", "salt"):
            if key not in place:
                problems.append(f"place {place['name']}: no {key}")
        if not 0 < place.get("separation", 0) < place.get("spacing", 0):
            problems.append(f"place {place['name']}: separation must be below spacing")
        pools = place_pools(place)
        start = place.get("start_pool", f"{place['name']}/start")
        if start not in pools:
            problems.append(f"place {place['name']}: start pool {start} is not among its pools")
        pool_pieces = {}
        for path, (fallback, elements) in pools.items():
            pieces = [_piece_of(e) for e in elements]
            for piece in pieces:
                if piece is not None and piece not in place["pieces"]:
                    problems.append(f"pool {path}: piece {piece} is not one of {place['name']}'s pieces")
            pool_pieces[_q(path)] = ([p for p in pieces if p in place["pieces"]], fallback)
            if fallback != "minecraft:empty" and fallback not in {_q(k) for k in pools}:
                problems.append(f"pool {path}: fallback {fallback} is not a pool of {place['name']}")
        used = {p for path, (_, els) in pools.items() for p in map(_piece_of, els) if p}
        for key in place["pieces"]:
            if key not in used:
                problems.append(f"piece {key} is in no pool of {place['name']}")
        for key in place["pieces"]:
            piece = built[key]
            w, h, d = piece.size
            for (x, y, z), orientation, nbt in piece.jigsaws():
                pool, target = nbt.get("pool", "minecraft:empty"), nbt.get("target", "minecraft:empty")
                if pool == "minecraft:empty":
                    continue
                if pool not in pool_pieces:
                    problems.append(f"{key} jigsaw at {(x, y, z)}: pool {pool} is not a pool of {place['name']}")
                    continue
                names_there = set()
                fallback_chain, seen = [pool], set()
                while fallback_chain:
                    current = fallback_chain.pop()
                    if current in seen or current not in pool_pieces:
                        continue
                    seen.add(current)
                    for other in pool_pieces[current][0]:
                        names_there |= {n.get("name") for _, _, n in built[other].jigsaws()}
                    fallback_chain.append(pool_pieces[current][1])
                if target not in names_there:
                    problems.append(f"{key} jigsaw at {(x, y, z)}: no piece in {pool} (or its fallback) "
                                    f"has a jigsaw named {target}")
                front = orientation.split("_")[0]
                dx, dy, dz = structkit.VECTOR[front]
                if piece.in_bounds(x + dx, y + dy, z + dz):
                    problems.append(f"{key} jigsaw at {(x, y, z)} faces {front} into its own piece; "
                                    f"connectors sit in the outer layer facing out")
    for key, piece in built.items():
        for (x, y, z), (b, nbt) in sorted(piece.cells.items()):
            if not nbt:
                continue
            table = nbt.get("LootTable")
            if table:
                stem = table.split("chests/", 1)[-1]
                if not table.startswith(f"{NS}:chests/") or stem not in CHESTS:
                    problems.append(f"{key} {(x, y, z)}: loot table {table} is not one of CHESTS")
            entity = nbt.get("SpawnData", {}).get("entity", {}).get("id")
            if entity and entity.startswith(NS + ":") and entity.split(":")[1] not in MOBS:
                problems.append(f"{key} {(x, y, z)}: spawner mob {entity} is not one of MOBS")
    return problems


def structures(schema_path=None):
    from structures import PLACES

    built = {}
    for place in PLACES:
        for key, build in place["pieces"].items():
            assert key not in built, f"piece {key} is built twice"
            built[key] = build()
    problems = check_places(PLACES, built)
    if schema_path:
        schema = structkit.load_schema(schema_path)
        known = structkit.mod_blocks()
        for piece in built.values():
            problems += piece.validate(schema, known)
    if problems:
        print(f"{len(problems)} structure problem(s):", file=sys.stderr)
        for problem in problems:
            print("  " + problem, file=sys.stderr)
        sys.exit(1)

    for owned in OWNED:
        shutil.rmtree(DATA / owned, ignore_errors=True)
    made = {key: piece.save(DATA / "structure" / f"{key}.nbt") for key, piece in built.items()}
    for place in PLACES:
        name = place["name"]
        if "add_to" in place:
            write_json(DATA / "worldgen/template_pool" / f"{name}.json", {
                "horizon:add_to": list(place["add_to"]),
                "elements": [pool_element((piece, place.get("weight", 1))) for piece in place["pieces"]]})
            continue
        structure = {
            "type": "minecraft:jigsaw", "biomes": f"#{NS}:has_structure/{name}", "step": place["step"],
            "spawn_overrides": {}, "terrain_adaptation": place["terrain"],
            "start_pool": _q(place.get("start_pool", f"{name}/start")),
            "size": place.get("size", 1), "start_height": height(place["start_height"]),
            "max_distance_from_center": place.get("max_distance", 80),
        }
        if place.get("surface"):
            structure["project_start_to_heightmap"] = "WORLD_SURFACE_WG"
        write_json(DATA / "worldgen/structure" / f"{name}.json", structure)
        for path, (fallback, elements) in place_pools(place).items():
            write_json(DATA / "worldgen/template_pool" / f"{path}.json", {
                "fallback": fallback, "elements": [pool_element(e) for e in elements]})
        write_json(DATA / "worldgen/structure_set" / f"{name}.json", {
            "structures": [{"structure": f"{NS}:{name}", "weight": 1}],
            "placement": {"type": "minecraft:random_spread", "salt": place["salt"],
                          "spacing": place["spacing"], "separation": place["separation"]}})
        write_json(DATA / "tags/worldgen/biome/has_structure" / f"{name}.json", {"values": list(place["biomes"])})
    return made, built


# ------------------------------------------------------------------ loot
def item(name, weight, lo=1, hi=1, worn=False):
    entry = {"type": "minecraft:item", "name": name if ":" in name else f"{NS}:{name}", "weight": weight}
    functions = []
    if hi > 1:
        functions.append({"function": "minecraft:set_count",
                          "count": {"type": "minecraft:uniform", "min": lo, "max": hi}})
    if worn:                                                      # found gear is part-used
        functions.append({"function": "minecraft:set_damage",
                          "damage": {"type": "minecraft:uniform", "min": 0.25, "max": 0.8}})
    if functions:
        entry["functions"] = functions
    return entry


def pool(lo, hi, entries, nothing=0):
    entries = list(entries)
    if nothing:
        entries.append({"type": "minecraft:empty", "weight": nothing})
    rolls = lo if lo == hi else {"type": "minecraft:uniform", "min": lo, "max": hi}
    return {"rolls": rolls, "entries": entries}


COMMON = [item("minecraft:bread", 8, 1, 3), item("minecraft:coal", 8, 1, 4), item("minecraft:iron_nugget", 6, 2, 6),
          item("minecraft:lapis_lazuli", 5, 1, 4), item("minecraft:quartz", 5, 1, 4), item("minecraft:redstone", 5, 1, 4),
          item("redstoneingot", 3, 1, 2), item("longstick", 4, 1, 2), item("minecraft:stick", 4, 1, 4)]
CHESTS = {
    # table: (uncommon pool, rare pool, weight of "nothing" in the rare pool[, rolls overriding ROLLS])
    "ruined_forge": ([item("colosifiteingot", 6, 1, 3), item("aquiteingot", 4, 1, 2), item("obsidainingot", 3, 1, 2),
                      item("minecraft:iron_ingot", 6, 1, 4), item("quartzpickaxe", 2, worn=True),
                      item("redstoneaxe", 2, worn=True)],
                     [item("ancient_hilt", 3), item("forge_hammer_head", 3), item("swordpart1", 1)], 8),
    "wanderers_camp": ([item("minecraft:cooked_beef", 6, 1, 3), item("lapissword", 2, worn=True),
                        item("quartzamorboots", 2, worn=True),
                        item("lapisarmorhelmet", 2, worn=True), item("minecraft:emerald", 4, 1, 3)],
                       [item("tarnished_ring", 3), item("faded_map_scrap", 4)], 9),
    "aquite_shrine": ([item("aquiteingot", 8, 2, 4), item("minecraft:prismarine_crystals", 5, 1, 4),
                       item("minecraft:emerald", 3, 1, 2)],
                      [item("aquitesword", 2, worn=True), item("aquitepickaxe", 2, worn=True),
                       item("aquitedagger", 2, worn=True), item("tarnished_ring", 2)], 6),
    "colosifite_watchtower": ([item("colosifiteingot", 8, 1, 4), item("minecraft:arrow", 6, 4, 12),
                               item("colosifitedagger", 2, worn=True), item("colosifitearmorhelmet", 2, worn=True),
                               item("minecraft:iron_ingot", 5, 1, 3)],
                              [item("faded_map_scrap", 4), item("colosifitehalbert", 1, worn=True),
                               item("ancient_hilt", 2)], 8),
    "pigman_outpost": ([item("minecraft:gold_ingot", 8, 1, 5), item("minecraft:gold_nugget", 6, 3, 9),
                        item("emagma", 3, 1, 2), item("minecraft:magma_cream", 4, 1, 3),
                        item("minecraft:quartz", 5, 2, 6)],
                       [item("pigmansword", 1, worn=True), item("swordpart2", 1), item("cracked_soul_gem", 2)], 10),
    "shadow_vault": ([item("shadowore", 5, 1, 3), item("shadowingot", 4, 1, 2), item("obsidainingot", 4, 1, 3),
                      item("shadow_shard", 6, 1, 3), item("minecraft:diamond", 2, 1, 2)],
                     [item("cracked_soul_gem", 3), item("swordpart3", 2), item("shadowdagger", 1, worn=True)], 6),
    "miners_cache": ([item("colosifiteore", 6, 1, 4), item("aquiteore", 5, 1, 3), item("redstoneingot", 5, 1, 3),
                      item("obsidainstring", 3, 1, 2), item("minecraft:rail", 5, 2, 8),
                      item("redstonepicaxe", 2, worn=True)],
                     [item("tarnished_ring", 2), item("faded_map_scrap", 3), item("diamondstick", 1)], 9),
    "forgotten_armory": ([item("emeraldarmorhelmet", 1, worn=True), item("obsidainarmorbody", 1, worn=True),
                          item("colosifitearmorlegs", 2, worn=True), item("aquiteboots", 2, worn=True),
                          item("quartzamorbody", 2, worn=True), item("lapisarmorlegs", 2, worn=True),
                          item("redstonearmorboots", 2, worn=True), item("obsidainingot", 4, 1, 3),
                          item("shadowingot", 2, 1, 2)],
                         [item("cracked_soul_gem", 3), item("ancient_hilt", 3), item("forge_hammer_head", 3),
                          item("swordpart1", 1), item("swordpart2", 1)], 4),
    "village_blacksmith": ([item("minecraft:iron_ingot", 8, 1, 4), item("colosifiteingot", 4, 1, 2),
                            item("aquiteingot", 3, 1, 2), item("longstick", 5, 1, 3),
                            item("quartzsword", 2), item("lapispickaxe", 2), item("redstoneshovel", 2)],
                           [item("forge_hammer_head", 2), item("minecraft:diamond", 1)], 10),
    "bandit_fort": ([item("minecraft:emerald", 6, 1, 4), item("minecraft:arrow", 6, 4, 12),
                     item("minecraft:iron_ingot", 5, 1, 3), item("minecraft:crossbow", 2, worn=True),
                     item("colosifiteingot", 3, 1, 2), item("lapissword", 2, worn=True),
                     item("redstoneaxe", 2, worn=True), item("quartzamorhelmet", 2, worn=True)],
                    [item("tarnished_ring", 3), item("faded_map_scrap", 4), item("ancient_hilt", 2)], 8),
    "infested_mine": ([item("minecraft:string", 8, 2, 6), item("minecraft:spider_eye", 5, 1, 3),
                       item("colosifiteore", 5, 1, 3), item("aquiteore", 4, 1, 2), item("redstoneingot", 4, 1, 3),
                       item("minecraft:rail", 4, 2, 6), item("obsidainstring", 3, 1, 2),
                       item("redstonepicaxe", 2, worn=True), item("colosifitepickaxe", 1, worn=True)],
                      [item("faded_map_scrap", 3), item("tarnished_ring", 2), item("diamondstick", 1)], 9),
    "crypt": ([item("minecraft:bone", 8, 2, 6), item("minecraft:gold_nugget", 6, 2, 8),
               item("minecraft:candle", 4, 1, 3), item("shadow_shard", 4, 1, 2), item("obsidainingot", 3, 1, 2),
               item("aquitedagger", 2, worn=True), item("lapisdagger", 2, worn=True)],
              [item("cracked_soul_gem", 2), item("ancient_hilt", 3), item("tarnished_ring", 3)], 9),
    # the one treasure room per crypt: more rolls, better items, and the rare pool nearly always pays
    "crypt_treasure": ([item("minecraft:diamond", 4, 1, 3), item("minecraft:gold_ingot", 6, 2, 6),
                        item("minecraft:emerald", 5, 2, 5), item("shadowingot", 5, 1, 3), item("obsidainingot", 5, 2, 4),
                        item("shadowdagger", 2, worn=True), item("shadowsword", 2, worn=True),
                        item("colosifitehalbert", 2, worn=True), item("shadowhelmet", 2, worn=True)],
                       [item("cracked_soul_gem", 4), item("swordpart2", 2), item("swordpart3", 2),
                        item("forge_hammer_head", 2), item("ultimatenugget", 1)], 1,
                       {"uncommon": (3, 5), "rare": (1, 2)}),
}
ROLLS = {"common": (3, 5), "uncommon": (1, 3), "rare": (1, 1)}
MOBS = {
    # id: (name, attributes, drops)
    "vault_guardian": ("Vault guardian",
                       {"minecraft:max_health": 30.0, "minecraft:movement_speed": 0.25,
                        "minecraft:attack_damage": 5.0, "minecraft:armor": 6.0},
                       [("minecraft:rotten_flesh", 0, 2, None), ("shadow_shard", 1, 1, 0.3)]),
    "tower_sentry": ("Tower sentry",
                     {"minecraft:max_health": 24.0, "minecraft:movement_speed": 0.27,
                      "minecraft:attack_damage": 4.0, "minecraft:armor": 4.0},
                     [("minecraft:rotten_flesh", 0, 2, None), ("colosifiteingot", 1, 1, 0.2),
                      ("faded_map_scrap", 1, 1, 0.05)]),
}


def loot_and_mobs(known_items):
    used = set()

    def check(entries):
        for e in entries:
            if e["type"] == "minecraft:item" and e["name"].startswith(NS + ":"):
                used.add(e["name"].split(":")[1])

    for name, (uncommon, rare, nothing, *more) in CHESTS.items():
        rolls = {**ROLLS, **(more[0] if more else {})}
        check(COMMON), check(uncommon), check(rare)
        write_json(DATA / "loot_table/chests" / f"{name}.json", {
            "type": "minecraft:chest",
            "pools": [pool(*rolls["common"], COMMON), pool(*rolls["uncommon"], uncommon),
                      pool(*rolls["rare"], rare, nothing)]})
    for mob, (_, attributes, drops) in MOBS.items():
        write_json(DATA / "horizon/entity_type" / f"{mob}.json",
                   {"template": "minecraft:zombie", "attributes": attributes})
        pools = []
        for name, lo, hi, chance in drops:
            entry = item(name, 1)
            check([entry])
            del entry["weight"]
            entry["functions"] = [{"function": "minecraft:set_count",
                                   "count": {"type": "minecraft:uniform", "min": lo, "max": hi}}]
            one = {"rolls": 1, "entries": [entry]}
            if chance:
                one["conditions"] = [{"condition": "minecraft:random_chance", "chance": chance}]
            pools.append(one)
        write_json(DATA / "loot_table/entities" / f"{mob}.json", {"type": "minecraft:entity", "pools": pools})
    missing = sorted(used - known_items)
    assert not missing, f"loot names items the mod does not have: {missing}"


# ------------------------------------------------------------------ art
def sprite(rows, colours):
    assert len(rows) == 16 and all(len(r) == 16 for r in rows), [len(r) for r in rows]
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch != ".":
                c = colours[ch]
                img.putpixel((x, y), (int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16), 255))
    return img


RELICS = {
    # id: (name, tooltip, rarity, rows, colours)
    "cracked_soul_gem": ("Cracked soul gem", "Something is still moving inside it", "rare", [
        "................",
        "................",
        ".....oooooo.....",
        "....olllllmo....",
        "...olwllkmmdo...",
        "..olwllkmmmddo..",
        "..ollllkkmmddo..",
        "..olllmmkmdddo..",
        "...ommmmkkddo...",
        "...ommmkdmddo...",
        "....ommkdddo....",
        ".....omddko.....",
        "......oddo......",
        ".......oo.......",
        "................",
        "................",
    ], {"o": "2a1030", "d": "6a2a7a", "m": "b05ac0", "l": "e8a0ec", "w": "f8e0fa", "k": "2a1030"}),
    "ancient_hilt": ("Ancient hilt", "The blade is long gone", "uncommon", [
        "................",
        "................",
        "................",
        "..........oo....",
        ".........osso...",
        "........osseo...",
        ".....oo.oseo....",
        "....oygooeo.....",
        ".....oygyo......",
        "......ogygo.....",
        ".....obtogyo....",
        "....obto.oo.....",
        "...obto.........",
        "..oyyo..........",
        "..ogyo..........",
        "...oo...........",
    ], {"o": "2b2118", "g": "b8860b", "y": "e8c84a", "b": "6b4a2a", "t": "8f6a3e", "s": "9aa0a8", "e": "5a6068"}),
    "forge_hammer_head": ("Forge master's hammer head", "Still warm", "uncommon", [
        "................",
        "................",
        "................",
        "...oooooooooo...",
        "..ommmmmmmmmlo..",
        "..omlllllllhlo..",
        "..omlmmmmmmllo..",
        "..omdmrqqrmdlo..",
        "..omdmrqqrmdlo..",
        "..omdmmmmmmdlo..",
        "..omddddddddmo..",
        "..odddddddddmo..",
        "...oooooooooo...",
        "................",
        "................",
        "................",
    ], {"o": "1e1e22", "d": "4a4d55", "m": "7b808a", "l": "b4bac4", "h": "e6e9ee", "r": "f28c18", "q": "ffba42"}),
    "shadow_shard": ("Shadow shard", "Cold to the touch", "uncommon", [
        "................",
        ".........o......",
        "........olo.....",
        ".......olvo.....",
        ".......omlo.....",
        "......olmvo.....",
        ".....olmmlo.....",
        ".....omlvmo.....",
        "....olmmmdo.....",
        "....omvmddo.....",
        "...olmmddo......",
        "...omlmddo......",
        "....omddo.......",
        ".....odo........",
        "......o.........",
        "................",
    ], {"o": "020207", "d": "161728", "m": "24263f", "l": "3c3f63", "v": "8d7be0", "w": "d9b8ff"}),
    "tarnished_ring": ("Tarnished ring", "It was worth something once", "uncommon", [
        "................",
        "................",
        "................",
        "......oooo......",
        ".....oGGgo......",
        "....oogggoo.....",
        "...omloooomo....",
        "..omlo....omo...",
        "..omo......omo..",
        "..omo......odo..",
        "..omo......odo..",
        "...omo....odo...",
        "....ommooddo....",
        ".....oddddo.....",
        "......oooo......",
        "................",
    ], {"o": "2a2416", "d": "5a5030", "m": "8a7a48", "l": "b8a868", "g": "4a7a5a", "G": "7ab08a"}),
    "faded_map_scrap": ("Faded map scrap", "Most of the markings have worn away", "common", [
        "................",
        "................",
        "..ooooooooo.....",
        "..opsssssppo....",
        "..opsiiisspqo...",
        "..opssssispqo...",
        "..oppsisssppo...",
        "...opsisrsrpo...",
        "..oppiisssrspo..",
        "..opssssrsrpo...",
        "..opqsisssspo...",
        "...oqqppsppqo...",
        "....oo.oqqoo....",
        ".......ooo......",
        "................",
        "................",
    ], {"o": "5a4a2a", "p": "d8c898", "q": "c0ae7c", "s": "e8dcb4", "i": "6a5038", "r": "a03020"}),
}
DEEPSLATE_ORES = {
    # id: (stone ore id, texture stem, name, glows, hardness, ingot)
    "deepslate_aquite_ore": ("aquiteore", "aquite_ore", "§bDeepslate aquite ore", True, 2.8, "aquiteingot"),
    "deepslate_colosifite_ore": ("colosifiteore", "colosifite_ore", "§6Deepslate colosifite ore", False, 3.5, "colosifiteingot"),
    "deepslate_shadow_ore": ("shadowore", "shadow_ore", "§8Deepslate shadow ore", True, 3.0, "shadowingot"),
}
STONE_SHADOW = (0x58, 0x58, 0x58, 255)          # the pocket shadow in the stone overlays
DEEPSLATE_SHADOW = (0x2a, 0x2a, 0x30, 255)      # the same shadow, dark enough for deepslate


def faces(texture):
    return {side: {"uv": [0, 0, 16, 16], "texture": texture, "cullface": side}
            for side in ("down", "up", "north", "south", "east", "west")}


def relics_and_ores():
    names, tab = {}, []
    for rid, (name, tip, rarity, rows, colours) in RELICS.items():
        sprite(rows, colours).save(ASSETS / "textures/item" / f"{rid}.png")
        write_json(ASSETS / "models/item" / f"{rid}.json",
                   {"parent": "minecraft:item/generated", "textures": {"layer0": f"{NS}:item/{rid}"}})
        write_json(ASSETS / "items" / f"{rid}.json",
                   {"model": {"type": "minecraft:model", "model": f"{NS}:item/{rid}"}})
        write_json(DATA / "horizon/item" / f"{rid}.json", {
            "template": "minecraft:iron_ingot",
            "components": {
                "minecraft:item_model": f"{NS}:{rid}",
                "minecraft:item_name": {"translate": f"item.{NS}.{rid}"},
                "!minecraft:cooking_fuel": {}, "!minecraft:repairable": {},
                "minecraft:lore": [{"text": tip}],
            },
            "max_stack_size": 16, "rarity": rarity})
        names[f"item.{NS}.{rid}"] = name
        tab.append(f"{NS}:{rid}")
    blocks = []
    for bid, (stone_id, stem, name, glows, hardness, ingot) in DEEPSLATE_ORES.items():
        overlay = Image.open(ASSETS / "textures/block" / f"{stem}.png").convert("RGBA")
        for y in range(16):
            for x in range(16):
                if overlay.getpixel((x, y)) == STONE_SHADOW:
                    overlay.putpixel((x, y), DEEPSLATE_SHADOW)
        overlay.save(ASSETS / "textures/block" / f"deepslate_{stem}.png")
        textures = {"stone": "minecraft:block/deepslate", "ore": f"{NS}:block/deepslate_{stem}",
                    "particle": "minecraft:block/deepslate"}
        elements = [{"from": [0, 0, 0], "to": [16, 16, 16], "faces": faces("#stone")},
                    {"from": [-0.0025] * 3, "to": [16.0025] * 3, "faces": faces("#ore")}]
        if glows:                                                 # the same glow layer as the stone ore
            textures["glow"] = f"{NS}:block/{stem}_e"
            elements.append({"from": [-0.005] * 3, "to": [16.005] * 3, "shade": False,
                             "light_emission": 15, "faces": faces("#glow")})
        write_json(ASSETS / "models/block" / f"{bid}.json",
                   {"parent": "minecraft:block/block", "textures": textures, "elements": elements})
        write_json(ASSETS / "blockstates" / f"{bid}.json", {"variants": {"": {"model": f"{NS}:block/{bid}"}}})
        write_json(ASSETS / "models/item" / f"{bid}.json", {"parent": f"{NS}:block/{bid}"})
        write_json(ASSETS / "items" / f"{bid}.json",
                   {"model": {"type": "minecraft:model", "model": f"{NS}:item/{bid}"}})
        write_json(DATA / "horizon/block" / f"{bid}.json", {
            "template": "minecraft:deepslate_iron_ore",
            "properties": {"hardness": hardness, "light": 0},
            "item": True,
            "components": {"minecraft:item_model": f"{NS}:{bid}",
                           "minecraft:item_name": {"translate": f"block.{NS}.{bid}"}}})
        write_json(DATA / "loot_table/blocks" / f"{bid}.json", {
            "type": "minecraft:block",
            "pools": [{"rolls": 1, "entries": [{"type": "minecraft:item", "name": f"{NS}:{bid}"}]}]})
        write_json(DATA / "recipe" / f"{bid}_smelting.json", {
            "type": "minecraft:smelting", "ingredient": f"{NS}:{bid}",
            "result": {"id": f"{NS}:{ingot}"}, "experience": 1, "cookingtime": 200})

        def deepslate_target(feature, bid=bid):
            for target in feature["targets"]:
                if target["target"]["tag"] == "minecraft:deepslate_ore_replaceables":
                    target["state"] = f"{NS}:{bid}"
        edit_json(DATA / "worldgen/feature" / f"ore_{stem.split('_')[0]}.json", deepslate_target)
        names[f"block.{NS}.{bid}"] = name
        blocks.append(f"{NS}:{bid}")
        tab.append(f"{NS}:{bid}")
    for mob, (name, _, _) in MOBS.items():
        names[f"entity.{NS}.{mob}"] = name

    def add_all(tag):
        tag["values"] = tag["values"] + [b for b in blocks if b not in tag["values"]]
    for tag in (CONTENT / "data/minecraft/tags/block/mineable/pickaxe.json",
                CONTENT / "data/minecraft/tags/block/needs_stone_tool.json",
                DATA / "tags/block/all_blocks.json"):
        edit_json(tag, add_all)
    edit_json(ASSETS / "lang/en_us.json", lambda lang: lang.update(names))
    edit_json(DATA / "horizon/creative_tab/armory.json",
              lambda t: t.__setitem__("items", t["items"] + [i for i in tab if i not in t["items"]]))


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--schema", help="block_schema.json to validate every structure block against")
    args = parser.parse_args()
    made, _ = structures(args.schema)        # checks first: exits 1 before writing on a problem
    relics_and_ores()
    known = {p.stem for p in (DATA / "horizon/item").glob("*.json")} | {p.stem for p in (DATA / "horizon/block").glob("*.json")}
    loot_and_mobs(known)
    for name, count in made.items():
        print(f"structure {name}: {count} blocks")
    print(f"{len(RELICS)} relics, {len(DEEPSLATE_ORES)} deepslate ores, {len(MOBS)} mob types, "
          f"{len(CHESTS)} chest tables, {len(made)} structure pieces"
          + (" (validated)" if args.schema else ""))


if __name__ == "__main__":
    main()
