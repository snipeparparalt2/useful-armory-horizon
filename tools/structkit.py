#!/usr/bin/env python3
"""Toolkit for building Useful Armory's structure pieces (vanilla structure .nbt files).

    python3 -I tools/structkit.py --selftest

A `Piece` is a box of cells. Cells never set keep whatever the world has there; set
`minecraft:air` to carve. Coordinates are piece-local: x east, y up, z south, all from 0.

Direction words used everywhere below (they are Minecraft's):
  north = -z, south = +z, west = -x, east = +x.

What each helper's `facing` means (Minecraft's own conventions, so the states are vanilla's):
  stairs     facing = the side of the tall back; the direction you move when walking UP them.
  door       facing = the direction the placing player looked; the closed panel lies on the
             cell edge OPPOSITE `facing` (the near side). Walk through it in `facing` direction
             to "push" it. hinge left/right is seen by that player.
  trapdoor   facing = the direction away from the block it hangs on: an open trapdoor lies
             against the cell's -facing side. A shutter on a wall's outside face: facing = the
             wall's outward normal.
  ladder, wall_torch, wall signs: facing = away from the wall they are fixed to.
  bed        facing = from foot to head (head cell = foot + facing).
  chest, furnace, barrel...: facing = the side the front/lid points to.
  jigsaw     orientation = "<front>_<top>": front points OUT of the piece toward the
             neighbour that will attach (see tools/structures/crypt.py for the conventions).

Connection blocks (fence, wall, pane, bars) are placed as bare ids; `finalize()` (run by
`save()` and `validate()`) sets their north/east/south/west (and wall up/heights) from the
neighbours. A bare `minecraft:oak_fence` given to `set`/`fill` is treated the same way.
"""
import fnmatch
import gzip
import json
import random
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content"
NS = "useful_armory"
DATA = CONTENT / "data" / NS
DATA_VERSION = 5023          # Minecraft 26.3, as Horizon fdc87ae writes it
AIR = "minecraft:air"

HORIZONTAL = ("north", "east", "south", "west")          # clockwise order
VECTOR = {"north": (0, 0, -1), "south": (0, 0, 1), "west": (-1, 0, 0), "east": (1, 0, 0),
          "up": (0, 1, 0), "down": (0, -1, 0)}
OPPOSITE = {"north": "south", "south": "north", "east": "west", "west": "east", "up": "down", "down": "up"}


def cw(d):
    return HORIZONTAL[(HORIZONTAL.index(d) + 1) % 4] if d in HORIZONTAL else d


def ccw(d):
    return HORIZONTAL[(HORIZONTAL.index(d) + 3) % 4] if d in HORIZONTAL else d


# ------------------------------------------------------------------ NBT
class Byte(int):
    pass


class Short(int):
    pass


class Long(int):
    pass


class Float(float):
    pass


def _nbt_payload(v):
    if isinstance(v, bool):
        return 1, struct.pack(">b", int(v))
    if isinstance(v, Byte):
        return 1, struct.pack(">b", int(v))
    if isinstance(v, Short):
        return 2, struct.pack(">h", int(v))
    if isinstance(v, Long):
        return 4, struct.pack(">q", int(v))
    if isinstance(v, int):
        return 3, struct.pack(">i", v)
    if isinstance(v, Float):
        return 5, struct.pack(">f", float(v))
    if isinstance(v, float):
        return 6, struct.pack(">d", v)
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
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as raw:
        # mtime=0 keeps the file byte-identical between runs
        with gzip.GzipFile(fileobj=raw, mode="wb", mtime=0) as out:
            out.write(b"\x0a\x00\x00" + payload)


def _read(b, i, t):
    if t == 1:
        return Byte(struct.unpack_from(">b", b, i)[0]), i + 1
    if t == 2:
        return Short(struct.unpack_from(">h", b, i)[0]), i + 2
    if t == 3:
        return struct.unpack_from(">i", b, i)[0], i + 4
    if t == 4:
        return Long(struct.unpack_from(">q", b, i)[0]), i + 8
    if t == 5:
        return Float(struct.unpack_from(">f", b, i)[0]), i + 4
    if t == 6:
        return struct.unpack_from(">d", b, i)[0], i + 8
    if t in (7, 11, 12):
        n = struct.unpack_from(">i", b, i)[0]
        size, fmt = {7: (1, "b"), 11: (4, "i"), 12: (8, "q")}[t]
        return list(struct.unpack_from(f">{n}{fmt}", b, i + 4)), i + 4 + n * size
    if t == 8:
        n = struct.unpack_from(">H", b, i)[0]
        return b[i + 2:i + 2 + n].decode("utf-8"), i + 2 + n
    if t == 9:
        et, n = struct.unpack_from(">bi", b, i)
        i += 5
        out = []
        for _ in range(n):
            v, i = _read(b, i, et)
            out.append(v)
        return out, i
    if t == 10:
        d = {}
        while True:
            tt = b[i]
            i += 1
            if tt == 0:
                return d, i
            n = struct.unpack_from(">H", b, i)[0]
            k = b[i + 2:i + 2 + n].decode("utf-8")
            i += 2 + n
            d[k], i = _read(b, i, tt)
    raise ValueError(f"NBT tag {t}")


def read_nbt(path):
    raw = gzip.open(path).read()
    assert raw[0] == 10, "root is a compound"
    n = struct.unpack_from(">H", raw, 1)[0]
    return _read(raw, 3 + n, 10)[0]


# ------------------------------------------------------------------ block strings
def parse_block(text):
    """'minecraft:chest[facing=north]' -> ('minecraft:chest', {'facing': 'north'})."""
    if "[" not in text:
        return text, {}
    name, rest = text[:-1].split("[", 1)
    return name, dict(pair.split("=") for pair in rest.split(",")) if rest else {}


def block_name(text):
    return text.split("[", 1)[0]


def state(name, **props):
    """state('minecraft:oak_stairs', facing='north', ...) with properties sorted by key."""
    if not props:
        return name
    return f"{name}[{','.join(f'{k}={_s(v)}' for k, v in sorted(props.items()))}]"


def _s(v):
    return ("true" if v else "false") if isinstance(v, bool) else str(v)


