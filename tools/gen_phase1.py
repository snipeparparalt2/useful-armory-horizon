#!/usr/bin/env python3
"""Release 0.2 "Places to loot": writes its data and art into content/.

    python3 tools/gen_phase1.py

Everything this release adds is generated here, so one file shows what it is made of:

  * deepslate versions of the three ores
  * six relic items that only come from loot
  * two guardian mob types (zombie-based) for spawners
  * nine structures: their building files (.nbt), worldgen files and biome tags
  * one loot table per structure, plus the guardians' drops

Re-running it rewrites the same files (the random choices are seeded). It needs Pillow for
the textures. It does not touch anything that existed before 0.2 except the three ore
features (deepslate now gets the deepslate ore), the language file, the creative tab and
the block tags, which it adds to.
"""
import gzip
import json
import random
import struct
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content"
ASSETS = CONTENT / "assets" / "useful_armory"
DATA = CONTENT / "data" / "useful_armory"
NS = "useful_armory"
DATA_VERSION = 5023          # Minecraft 26.3, as Horizon fdc87ae writes it


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n")


def edit_json(path, change):
    value = json.loads(path.read_text())
    change(value)
    write_json(path, value)


# ------------------------------------------------------------------ NBT (structure files)
class Short(int):
    pass


def _nbt_payload(v):
    if isinstance(v, bool):
        return 1, struct.pack(">b", int(v))
    if isinstance(v, Short):
        return 2, struct.pack(">h", int(v))
    if isinstance(v, int):
        return 3, struct.pack(">i", v)
    if isinstance(v, str):
        raw = v.encode("utf-8")
        return 8, struct.pack(">H", len(raw)) + raw
    if isinstance(v, dict):
        out = b""
        for key, item in v.items():
            tag, payload = _nbt_payload(item)
            name = key.encode("utf-8")
            out += struct.pack(">bH", tag, len(name)) + name + payload
        return 10, out + b"\x00"
    if isinstance(v, (list, tuple)):
        if not v:
            return 9, struct.pack(">bi", 0, 0)
        parts = [_nbt_payload(item) for item in v]
        tags = {t for t, _ in parts}
        assert len(tags) == 1, "a list holds one kind of tag"
        return 9, struct.pack(">bi", tags.pop(), len(parts)) + b"".join(p for _, p in parts)
    raise TypeError(type(v))


def write_nbt(path, root):
    tag, payload = _nbt_payload(root)
    assert tag == 10
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as raw:
        # mtime=0 keeps the file byte-identical between runs
        with gzip.GzipFile(fileobj=raw, mode="wb", mtime=0) as out:
            out.write(b"\x0a\x00\x00" + payload)


# ------------------------------------------------------------------ building pieces
def parse_block(text):
    """'minecraft:chest[facing=north]' -> ('minecraft:chest', {'facing': 'north'})."""
    if "[" not in text:
        return text, {}
    name, rest = text[:-1].split("[", 1)
    return name, dict(pair.split("=") for pair in rest.split(","))


AIR = "minecraft:air"