def _ns(name):
    return name if ":" in name else f"minecraft:{name}"


def block_id(material, kind):
    """The id of a shape of a material: block_id('stone_bricks', 'stairs') ->
    'minecraft:stone_brick_stairs'; ('oak', 'slab') -> 'minecraft:oak_slab';
    ('oak_planks', 'fence') -> 'minecraft:oak_fence'. A full id ending in _<kind> is kept."""
    material = _ns(material)
    if material.endswith("_" + kind):
        return material
    ns, base = material.split(":", 1)
    for suffix in ("_planks", "_block"):
        if base.endswith(suffix):
            base = base[: -len(suffix)]
            break
    if base.endswith("bricks") or base.endswith("tiles"):
        base = base[:-1]
    return f"{ns}:{base}_{kind}"


WOODS = ("oak", "spruce", "birch", "jungle", "acacia", "dark_oak", "mangrove", "cherry",
         "pale_oak", "bamboo", "crimson", "warped")
DYES = ("white", "orange", "magenta", "light_blue", "yellow", "lime", "pink", "gray",
        "light_gray", "cyan", "purple", "blue", "brown", "green", "red", "black")

# Families that are never a full solid cube (for fence/pane/wall connections). Matched
# against the id's path (no namespace) as an exact name or a suffix.
NOT_SOLID_EXACT = {
    "air", "cave_air", "void_air", "structure_void", "light", "barrier", "water", "lava",
    "bubble_column", "fire", "soul_fire", "nether_portal", "end_portal", "end_gateway",
    "moving_piston", "piston_head", "cobweb", "scaffolding", "ladder", "vine", "glow_lichen",
    "sculk_vein", "resin_clump", "chest", "trapped_chest", "ender_chest", "cake", "flower_pot",
    "lectern", "enchanting_table", "end_portal_frame", "brewing_stand", "hopper", "bell",
    "grindstone", "stonecutter", "composter", "conduit", "dragon_egg", "turtle_egg",
    "sniffer_egg", "sea_pickle", "frogspawn", "lily_pad", "cactus", "cactus_flower", "bamboo",
    "bamboo_sapling", "sugar_cane", "kelp", "kelp_plant", "seagrass", "tall_seagrass",
    "short_grass", "tall_grass", "grass", "fern", "large_fern", "dead_bush", "bush",
    "firefly_bush", "short_dry_grass", "tall_dry_grass", "leaf_litter", "wildflowers",
    "pink_petals", "spore_blossom", "azalea", "flowering_azalea", "big_dripleaf",
    "big_dripleaf_stem", "small_dripleaf", "hanging_roots", "pointed_dripstone",
    "dandelion", "poppy", "blue_orchid", "allium", "azure_bluet", "oxeye_daisy", "cornflower",
    "lily_of_the_valley", "wither_rose", "torchflower", "sunflower", "lilac", "rose_bush",
    "peony", "pitcher_plant", "pitcher_crop", "torchflower_crop", "open_eyeblossom",
    "closed_eyeblossom", "brown_mushroom", "red_mushroom", "wheat", "carrots", "potatoes",
    "beetroots", "melon_stem", "pumpkin_stem", "attached_melon_stem", "attached_pumpkin_stem",
    "nether_wart", "cocoa", "sweet_berry_bush", "chorus_plant", "chorus_flower", "snow",
    "powder_snow", "farmland", "dirt_path", "honey_block", "end_rod", "lightning_rod",
    "redstone_wire", "repeater", "comparator", "lever", "tripwire", "tripwire_hook",
    "daylight_detector", "sculk_sensor", "calibrated_sculk_sensor", "sculk_shrieker",
    "decorated_pot", "heavy_core", "dried_ghast", "creaking_heart_placeholder",
    # not full for connection purposes (vanilla's isExceptionForConnection)
    "pumpkin", "carved_pumpkin", "jack_o_lantern", "melon",
}
NOT_SOLID_SUFFIX = (
    "_stairs", "_slab", "_fence", "_fence_gate", "_wall", "_pane", "_bars", "_door",
    "_trapdoor", "_carpet", "_bed", "_sign", "_banner", "_button", "_pressure_plate", "torch",
    "candle", "_candle_cake", "_skull", "_head", "rail", "_sapling", "_propagule", "_tulip",
    "_leaves", "_coral", "_coral_fan", "_coral_wall_fan", "_roots", "_fungus", "vines",
    "vines_plant", "_vein", "_cluster", "_amethyst_bud", "_plant", "campfire", "cauldron",
    "anvil", "chain", "lantern", "shulker_box", "_rod", "_shelf", "_golem_statue",
    "_mushroom", "_egg", "_cake",
)
FULL_DESPITE_SUFFIX = {"sea_lantern", "mushroom_stem"}


def is_full_solid(block):
    """Conservative guess whether a block is a full solid cube that fences, panes and walls
    connect to. Unknown blocks count as solid; the non-solid families are listed above."""
    if block is None:
        return False
    path = block_name(block).split(":", 1)[-1]
    if path in FULL_DESPITE_SUFFIX:
        return True
    if path in NOT_SOLID_EXACT or path.startswith("potted_"):
        return False
    return not any(path.endswith(s) for s in NOT_SOLID_SUFFIX)


def _connect_kind(block):
    """'fence', 'gate', 'wall', 'pane' or None for a block string."""
    if block is None:
        return None
    path = block_name(block).split(":", 1)[-1]
    if path.endswith("_fence_gate"):
        return "gate"
    if path.endswith("_fence"):
        return "fence"
    if path.endswith("_wall"):
        return "wall"
    if path.endswith("_pane") or path.endswith("_bars"):
        return "pane"
    return None


def _fence_family(block):
    return "nether" if block_name(block) == "minecraft:nether_brick_fence" else "wood"


def _gate_connects(gate, direction):
    """FenceGateBlock.connectsToDirection: a gate facing east/west sits in a north-south run."""
    facing = parse_block(gate)[1].get("facing")
    if facing is None:
        return True
    return (facing in ("east", "west")) == (direction in ("north", "south"))


# ------------------------------------------------------------------ rotation and mirroring
def _rail_shape(shape, m):
    if shape.startswith("ascending_"):
        return "ascending_" + m(shape[10:])
    a, b = shape.split("_")
    a, b = m(a), m(b)
    if {a, b} in ({"north", "south"}, {"east", "west"}):
        return "north_south" if "north" in (a, b) else "east_west"
    ns_ = a if a in ("north", "south") else b
    ew = b if ns_ == a else a
    return f"{ns_}_{ew}"


def transform_state(text, m, quarter_turns=0, mirrored=False):
    """Map a block state through a horizontal transform. `m` maps a horizontal direction
    word; `quarter_turns` is the clockwise rotation (axis x/z swap when odd, 16-step rotation);
    `mirrored` is True for an x-mirror (left/right swap, 16-step rotation reflects)."""
    name, props = parse_block(text)
    if not props:
        return text
    out = {}
    for k, v in props.items():
        if k in HORIZONTAL:
            out[m(k)] = v
            continue
        if k == "facing" and v in HORIZONTAL:
            v = m(v)
        elif k == "axis" and quarter_turns % 2 and v in ("x", "z"):
            v = "z" if v == "x" else "x"
        elif k == "orientation":
            front, top = v.split("_")
            v = f"{m(front) if front in HORIZONTAL else front}_{m(top) if top in HORIZONTAL else top}"
        elif k == "shape" and name.endswith("_stairs"):
            if mirrored:
                v = v.replace("left", "@").replace("right", "left").replace("@", "right")
        elif k == "shape" and "rail" in name:
            v = _rail_shape(v, m)
        elif k == "rotation":
            r = int(v)
            if mirrored:
                r = (16 - r) % 16
            v = str((r + 4 * quarter_turns) % 16)
        elif k in ("hinge", "type") and mirrored and v in ("left", "right"):
            v = "right" if v == "left" else "left"
        out[k] = v
    return f"{name}[{','.join(f'{k}={out[k]}' for k in sorted(out))}]"


# ------------------------------------------------------------------ the piece
def mod_blocks():
    """Our own block ids, from the block definitions in content/."""
    return {f"{NS}:{p.stem}" for p in (DATA / "horizon/block").glob("*.json")}