class Piece:
    """A box of blocks. Cells never set stay whatever the world has there."""

    def __init__(self, name, w, h, d, seed):
        self.name, self.size = name, (w, h, d)
        self.cells = {}
        self.rnd = random.Random(f"useful_armory/{seed}")

    def set(self, x, y, z, block, nbt=None):
        w, h, d = self.size
        assert 0 <= x < w and 0 <= y < h and 0 <= z < d, (self.name, x, y, z)
        self.cells[(x, y, z)] = (block, nbt)

    def fill(self, x0, y0, z0, x1, y1, z1, block):
        for x in range(x0, x1 + 1):
            for y in range(y0, y1 + 1):
                for z in range(z0, z1 + 1):
                    self.set(x, y, z, block() if callable(block) else block)

    def shell(self, x0, y0, z0, x1, y1, z1, block, inside=AIR):
        """A closed box of `block` with `inside` in it."""
        for x in range(x0, x1 + 1):
            for y in range(y0, y1 + 1):
                for z in range(z0, z1 + 1):
                    edge = x in (x0, x1) or y in (y0, y1) or z in (z0, z1)
                    self.set(x, y, z, (block() if callable(block) else block) if edge else inside)

    def mix(self, *weighted):
        """A block picked at random each time: mix(('a', 6), ('b', 1))."""
        names = [n for n, _ in weighted]
        weights = [w for _, w in weighted]
        return lambda: self.rnd.choices(names, weights)[0]

    def chest(self, x, y, z, table, facing="south", block="minecraft:chest"):
        state = f"{block}[facing={facing}]" if block != "minecraft:barrel" else "minecraft:barrel[facing=up]"
        self.set(x, y, z, state, {"id": block, "LootTable": f"{NS}:chests/{table}"})

    def spawner(self, x, y, z, entity):
        self.set(x, y, z, "minecraft:spawner", {
            "id": "minecraft:mob_spawner",
            "SpawnData": {"entity": {"id": entity}},
            "Delay": Short(20), "MinSpawnDelay": Short(200), "MaxSpawnDelay": Short(800),
            "SpawnCount": Short(2), "MaxNearbyEntities": Short(4),
            "RequiredPlayerRange": Short(16), "SpawnRange": Short(4),
        })

    def save(self):
        palette, index, blocks = [], {}, []
        for (x, y, z), (block, nbt) in sorted(self.cells.items(), key=lambda c: (c[0][1], c[0][2], c[0][0])):
            if block not in index:
                name, props = parse_block(block)
                entry = {"Name": name}
                if props:
                    entry["Properties"] = props
                index[block] = len(palette)
                palette.append(entry)
            cell = {"pos": [x, y, z], "state": index[block]}
            if nbt:
                cell["nbt"] = nbt
            blocks.append(cell)
        write_nbt(DATA / "structure" / f"{self.name}.nbt", {
            "size": list(self.size), "palette": palette, "blocks": blocks,
            "entities": [], "DataVersion": DATA_VERSION,
        })
        return len(blocks)


def ruined_forge():
    p = Piece("ruined_forge", 9, 6, 9, "forge")
    floor = p.mix(("minecraft:cobblestone", 5), ("minecraft:mossy_cobblestone", 2), ("minecraft:stone_bricks", 2))
    wall = p.mix(("minecraft:stone_bricks", 5), ("minecraft:cracked_stone_bricks", 2), ("minecraft:mossy_stone_bricks", 2))
    p.fill(0, 0, 0, 8, 0, 8, floor)
    p.fill(0, 1, 0, 8, 5, 8, AIR)
    for x in range(9):
        for z in range(9):
            if x in (0, 8) or z in (0, 8):
                corner = x in (0, 8) and z in (0, 8)
                # the walls have crumbled: lower away from the corners
                top = 4 if corner else p.rnd.choice((1, 2, 2, 3, 3))
                for y in range(1, top + 1):
                    p.set(x, y, z, wall())
    for y in (1, 2):
        p.set(4, y, 8, AIR)                                       # doorway
    p.set(1, 1, 1, "minecraft:furnace[facing=south,lit=false]")
    p.set(2, 1, 1, "minecraft:blast_furnace[facing=south,lit=false]")
    p.set(4, 1, 1, "minecraft:smithing_table")
    p.set(6, 1, 2, "minecraft:damaged_anvil[facing=north]")
    p.set(7, 1, 6, "minecraft:cauldron")
    p.set(7, 1, 1, "minecraft:mossy_cobblestone")
    p.set(6, 1, 7, "minecraft:cobblestone")
    p.chest(1, 1, 6, "ruined_forge", "east")
    return p


def wanderers_camp():
    p = Piece("wanderers_camp", 7, 4, 7, "camp")
    ground = p.mix(("minecraft:coarse_dirt", 3), ("minecraft:dirt_path", 1), ("minecraft:gravel", 1))
    p.fill(0, 0, 0, 6, 0, 6, ground)
    p.fill(0, 1, 0, 6, 3, 6, AIR)
    p.set(3, 0, 3, "minecraft:cobblestone")
    p.set(3, 1, 3, "minecraft:campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    for x0, z0, wool in ((0, 0, "minecraft:white_wool"), (4, 4, "minecraft:red_wool")):
        for z in range(z0, z0 + 3):                                # a ridge tent, open at both ends
            p.set(x0, 1, z, wool)
            p.set(x0 + 2, 1, z, wool)
            p.set(x0 + 1, 2, z, wool)
    p.chest(5, 1, 1, "wanderers_camp", block="minecraft:barrel")
    p.set(5, 1, 2, "minecraft:crafting_table")
    p.set(1, 1, 5, "minecraft:hay_block[axis=y]")
    p.set(3, 1, 5, "minecraft:spruce_log[axis=x]")
    p.set(1, 1, 3, "minecraft:spruce_log[axis=z]")
    p.set(2, 1, 4, "minecraft:lantern[hanging=false,waterlogged=false]")
    return p


def aquite_shrine():
    p = Piece("aquite_shrine", 7, 6, 7, "shrine")
    for x in range(7):
        for z in range(7):
            edge = x in (0, 6) or z in (0, 6)
            p.set(x, 0, z, "minecraft:dark_prismarine" if edge else "minecraft:prismarine_bricks")
    p.fill(0, 1, 0, 6, 5, 6, AIR)
    for x, z in ((1, 1), (5, 1), (1, 5), (5, 5)):
        p.fill(x, 1, z, x, 3, z, "minecraft:prismarine_bricks")
        p.set(x, 4, z, "minecraft:sea_lantern")
    for x, z in ((3, 0), (0, 3), (6, 3), (3, 6)):
        p.set(x, 1, z, f"{NS}:aquiteore")                         # glowing ore set in the rim
    p.fill(2, 1, 2, 4, 1, 4, "minecraft:prismarine")
    p.set(3, 1, 3, "minecraft:dark_prismarine")
    p.chest(3, 2, 3, "aquite_shrine", "south")
    return p


def colosifite_watchtower():
    p = Piece("colosifite_watchtower", 7, 15, 7, "tower")
    wall = p.mix(("minecraft:stone_bricks", 6), ("minecraft:cracked_stone_bricks", 2), ("minecraft:mossy_stone_bricks", 1))
    p.shell(0, 0, 0, 6, 12, 6, wall)
    for y in (4, 8):
        p.fill(1, y, 1, 5, y, 5, "minecraft:spruce_planks")       # upper floors
    for y in range(1, 13):
        p.set(3, y, 1, "minecraft:ladder[facing=south,waterlogged=false]")
    for y in (1, 2):
        p.set(3, y, 6, AIR)                                       # door
    for y in (6, 10):                                             # arrow slits
        for x, z in ((3, 0), (0, 3), (6, 3), (3, 6)):
            p.set(x, y, z, AIR)
    p.fill(0, 13, 0, 6, 14, 6, AIR)
    for x in range(7):                                            # battlements
        for z in range(7):
            if (x in (0, 6) or z in (0, 6)) and (x + z) % 2 == 0:
                corner = x in (0, 6) and z in (0, 6)
                p.set(x, 13, z, f"{NS}:colosfiteblock" if corner else wall())
    p.chest(1, 1, 5, "colosifite_watchtower", "north")
    p.chest(5, 9, 5, "colosifite_watchtower", "north")
    p.spawner(3, 9, 3, f"{NS}:tower_sentry")                      # roofed, so the sentries do not burn
    p.set(5, 5, 1, "minecraft:hay_block[axis=y]")
    p.set(1, 5, 5, "minecraft:barrel[facing=up]")
    return p


def pigman_outpost():
    p = Piece("pigman_outpost", 9, 6, 9, "outpost")
    brick = p.mix(("minecraft:nether_bricks", 6), ("minecraft:cracked_nether_bricks", 2))
    p.shell(0, 0, 0, 8, 5, 8, brick)
    for x, z in ((1, 1), (7, 1), (1, 7), (7, 7)):
        p.fill(x, 1, z, x, 4, z, "minecraft:gold_block" if (x, z) in ((1, 1), (7, 1)) else "minecraft:chiseled_nether_bricks")
    for y in (1, 2):
        p.set(4, y, 8, AIR)                                       # door
    p.set(4, 0, 4, "minecraft:magma_block")
    p.spawner(4, 1, 4, "minecraft:zombified_piglin")
    p.chest(4, 1, 1, "pigman_outpost", "south")
    p.set(3, 1, 1, "minecraft:gold_block")
    p.set(5, 1, 1, "minecraft:gold_block")
    p.set(2, 1, 6, "minecraft:lantern[hanging=false,waterlogged=false]")
    p.set(6, 1, 6, "minecraft:lantern[hanging=false,waterlogged=false]")
    return p


def shadow_vault():
    p = Piece("shadow_vault", 9, 7, 9, "vault")
    brick = p.mix(("minecraft:deepslate_bricks", 6), ("minecraft:cracked_deepslate_bricks", 2),
                  (f"{NS}:deepslate_shadow_ore", 1))
    p.shell(0, 0, 0, 8, 6, 8, brick)
    p.fill(1, 0, 1, 7, 0, 7, "minecraft:deepslate_tiles")
    for x, z in ((1, 1), (7, 1), (1, 7), (7, 7)):
        p.fill(x, 1, z, x, 5, z, f"{NS}:shadowblock")
    p.fill(3, 1, 3, 5, 1, 5, "minecraft:polished_deepslate")
    p.set(4, 1, 4, "minecraft:deepslate_tiles")
    p.spawner(4, 2, 4, f"{NS}:vault_guardian")
    p.chest(4, 1, 1, "shadow_vault", "south")
    for x, z in ((2, 1, ), (6, 1), (1, 4), (7, 4)):
        p.set(x, 1, z, "minecraft:soul_lantern[hanging=false,waterlogged=false]")
    return p


def miners_cache():
    p = Piece("miners_cache", 7, 6, 11, "cache")
    rock = p.mix(("minecraft:stone", 5), ("minecraft:cobblestone", 3), ("minecraft:andesite", 1))
    p.shell(1, 0, 0, 5, 4, 10, rock)
    for z in (2, 5, 8):                                           # timber frames
        for x in (1, 5):
            p.fill(x, 1, z, x, 3, z, "minecraft:oak_log[axis=y]")
        p.fill(1, 4, z, 5, 4, z, "minecraft:oak_planks")
    for z in range(1, 10):
        if z not in (4, 7):                                       # a few rails are missing
            p.set(3, 1, z, "minecraft:rail[shape=north_south,waterlogged=false]")
    p.chest(2, 1, 5, "miners_cache", block="minecraft:barrel")
    p.set(4, 1, 9, "minecraft:gravel")
    p.set(4, 2, 9, "minecraft:gravel")
    p.set(4, 1, 8, "minecraft:gravel")
    p.set(2, 1, 9, "minecraft:cobblestone")
    p.set(4, 3, 2, "minecraft:cobweb")
    p.set(2, 3, 8, "minecraft:cobweb")
    p.set(4, 1, 2, "minecraft:lantern[hanging=false,waterlogged=false]")
    p.set(2, 1, 6, f"{NS}:colosifiteore")
    return p


def forgotten_armory():
    p = Piece("forgotten_armory", 17, 6, 9, "armory")
    wall = p.mix(("minecraft:stone_bricks", 6), ("minecraft:cracked_stone_bricks", 2), ("minecraft:mossy_stone_bricks", 1))
    p.shell(0, 0, 0, 16, 5, 8, wall)
    for x in (5, 11):                                             # two inner walls, a doorway in each
        p.fill(x, 1, 1, x, 4, 7, wall)
        for y in (1, 2):
            p.set(x, y, 4, AIR)
    # west room: the library
    p.fill(1, 1, 1, 4, 2, 1, "minecraft:bookshelf")
    p.chest(1, 1, 7, "forgotten_armory", "north")
    p.set(4, 1, 7, "minecraft:lantern[hanging=false,waterlogged=false]")
    # middle room: the guard post
    for x, z in ((6, 1), (10, 1), (6, 7), (10, 7)):
        p.fill(x, 1, z, x, 4, z, "minecraft:chiseled_stone_bricks")
    p.spawner(8, 1, 4, f"{NS}:vault_guardian")
    p.set(8, 4, 2, "minecraft:cobweb")
    p.set(7, 4, 6, "minecraft:cobweb")
    # east room: the workshop
    p.set(15, 1, 1, "minecraft:smithing_table")
    p.set(14, 1, 1, "minecraft:damaged_anvil[facing=north]")
    p.set(12, 1, 1, "minecraft:grindstone[face=floor,facing=north]")
    p.set(15, 1, 4, f"{NS}:colosfiteblock")
    p.chest(15, 1, 7, "forgotten_armory", "north")
    p.set(12, 1, 7, "minecraft:lantern[hanging=false,waterlogged=false]")
    return p


def armory_blacksmith():
    p = Piece("village/armory_blacksmith", 9, 7, 9, "blacksmith")
    p.fill(0, 0, 0, 8, 0, 8, "minecraft:cobblestone")
    p.fill(0, 1, 0, 8, 6, 8, AIR)
    p.shell(0, 1, 0, 8, 4, 6, "minecraft:oak_planks")             # the shop
    p.fill(0, 1, 0, 8, 1, 6, "minecraft:cobblestone")             # stone footing course
    p.fill(1, 1, 1, 7, 1, 5, AIR)
    for x, z in ((0, 0), (8, 0), (0, 6), (8, 6), (0, 8), (8, 8)):
        p.fill(x, 1, z, x, 4, z, "minecraft:oak_log[axis=y]")
    p.fill(0, 4, 0, 8, 4, 8, "minecraft:spruce_planks")           # roof, over the porch too
    p.fill(1, 5, 1, 7, 5, 7, "minecraft:spruce_slab[type=bottom,waterlogged=false]")
    for y in (1, 2):
        p.set(4, y, 6, AIR)                                       # door
    p.set(2, 2, 6, "minecraft:glass")
    p.set(6, 2, 6, "minecraft:glass")
    p.chest(1, 1, 1, "village_blacksmith", "south")
    p.set(4, 1, 1, "minecraft:blast_furnace[facing=south,lit=false]")
    p.set(7, 1, 1, "minecraft:smithing_table")
    p.set(7, 1, 4, "minecraft:lantern[hanging=false,waterlogged=false]")
    # the porch
    p.set(1, 1, 7, "minecraft:furnace[facing=south,lit=false]")
    p.set(6, 1, 7, "minecraft:anvil[facing=east]")
    p.set(7, 1, 7, "minecraft:grindstone[face=floor,facing=north]")
    # where a village street joins on
    p.set(4, 0, 8, "minecraft:jigsaw[orientation=south_up]", {
        "id": "minecraft:jigsaw", "name": "minecraft:building_entrance",
        "target": "minecraft:building_entrance", "pool": "minecraft:empty",
        "final_state": "minecraft:cobblestone", "joint": "aligned",
        "selection_priority": 0, "placement_priority": 0,
    })
    return p


# name -> (piece, step, start height, on the surface?, terrain, biomes, spacing, separation, salt)
def uniform(lo, hi):
    return {"type": "minecraft:uniform", "min_inclusive": {"absolute": lo}, "max_inclusive": {"absolute": hi}}


STRUCTURES = {
    "ruined_forge": (ruined_forge, "surface_structures", {"absolute": -1}, True, "beard_thin",
                     ["#minecraft:is_forest", "minecraft:plains", "minecraft:sunflower_plains", "minecraft:meadow"],
                     28, 10, 418200101),
    "wanderers_camp": (wanderers_camp, "surface_structures", {"absolute": -1}, True, "beard_thin",
                       ["#minecraft:is_forest", "#minecraft:is_taiga", "#minecraft:is_savanna", "minecraft:plains",
                        "minecraft:snowy_plains", "minecraft:desert", "minecraft:meadow"],
                       24, 8, 418200102),
    "aquite_shrine": (aquite_shrine, "surface_structures", {"absolute": -1}, True, "beard_thin",
                      ["#minecraft:is_beach", "#minecraft:is_river", "minecraft:swamp", "minecraft:mangrove_swamp"],
                      30, 10, 418200103),
    "colosifite_watchtower": (colosifite_watchtower, "surface_structures", {"absolute": -1}, True, "beard_thin",
                              ["#minecraft:is_hill", "#minecraft:is_savanna", "#minecraft:is_badlands"],
                              34, 12, 418200104),
    "pigman_outpost": (pigman_outpost, "underground_structures", uniform(34, 60), False, "none",
                       ["minecraft:nether_wastes"], 20, 8, 418200105),
    "shadow_vault": (shadow_vault, "underground_structures", uniform(-52, -12), False, "none",
                     ["#minecraft:is_overworld"], 22, 8, 418200106),
    "miners_cache": (miners_cache, "underground_structures", uniform(0, 40), False, "none",
                     ["#minecraft:is_overworld"], 18, 6, 418200107),
    "forgotten_armory": (forgotten_armory, "underground_structures", uniform(-30, 20), False, "none",
                         ["#minecraft:is_overworld"], 40, 14, 418200108),
}
VILLAGES = ("plains", "desert", "savanna", "snowy", "taiga")


def structures():
    made = {}
    for name, (build, step, height, surface, terrain, biomes, spacing, separation, salt) in STRUCTURES.items():
        made[name] = build().save()
        structure = {
            "type": "minecraft:jigsaw", "biomes": f"#{NS}:has_structure/{name}", "step": step,
            "spawn_overrides": {}, "terrain_adaptation": terrain, "start_pool": f"{NS}:{name}/start",
            "size": 1, "start_height": height, "max_distance_from_center": 80,
        }
        if surface:
            structure["project_start_to_heightmap"] = "WORLD_SURFACE_WG"
        write_json(DATA / "worldgen/structure" / f"{name}.json", structure)
        write_json(DATA / "worldgen/template_pool" / name / "start.json", {
            "fallback": "minecraft:empty",
            "elements": [{"weight": 1, "element": {
                "element_type": "minecraft:single_pool_element", "location": f"{NS}:{name}",
                "projection": "rigid", "processors": "minecraft:empty"}}]})
        write_json(DATA / "worldgen/structure_set" / f"{name}.json", {
            "structures": [{"structure": f"{NS}:{name}", "weight": 1}],
            "placement": {"type": "minecraft:random_spread", "salt": salt,
                          "spacing": spacing, "separation": separation}})
        write_json(DATA / "tags/worldgen/biome/has_structure" / f"{name}.json", {"values": biomes})
    made["village/armory_blacksmith"] = armory_blacksmith().save()
    write_json(DATA / "worldgen/template_pool/village/armory_blacksmith.json", {
        "horizon:add_to": [f"minecraft:village/{v}/houses" for v in VILLAGES],
        "elements": [{"weight": 2, "element": {
            "element_type": "minecraft:single_pool_element", "location": f"{NS}:village/armory_blacksmith",
            "projection": "rigid", "processors": "minecraft:empty"}}]})
    return made


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
    # table: (uncommon pool, rare pool, weight of "nothing" in the rare pool)
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
}
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

    for name, (uncommon, rare, nothing) in CHESTS.items():
        check(COMMON), check(uncommon), check(rare)
        write_json(DATA / "loot_table/chests" / f"{name}.json", {
            "type": "minecraft:chest",
            "pools": [pool(3, 5, COMMON), pool(1, 3, uncommon), pool(1, 1, rare, nothing)]})
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
    relics_and_ores()
    known = {p.stem for p in (DATA / "horizon/item").glob("*.json")} | {p.stem for p in (DATA / "horizon/block").glob("*.json")}
    loot_and_mobs(known)
    for name, count in structures().items():
        print(f"structure {name}: {count} blocks")
    print(f"{len(RELICS)} relics, {len(DEEPSLATE_ORES)} deepslate ores, {len(MOBS)} mob types, {len(CHESTS)} chest tables")


if __name__ == "__main__":
    main()