class Piece:
    """A box of blocks (w x h x d). Cells never set stay whatever the world has there."""

    def __init__(self, name, w, h, d, seed):
        self.name, self.size = name, (w, h, d)
        self.cells = {}
        self.rnd = random.Random(f"useful_armory/{seed}")
        self._waterlogged_markers = set()

    # ---- basics
    def in_bounds(self, x, y, z):
        w, h, d = self.size
        return 0 <= x < w and 0 <= y < h and 0 <= z < d

    def set(self, x, y, z, block, nbt=None):
        assert self.in_bounds(x, y, z), (self.name, x, y, z)
        if callable(block):
            block = block()
        self.cells[(x, y, z)] = (block, nbt)
        self._waterlogged_markers.discard((x, y, z))

    def get(self, x, y, z):
        """The block string at a cell, or None when the cell is not set (or outside)."""
        cell = self.cells.get((x, y, z))
        return cell[0] if cell else None

    def get_nbt(self, x, y, z):
        cell = self.cells.get((x, y, z))
        return cell[1] if cell else None

    def is_set(self, x, y, z):
        return (x, y, z) in self.cells

    def unset(self, x, y, z):
        self.cells.pop((x, y, z), None)

    @staticmethod
    def box_cells(box):
        x0, y0, z0, x1, y1, z1 = box
        for y in range(min(y0, y1), max(y0, y1) + 1):
            for z in range(min(z0, z1), max(z0, z1) + 1):
                for x in range(min(x0, x1), max(x0, x1) + 1):
                    yield x, y, z

    def fill(self, x0, y0, z0, x1, y1, z1, block):
        """Every cell of the box. `block` may be a callable (see `mix`), called per cell."""
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

    def walls(self, x0, y0, z0, x1, y1, z1, block):
        """The four side walls of the box (its perimeter on every layer), no floor or roof."""
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                for z in range(z0, z1 + 1):
                    if x in (x0, x1) or z in (z0, z1):
                        self.set(x, y, z, block)

    def floor(self, x0, y, z0, x1, z1, block):
        """One layer at height y over x0..x1, z0..z1."""
        self.fill(x0, y, z0, x1, y, z1, block)

    def pillar(self, x, z, y0, y1, block):
        """A column at (x, z) from y0 to y1 inclusive."""
        self.fill(x, y0, z, x, y1, z, block)

    def line(self, x0, y0, z0, x1, y1, z1, block):
        """A straight (possibly diagonal) line of cells, both ends included."""
        n = max(abs(x1 - x0), abs(y1 - y0), abs(z1 - z0))
        for i in range(n + 1):
            t = i / n if n else 0
            self.set(round(x0 + (x1 - x0) * t), round(y0 + (y1 - y0) * t),
                     round(z0 + (z1 - z0) * t), block)

    def clear(self, box):
        """Set every cell of box (x0, y0, z0, x1, y1, z1) to air."""
        for x, y, z in self.box_cells(box):
            self.set(x, y, z, AIR)

    @staticmethod
    def _matcher(match):
        if callable(match):
            return match
        if isinstance(match, (set, list, tuple, frozenset)):
            names = {_ns(m) for m in match}
            return lambda b: b is not None and (b in names or block_name(b) in names)
        full = _ns(match)
        return lambda b: b is not None and (b == full or block_name(b) == full)

    def replace(self, box, match, to, chance=1.0):
        """Within box, swap blocks matching `match` (a name, set of names or a predicate on
        the block string; names match with or without properties) for `to` (block or
        callable). With chance < 1, each match is swapped with that seeded probability.
        Unset cells are never touched. Block-entity data on a swapped cell is dropped."""
        hit = self._matcher(match)
        n = 0
        for x, y, z in self.box_cells(box):
            b = self.get(x, y, z)
            if hit(b) and (chance >= 1 or self.rnd.random() < chance):
                self.set(x, y, z, to)
                n += 1
        return n

    def scatter(self, box, block, chance, only_on=None):
        """Seeded: put `block` into empty cells (air or unset) of box with probability
        `chance`. With `only_on` (name, set or predicate) the cell below must match too."""
        below = self._matcher(only_on) if only_on is not None else None
        n = 0
        for x, y, z in self.box_cells(box):
            b = self.get(x, y, z)
            if b not in (None, AIR):
                continue
            if below is not None and not below(self.get(x, y - 1, z)):
                continue
            if self.rnd.random() < chance:
                self.set(x, y, z, block)
                n += 1
        return n

    # ---- shaped blocks (each writes every state property)
    def stairs(self, x, y, z, material, facing, half="bottom", shape="straight", waterlogged=False):
        """facing = side of the tall back = direction you move walking up. half 'top' is
        upside-down. shape straight / inner_left / inner_right / outer_left / outer_right:
        outer_left keeps only the back quarter on the left (facing's counter-clockwise
        side), outer_right the one on the right; inner_* add the front quarter on that side."""
        self.set(x, y, z, state(block_id(material, "stairs"), facing=facing, half=half,
                                shape=shape, waterlogged=waterlogged))

    def slab(self, x, y, z, material, type="bottom", waterlogged=False):
        self.set(x, y, z, state(block_id(material, "slab"), type=type, waterlogged=waterlogged))

    def door(self, x, y, z, wood, facing, hinge="left", open=False):
        """Both halves, lower at y. facing = direction of the placing player's look; the
        closed panel sits on the cell edge opposite facing."""
        name = block_id(wood, "door")
        for half, dy in (("lower", 0), ("upper", 1)):
            self.set(x, y + dy, z, state(name, facing=facing, half=half, hinge=hinge,
                                         open=open, powered=False))

    def trapdoor(self, x, y, z, wood, facing, half="bottom", open=False, waterlogged=False):
        """Closed: a plate in the bottom (or top) of the cell. Open: a plate against the
        cell's -facing side (facing points away from what it hangs on)."""
        self.set(x, y, z, state(block_id(wood, "trapdoor"), facing=facing, half=half, open=open,
                                powered=False, waterlogged=waterlogged))

    def bed(self, x, y, z, colour, facing):
        """Foot at (x, y, z), head at foot + facing."""
        dx, _, dz = VECTOR[facing]
        name = f"minecraft:{colour}_bed"
        self.set(x, y, z, state(name, facing=facing, occupied=False, part="foot"))
        self.set(x + dx, y, z + dz, state(name, facing=facing, occupied=False, part="head"))

    def ladder(self, x, y, z, facing, waterlogged=False):
        """facing = away from the wall the ladder is on (the wall is at -facing)."""
        self.set(x, y, z, state("minecraft:ladder", facing=facing, waterlogged=waterlogged))

    def ladder_column(self, x, z, y0, y1, facing):
        for y in range(y0, y1 + 1):
            self.ladder(x, y, z, facing)

    def lantern(self, x, y, z, hanging=False, soul=False, waterlogged=False):
        self.set(x, y, z, state("minecraft:soul_lantern" if soul else "minecraft:lantern",
                                hanging=hanging, waterlogged=waterlogged))

    def chain(self, x, y, z, axis="y"):
        """26.3 calls the chain block minecraft:iron_chain."""
        self.set(x, y, z, state("minecraft:iron_chain", axis=axis, waterlogged=False))

    def hanging_lantern(self, x, y, z, chain=1, soul=False):
        """A lantern at y hanging from `chain` chain links above it."""
        self.lantern(x, y, z, hanging=True, soul=soul)
        for i in range(1, chain + 1):
            self.chain(x, y + i, z)

    def candle(self, x, y, z, colour=None, candles=1, lit=True):
        name = f"minecraft:{colour}_candle" if colour else "minecraft:candle"
        self.set(x, y, z, state(name, candles=candles, lit=lit, waterlogged=False))

    def torch(self, x, y, z, soul=False):
        self.set(x, y, z, "minecraft:soul_torch" if soul else "minecraft:torch")

    def wall_torch(self, x, y, z, facing, soul=False):
        """facing = away from the wall the torch is fixed to."""
        name = "minecraft:soul_wall_torch" if soul else "minecraft:wall_torch"
        self.set(x, y, z, state(name, facing=facing))

    def log(self, x, y, z, wood, axis="y", stripped=False, bark=False):
        """wood: oak, spruce, ... (crimson/warped give stems). bark=True gives the *_wood
        (all-bark) block."""
        wood = wood.split(":")[-1]
        nether = wood in ("crimson", "warped")
        kind = ("hyphae" if nether else "wood") if bark else ("stem" if nether else "log")
        name = f"minecraft:{'stripped_' if stripped else ''}{wood}_{kind}"
        self.set(x, y, z, state(name, axis=axis))

    def barrel(self, x, y, z, facing="up", open=False):
        """A decorative barrel (no loot). For loot use chest(..., block='minecraft:barrel')."""
        self.set(x, y, z, state("minecraft:barrel", facing=facing, open=open))

    def carpet(self, x, y, z, colour):
        self.set(x, y, z, f"minecraft:{colour}_carpet")

    def wool(self, colour):
        return f"minecraft:{colour}_wool"

    def skull(self, x, y, z, rotation=0, kind="skeleton"):
        """A floor skull; rotation 0 = facing south, 4 west, 8 north, 12 east."""
        self.set(x, y, z, state(f"minecraft:{kind}_skull" if kind in ("skeleton", "wither_skeleton")
                                else f"minecraft:{kind}_head", powered=False, rotation=rotation))

    # ---- connection blocks (resolved by finalize)
    def _marker(self, x, y, z, name, waterlogged):
        self.set(x, y, z, name)
        if waterlogged:
            self._waterlogged_markers.add((x, y, z))

    def fence(self, x, y, z, material="oak", waterlogged=False):
        """Connects to same-family fences, fence gates (in line) and full solid blocks."""
        self._marker(x, y, z, block_id(material, "fence"), waterlogged)

    def fence_gate(self, x, y, z, wood, facing, open=False, in_wall=False):
        """facing = the direction you look through the gate (it sits in a run across it)."""
        self.set(x, y, z, state(block_id(wood, "fence_gate"), facing=facing, in_wall=in_wall,
                                open=open, powered=False))

    def wall(self, x, y, z, material="cobblestone", waterlogged=False):
        """Connects to walls, panes, bars, in-line gates and full solid blocks."""
        self._marker(x, y, z, block_id(material, "wall"), waterlogged)

    def pane(self, x, y, z, block="minecraft:glass_pane", waterlogged=False):
        """Connects to panes, bars, walls and full solid blocks."""
        self._marker(x, y, z, _ns(block), waterlogged)

    def bars(self, x, y, z, waterlogged=False):
        self._marker(x, y, z, "minecraft:iron_bars", waterlogged)

    def finalize(self):
        """Resolve bare fence / wall / pane / bars ids into full states from the neighbours."""
        todo = {pos: b for pos, (b, _) in self.cells.items() if "[" not in b and _connect_kind(b) in ("fence", "wall", "pane")}
        conns = {}
        for (x, y, z), b in todo.items():
            kind = _connect_kind(b)
            sides = {}
            for d in HORIZONTAL:
                dx, _, dz = VECTOR[d]
                nb = self.get(x + dx, y, z + dz)
                nk = _connect_kind(nb)
                if kind == "fence":
                    ok = (nk == "fence" and _fence_family(nb) == _fence_family(b)) or \
                         (nk == "gate" and _gate_connects(nb, d)) or is_full_solid(nb)
                elif kind == "pane":
                    ok = nk in ("pane", "wall") or is_full_solid(nb)
                else:
                    ok = nk in ("wall", "pane") or (nk == "gate" and _gate_connects(nb, d)) or is_full_solid(nb)
                sides[d] = ok
            conns[(x, y, z)] = sides

        def wall_sides(pos):
            if pos in conns:
                return conns[pos]
            b = self.get(*pos)
            props = parse_block(b)[1] if b else {}
            return {d: props.get(d, "none") != "none" for d in HORIZONTAL}

        for (x, y, z), b in todo.items():
            kind, sides = _connect_kind(b), conns[(x, y, z)]
            wl = (x, y, z) in self._waterlogged_markers
            if kind != "wall":
                self.cells[(x, y, z)] = (state(b, waterlogged=wl, **sides), self.cells[(x, y, z)][1])
                continue
            above = self.get(x, y + 1, z)
            above_kind = _connect_kind(above)
            if is_full_solid(above):
                tall = {d: True for d in HORIZONTAL}
            elif above_kind == "wall":
                tall = wall_sides((x, y + 1, z))
            else:
                tall = {d: False for d in HORIZONTAL}
            heights = {d: ("tall" if tall[d] else "low") if sides[d] else "none" for d in HORIZONTAL}
            on = [d for d in HORIZONTAL if sides[d]]
            straight = len(on) == 2 and OPPOSITE[on[0]] == on[1] and heights[on[0]] == heights[on[1]]
            up = not (straight and above in (None, AIR))
            self.cells[(x, y, z)] = (state(b, up=up, waterlogged=wl, **heights), self.cells[(x, y, z)][1])
        self._waterlogged_markers.clear()

    # ---- roofs
    def gable_roof(self, x0, x1, z0, z1, y, material, ridge_axis, overhang=1, gable_fill=None,
                   ridge_slab=True, under=None):
        """A gabled roof over the footprint x0..x1, z0..z1 (usually the outer wall line).
        ridge_axis 'x': the ridge runs east-west and the slopes face north and south; 'z'
        the other way. The lowest stair course is at height y on the eaves, `overhang` cells
        outside the footprint on every side; each course steps in one cell and up one.
        Odd span: a bottom slab ridge (ridge_slab=True), the block given (ridge_slab='id'),
        or nothing (False). Even span: the top stairs meet. gable_fill: a block filling each gable end wall (the footprint
        ends) from y up to under the roof line. under: a block put under each stair inside the
        footprint (a solid backing, so the roof is two thick). Returns the ridge height."""
        if ridge_axis == "x":
            a0, a1, b0, b1 = x0, x1, z0, z1          # along ridge a, across b
            rise_lo, rise_hi = "south", "north"
            at = lambda a, b: (a, b)                  # noqa: E731
        else:
            a0, a1, b0, b1 = z0, z1, x0, x1
            rise_lo, rise_hi = "east", "west"
            at = lambda a, b: (b, a)                  # noqa: E731
        lo, hi, i = b0 - overhang, b1 + overhang, 0
        top = y
        while lo <= hi:
            yy = y + i
            for a in range(a0 - overhang, a1 + overhang + 1):
                for b, facing in ((lo, rise_lo), (hi, rise_hi)):
                    cx, cz = at(a, b)
                    if not self.in_bounds(cx, yy, cz):
                        continue
                    if lo == hi:
                        if isinstance(ridge_slab, str):
                            self.set(cx, yy, cz, ridge_slab)
                        elif ridge_slab:
                            self.slab(cx, yy, cz, material)
                    else:
                        self.stairs(cx, yy, cz, material, facing)
                    if under and a0 <= a <= a1 and b0 <= b <= b1 and yy - 1 >= 0 and lo != hi:
                        self.set(cx, yy - 1, cz, under)
            if gable_fill:
                for b in range(max(lo + 1, b0), min(hi - 1, b1) + 1):
                    for a in (a0, a1):
                        cx, cz = at(a, b)
                        if self.in_bounds(cx, yy, cz):
                            self.set(cx, yy, cz, gable_fill)
            top = yy
            lo, hi, i = lo + 1, hi - 1, i + 1
        return top

    def hip_roof(self, x0, x1, z0, z1, y, material, overhang=1, ridge_slab=True):
        """A hipped roof: every side slopes. Rings of stairs step in and up from the eaves at
        height y (overhang outside the footprint); corners use outer stair shapes; when one
        side runs out a one-wide ridge line closes it (ridge_slab as in gable_roof). Returns the top height."""
        lx, hx, lz, hz = x0 - overhang, x1 + overhang, z0 - overhang, z1 + overhang
        yy = y
        while lx <= hx and lz <= hz:
            if lx == hx or lz == hz:                   # a one-wide ridge line
                for cx in range(lx, hx + 1):
                    for cz in range(lz, hz + 1):
                        if self.in_bounds(cx, yy, cz):
                            if isinstance(ridge_slab, str):
                                self.set(cx, yy, cz, ridge_slab)
                            elif ridge_slab:
                                self.slab(cx, yy, cz, material)
                break
            for cx in range(lx, hx + 1):
                for cz in range(lz, hz + 1):
                    if cx not in (lx, hx) and cz not in (lz, hz):
                        continue
                    if not self.in_bounds(cx, yy, cz):
                        continue
                    fz = "south" if cz == lz else "north" if cz == hz else None
                    fx = "east" if cx == lx else "west" if cx == hx else None
                    if fz and fx:                    # corner: tall quarter toward the inside
                        shape = "outer_left" if ccw(fz) == fx else "outer_right"
                        self.stairs(cx, yy, cz, material, fz, shape=shape)
                    else:
                        self.stairs(cx, yy, cz, material, fz or fx)
            lx, hx, lz, hz, yy = lx + 1, hx - 1, lz + 1, hz - 1, yy + 1
        return yy

    # ---- block entities
    def chest(self, x, y, z, table, facing=None, block="minecraft:chest"):
        """A loot container. block: minecraft:chest (default facing south), trapped_chest or
        minecraft:barrel (default facing up)."""
        block = _ns(block)
        if block == "minecraft:barrel":
            st = state(block, facing=facing or "up", open=False)
        else:
            st = state(block, facing=facing or "south", type="single", waterlogged=False)
        self.set(x, y, z, st, {"id": block, "LootTable": f"{NS}:chests/{table}"})

    def spawner(self, x, y, z, entity):
        self.set(x, y, z, "minecraft:spawner", {
            "id": "minecraft:mob_spawner",
            "SpawnData": {"entity": {"id": entity}},
            "Delay": Short(20), "MinSpawnDelay": Short(200), "MaxSpawnDelay": Short(800),
            "SpawnCount": Short(2), "MaxNearbyEntities": Short(4),
            "RequiredPlayerRange": Short(16), "SpawnRange": Short(4),
        })

    def jigsaw(self, x, y, z, orientation, name, target, pool, final_state=AIR, joint="rollable",
               selection_priority=0, placement_priority=0):
        """A jigsaw connector. orientation: '<front>_<top>' (north_up, up_north, ...); a bare
        horizontal direction means '<dir>_up'. name/target/pool without a namespace get ours;
        'minecraft:empty' is the empty pool/name. See tools/structures/crypt.py."""
        if orientation in HORIZONTAL:
            orientation += "_up"
        elif orientation in ("up", "down"):
            orientation += "_north"
        q = lambda s: s if ":" in s else f"{NS}:{s}"  # noqa: E731
        self.set(x, y, z, f"minecraft:jigsaw[orientation={orientation}]", {
            "id": "minecraft:jigsaw", "name": q(name), "target": q(target), "pool": q(pool),
            "final_state": final_state, "joint": joint,
            "selection_priority": selection_priority, "placement_priority": placement_priority,
        })

    def jigsaws(self):
        """[(pos, orientation, nbt)] of the piece's jigsaw blocks."""
        out = []
        for pos, (b, nbt) in sorted(self.cells.items()):
            if block_name(b) == "minecraft:jigsaw":
                out.append((pos, parse_block(b)[1].get("orientation", "north_up"), nbt or {}))
        return out

    # ---- copies
    def _copy_shape(self, size, name=None):
        p = Piece(name or self.name, *size, seed="copy")
        p.rnd = self.rnd
        return p

    def rotated(self, turns=1):
        """A copy turned `turns` quarter turns clockwise seen from above (north -> east),
        with every facing / axis / orientation / shape / side property turned too."""
        turns %= 4
        p = self
        for _ in range(turns):
            w, h, d = p.size
            q = p._copy_shape((d, h, w))
            for (x, y, z), (b, nbt) in p.cells.items():
                q.cells[(d - 1 - z, y, x)] = (transform_state(b, cw, 1), nbt)
            q._waterlogged_markers = {(d - 1 - z, y, x) for x, y, z in p._waterlogged_markers}
            p = q
        if p is self:
            p = self._copy_shape(self.size)
            p.cells = dict(self.cells)
            p._waterlogged_markers = set(self._waterlogged_markers)
        return p

    def mirrored_x(self):
        """A copy flipped east-west (x -> w-1-x); states mirror too (left/right swap)."""
        w, h, d = self.size
        q = self._copy_shape(self.size)
        flip = lambda s: {"east": "west", "west": "east"}.get(s, s)  # noqa: E731
        for (x, y, z), (b, nbt) in self.cells.items():
            q.cells[(w - 1 - x, y, z)] = (transform_state(b, flip, 0, mirrored=True), nbt)
        q._waterlogged_markers = {(w - 1 - x, y, z) for x, y, z in self._waterlogged_markers}
        return q

    def paste(self, src, x, y, z, turns=0, mirror_x=False, skip_air=False):
        """Copy another Piece's set cells in with its (0, 0, 0) at (x, y, z), after mirroring
        and then turning it. Unset cells of src are skipped; skip_air also skips its air."""
        if mirror_x:
            src = src.mirrored_x()
        if turns % 4:
            src = src.rotated(turns)
        for (sx, sy, sz), (b, nbt) in sorted(src.cells.items()):
            if skip_air and b == AIR:
                continue
            self.set(x + sx, y + sy, z + sz, b, dict(nbt) if nbt else nbt)
            if (sx, sy, sz) in src._waterlogged_markers:
                self._waterlogged_markers.add((x + sx, y + sy, z + sz))

    # ---- checks and output
    def validate(self, schema, known_mod_blocks=None):
        """Problems (strings) with the piece's blocks against a block-state schema
        ({id: {prop: [values] | {"integer": [lo, hi]}}}). Our own blocks must be in
        known_mod_blocks (default: content/data/useful_armory/horizon/block/*.json)."""
        self.finalize()
        if known_mod_blocks is None:
            known_mod_blocks = mod_blocks()
        where, seen = {}, {}
        for pos, (b, nbt) in sorted(self.cells.items(), key=lambda c: (c[0][1], c[0][2], c[0][0])):
            if b not in seen:
                seen[b] = self._check_state(b, schema, known_mod_blocks)
            if seen[b]:
                where.setdefault(b, []).append(pos)
        problems = []
        for b, positions in where.items():
            more = f" (and {len(positions) - 1} more)" if len(positions) > 1 else ""
            problems.append(f"{self.name} at {positions[0]}{more}: {seen[b]}")
        return problems

    @staticmethod
    def _check_state(b, schema, known_mod_blocks):
        try:
            name, props = parse_block(b)
        except ValueError:
            return f"malformed block string {b!r}"
        if name.startswith(NS + ":"):
            if name not in known_mod_blocks:
                return f"unknown mod block {name}"
            return f"{name} has no properties, got {props}" if props else None
        if name not in schema:
            return f"unknown block {name}"
        allowed, errors = schema[name], []
        for k, v in props.items():
            if k not in allowed:
                errors.append(f"no property {k}")
                continue
            spec = allowed[k]
            if isinstance(spec, dict):
                lo, hi = spec["integer"]
                if not (v.lstrip("-").isdigit() and lo <= int(v) <= hi):
                    errors.append(f"{k}={v} not in {lo}..{hi}")
            elif v not in spec:
                errors.append(f"{k}={v} not one of {spec}")
        missing = sorted(set(allowed) - set(props))
        if missing:
            errors.append(f"missing properties {missing}")
        return f"{b}: {'; '.join(errors)}" if errors else None

    def stats(self):
        """Size, cell counts, loot containers by table, spawners by entity, jigsaws."""
        loot, spawners, jig = {}, {}, 0
        solid = 0
        for b, nbt in self.cells.values():
            if b != AIR:
                solid += 1
            if not nbt:
                continue
            if "LootTable" in nbt:
                key = f"{block_name(b).split(':')[1]}:{nbt['LootTable'].split('/', 1)[-1]}"
                loot[key] = loot.get(key, 0) + 1
            if nbt.get("id") == "minecraft:mob_spawner":
                e = nbt.get("SpawnData", {}).get("entity", {}).get("id", "?")
                spawners[e] = spawners.get(e, 0) + 1
            if nbt.get("id") == "minecraft:jigsaw":
                jig += 1
        return {"name": self.name, "size": list(self.size), "cells": len(self.cells),
                "blocks": solid, "loot": dict(sorted(loot.items())),
                "spawners": dict(sorted(spawners.items())), "jigsaws": jig}

    def to_nbt(self):
        self.finalize()
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
        return {"size": list(self.size), "palette": palette, "blocks": blocks,
                "entities": [], "DataVersion": DATA_VERSION}

    def save(self, path=None):
        """Write the .nbt (default content/data/useful_armory/structure/<name>.nbt);
        returns the number of cells written."""
        root = self.to_nbt()
        write_nbt(Path(path) if path else DATA / "structure" / f"{self.name}.nbt", root)
        return len(root["blocks"])

    @classmethod
    def load(cls, path, name=None):
        """A Piece from a structure .nbt (first palette)."""
        root = read_nbt(path)
        w, h, d = root["size"]
        p = cls(name or Path(path).stem, w, h, d, seed=name or str(path))
        palette = root.get("palette") or root.get("palettes", [[]])[0]
        strings = [state(e["Name"], **e.get("Properties", {})) if e.get("Properties") else e["Name"]
                   for e in palette]
        for blk in root["blocks"]:
            p.cells[tuple(blk["pos"])] = (strings[blk["state"]], blk.get("nbt"))
        return p


def load_schema(path):
    return json.loads(Path(path).read_text())


def match_any(name, patterns):
    return not patterns or any(fnmatch.fnmatch(name, pat) for pat in patterns)


# ------------------------------------------------------------------ self test
def _selftest():
    ok = 0

    def check(cond, what):
        nonlocal ok
        assert cond, what
        ok += 1

    p = Piece("t", 8, 6, 8, "t")
    p.set(0, 1, 0, "minecraft:stone")
    p.fence(1, 1, 0)
    p.set(2, 1, 0, "minecraft:stone")
    p.finalize()
    f = parse_block(p.get(1, 1, 0))[1]
    check(f == {"east": "true", "west": "true", "north": "false", "south": "false", "waterlogged": "false"},
          f"fence between two solids: {f}")
    # a fence next to a chest or a stair does not connect; two fences do
    p.fence(4, 1, 4), p.fence(5, 1, 4)
    p.set(3, 1, 4, "minecraft:chest[facing=north,type=single,waterlogged=false]")
    p.stairs(4, 1, 3, "oak", "north")
    p.finalize()
    f = parse_block(p.get(4, 1, 4))[1]
    check(f["east"] == "true" and f["west"] == "false" and f["north"] == "false", f"fence {f}")
    # nether brick fence does not join a wooden one
    p.set(6, 1, 4, "minecraft:nether_brick_fence")
    p.finalize()
    check(parse_block(p.get(6, 1, 4))[1]["west"] == "false", "nether vs oak fence")
    # walls: straight run with air above has no post; end posts and tall under a block
    q = Piece("w", 5, 3, 3, "w")
    for x in range(5):
        q.wall(x, 0, 1)
    q.set(2, 1, 1, AIR)
    q.set(3, 1, 1, "minecraft:stone")
    q.finalize()
    mid = parse_block(q.get(2, 0, 1))[1]
    check(mid["up"] == "false" and mid["east"] == "low" and mid["west"] == "low", f"wall mid {mid}")
    under = parse_block(q.get(3, 0, 1))[1]
    check(under["east"] == "tall" and under["west"] == "tall" and under["up"] == "true", f"wall under block {under}")
    end = parse_block(q.get(0, 0, 1))[1]
    check(end["up"] == "true" and end["west"] == "none" and end["east"] == "low", f"wall end {end}")
    # panes join bars and walls
    r = Piece("p", 3, 1, 1, "p")
    r.pane(0, 0, 0)
    r.bars(1, 0, 0)
    r.wall(2, 0, 0)
    r.finalize()
    check(parse_block(r.get(1, 0, 0))[1]["east"] == "true" and parse_block(r.get(1, 0, 0))[1]["west"] == "true", "bars")
    check(parse_block(r.get(2, 0, 0))[1]["west"] == "low", "wall to bars")
    # is_full_solid
    for b, want in (("minecraft:stone_bricks", True), ("minecraft:sea_lantern", True), ("minecraft:barrel[facing=up,open=false]", True),
                    ("minecraft:lantern[hanging=false,waterlogged=false]", False), ("minecraft:oak_stairs", False),
                    ("minecraft:oak_leaves", False), ("minecraft:grass_block", True), ("minecraft:red_bed", False),
                    ("minecraft:mushroom_stem", True), ("minecraft:red_mushroom_block", True), (None, False), (AIR, False)):
        check(is_full_solid(b) == want, f"is_full_solid({b})")
    # ids
    for m, k, want in (("stone_bricks", "stairs", "minecraft:stone_brick_stairs"), ("oak_planks", "fence", "minecraft:oak_fence"),
                       ("deepslate_tiles", "slab", "minecraft:deepslate_tile_slab"), ("minecraft:cobblestone", "wall", "minecraft:cobblestone_wall"),
                       ("nether_bricks", "fence", "minecraft:nether_brick_fence"), ("oak", "door", "minecraft:oak_door"),
                       ("minecraft:oak_stairs", "stairs", "minecraft:oak_stairs"), ("quartz_block", "stairs", "minecraft:quartz_stairs")):
        check(block_id(m, k) == want, f"block_id({m}, {k}) = {block_id(m, k)}")
    # helpers write full states
    s = Piece("s", 4, 4, 4, "s")
    s.stairs(0, 0, 0, "stone_bricks", "north")
    check(s.get(0, 0, 0) == "minecraft:stone_brick_stairs[facing=north,half=bottom,shape=straight,waterlogged=false]", s.get(0, 0, 0))
    s.door(1, 0, 1, "spruce", "south")
    check(parse_block(s.get(1, 1, 1))[1]["half"] == "upper", "door upper")
    s.bed(2, 0, 0, "red", "south")
    check(parse_block(s.get(2, 0, 1))[1]["part"] == "head", "bed head at foot+facing")
    # rotation: a stair facing north turns to face east; positions move with it
    t = Piece("r", 3, 1, 2, "r")
    t.stairs(0, 0, 0, "oak", "north", shape="outer_left")
    t.set(2, 0, 1, "minecraft:rail[shape=north_east,waterlogged=false]")
    t.jigsaw(1, 0, 0, "north", "a", "a", "minecraft:empty")
    rt = t.rotated(1)
    check(rt.size == (2, 1, 3), "rotated size")
    check(parse_block(rt.get(1, 0, 0))[1]["facing"] == "east", f"rotated stair {rt.cells}")
    check(parse_block(rt.get(0, 0, 2))[1]["shape"] == "south_east", "rotated rail")
    check(parse_block(rt.get(1, 0, 1))[1]["orientation"] == "east_up", "rotated jigsaw")
    check(t.rotated(4).cells == t.cells, "four turns is the identity")
    mt = t.mirrored_x()
    check(parse_block(mt.get(2, 0, 0))[1]["shape"] == "outer_right", "mirror swaps left/right")
    check(parse_block(mt.get(0, 0, 1))[1]["shape"] == "north_west", "mirrored rail")
    # roof: odd span gets a slab ridge on the ridge line
    g = Piece("g", 7, 6, 5, "g")
    top = g.gable_roof(1, 5, 1, 3, 1, "oak", "x", overhang=1, gable_fill="minecraft:oak_planks")
    check(top == 3 and block_name(g.get(3, 3, 2)) == "minecraft:oak_slab", f"gable ridge {top}")
    check(parse_block(g.get(3, 1, 0))[1]["facing"] == "south", "north eave rises south")
    check(g.get(1, 2, 2) == "minecraft:oak_planks", "gable fill")
    # hip roof: corners are outer stairs with the tall quarter toward the middle
    hp = Piece("h", 7, 5, 6, "h")
    hp.hip_roof(1, 5, 1, 4, 0, "oak", overhang=1)
    nw = parse_block(hp.get(0, 0, 0))[1]
    se = parse_block(hp.get(6, 0, 5))[1]
    check((nw["facing"], nw["shape"]) == ("south", "outer_left"), f"hip NW corner {nw}")
    check((se["facing"], se["shape"]) == ("north", "outer_left"), f"hip SE corner {se}")
    check(parse_block(hp.get(3, 0, 0))[1]["facing"] == "south" and parse_block(hp.get(0, 0, 3))[1]["facing"] == "east",
          "hip sides rise inward")
    # validate catches partial states, unknown blocks and bad values
    schema = {"minecraft:stone": {}, "minecraft:oak_stairs": {"facing": ["north"], "half": ["bottom"],
              "shape": ["straight"], "waterlogged": ["false"]}, "minecraft:candle": {"candles": {"integer": [1, 4]}}}
    v = Piece("v", 4, 1, 1, "v")
    v.set(0, 0, 0, "minecraft:stone")
    v.set(1, 0, 0, "minecraft:oak_stairs[facing=north]")
    v.set(2, 0, 0, "minecraft:candle[candles=5]")
    v.set(3, 0, 0, f"{NS}:nosuchblock")
    probs = v.validate(schema, known_mod_blocks=set())
    check(len(probs) == 3 and "missing" in probs[0] and "5" in probs[1] and "unknown mod block" in probs[2], probs)
    # save is deterministic and load round-trips
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        a = Path(tmp) / "a.nbt"
        s.chest(3, 0, 3, "crypt", "west")
        s.spawner(3, 1, 3, "minecraft:zombie")
        s.save(a)
        first = a.read_bytes()
        s.save(a)
        check(a.read_bytes() == first, "deterministic")
        back = Piece.load(a, "s")
        check(back.cells == s.cells, "load round-trip")
        st = back.stats()
        check(st["loot"] == {"chest:crypt": 1} and st["spawners"] == {"minecraft:zombie": 1}, st)
    print(f"structkit selftest: {ok} checks passed")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        _selftest()
    else:
        print(__doc__)
