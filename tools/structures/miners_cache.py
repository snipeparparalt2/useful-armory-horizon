"""Miner's cache: a worked-out mine junction (underground, Y 0 to 40). A quiet find, no spawner.

One 39 x 12 x 39 piece. A timbered hub (13 x 13) with a hoist over a covered shaft and a
ladder shaft stub going up; four 5-wide tunnels leave it:
  north  -> the tool room (workbench, furnaces, anvil, ore sorting, two loot barrels)
  east   -> the sleeping nook (two bunks, cold campfire, wash cauldron)
  west   -> the worked-out face, dense with ore, where the rails end
  south  -> collapsed into rubble; behind it a sealed cache with a barrel and a trapped miner
The rock is carved as a set of air cells and wrapped in a 1-block rock skin (26-neighbour
dilation), so the walls follow the irregular tunnel line and the piece is enclosed whether
it is buried or cut by a cave. Floors are two blocks thick so the puddles stay sealed.
"""
from structkit import AIR, NS, Piece, block_name, state

W, H, D = 39, 12, 39
LOW = 2                                # lowest air layer; y 0..1 is the floor

ROCK = (("minecraft:stone", 12), ("minecraft:andesite", 2), ("minecraft:cobblestone", 1),
        ("minecraft:tuff", 1))
FLOOR = (("minecraft:stone", 4), ("minecraft:gravel", 3), ("minecraft:cobblestone", 3),
         ("minecraft:coarse_dirt", 2), ("minecraft:andesite", 1))
# (block, how many patches, radius): blotches that break up the rock faces
PATCHES = (("minecraft:gravel", 9, 1), ("minecraft:cobblestone", 8, 1), ("minecraft:andesite", 6, 2),
           ("minecraft:diorite", 3, 1), ("minecraft:granite", 3, 1), ("minecraft:tuff", 4, 1),
           ("minecraft:mossy_cobblestone", 4, 1))
# (block, how many pockets): small ore clusters on the visible rock
ORES = (("minecraft:coal_ore", 12), ("minecraft:iron_ore", 7), ("minecraft:copper_ore", 5),
        (f"{NS}:aquiteore", 4), (f"{NS}:colosifiteore", 4), (f"{NS}:shadowore", 3))
WOOD = "spruce"
ROCK_IDS = {n for n, _ in ROCK} | {n for n, _, _ in PATCHES} | {n for n, _ in ORES}


# ------------------------------------------------------------------ rock helpers
def _carve(p, air, box, rough=0.0):
    """Add box to the air set. With rough > 0 the side walls and ceiling get one-block
    bulges at that chance, so the rock line is not a flat plane."""
    x0, y0, z0, x1, y1, z1 = box
    air.update(Piece.box_cells(box))
    if not rough:
        return
    for x, y, z in Piece.box_cells(box):
        out = []
        if y > y0:
            out += [(x - 1, y, z)] * (x == x0) + [(x + 1, y, z)] * (x == x1)
            out += [(x, y, z - 1)] * (z == z0) + [(x, y, z + 1)] * (z == z1)
        if y == y1:
            out.append((x, y + 1, z))
        for c in out:
            if _inner(c) and p.rnd.random() < rough:
                air.add(c)


def _inner(c):
    """A cell that may be air: leaves room for the rock skin inside the piece."""
    x, y, z = c
    return 2 <= x <= W - 3 and LOW <= y <= H - 2 and 2 <= z <= D - 3


def _skin(p, air):
    """Wrap the air in rock: every non-air cell touching air (26 neighbours) becomes rock,
    with patches and ore pockets on the faces and a worn floor; then set the air."""
    shell = set()
    for x, y, z in air:
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    c = (x + dx, y + dy, z + dz)
                    if c not in air:
                        assert p.in_bounds(*c), c
                        shell.add(c)
    shell = sorted(shell)
    rock = p.mix(*ROCK)
    for c in shell:
        p.set(*c, rock)
    floor = p.mix(*FLOOR)
    for x, y, z in shell:
        if (x, y + 1, z) in air:
            p.set(x, y, z, floor)
            p.set(x, y - 1, z, rock)                     # second floor layer
    faces = [c for c in shell if (c[0], c[1] + 1, c[2]) not in air and _touches(c, air)]
    in_shell = set(shell)
    for block, n, r in PATCHES:
        for _ in range(n):
            cx, cy, cz = p.rnd.choice(faces)
            for c in Piece.box_cells((cx - r, cy - r, cz - r, cx + r, cy + r, cz + r)):
                if c in in_shell and abs(c[0] - cx) + abs(c[1] - cy) + abs(c[2] - cz) <= r:
                    p.set(*c, block)
    for block, n in ORES:
        for _ in range(n):
            _ore_pocket(p, p.rnd.choice(faces), block, in_shell, air)
    for c in sorted(air):
        p.set(*c, AIR)


def _touches(c, air):
    x, y, z = c
    return any(n in air for n in ((x + 1, y, z), (x - 1, y, z), (x, y, z + 1), (x, y, z - 1),
                                  (x, y + 1, z), (x, y - 1, z)))


def _ore_pocket(p, c, block, in_shell, air):
    """An ore cluster of 1 to 4 cells on the rock face around c."""
    x, y, z = c
    p.set(x, y, z, block)
    near = [n for n in ((x + 1, y, z), (x - 1, y, z), (x, y + 1, z), (x, y - 1, z), (x, y, z + 1),
                        (x, y, z - 1)) if n in in_shell and _touches(n, air)]
    for n in p.rnd.sample(near, min(len(near), p.rnd.randint(0, 3))):
        p.set(*n, block)


# ------------------------------------------------------------------ timber helpers
def _timber_set(p, along, at, lo, hi, top, missing=()):
    """A timber set across a tunnel: posts at lo and hi from the floor to top - 1, a cap log
    at top, knee braces (upside-down stairs) under the cap. along 'z': the tunnel runs
    north-south and the set spans x lo..hi at z = at; 'x' the other way. `missing` names
    parts left out of a set in poor repair: 'lo', 'hi', 'braces'."""
    pos = (lambda u, y: (u, y, at)) if along == "z" else (lambda u, y: (at, y, u))  # noqa: E731
    toward_lo, toward_hi = ("west", "east") if along == "z" else ("north", "south")
    for side, u in (("lo", lo), ("hi", hi)):
        if side not in missing:
            for y in range(LOW, top):
                p.log(*pos(u, y), WOOD)
    for u in range(lo, hi + 1):
        p.log(*pos(u, top), WOOD, axis="x" if along == "z" else "z")
    if "braces" not in missing:
        p.stairs(*pos(lo + 1, top - 1), WOOD, toward_lo, half="top")
        p.stairs(*pos(hi - 1, top - 1), WOOD, toward_hi, half="top")


def _rail(p, x, z, shape):
    p.set(x, LOW, z, state("minecraft:rail", shape=shape, waterlogged=False))


def _puddle(p, cells):
    """Water sunk into the floor: one deep, with solid floor under and around it."""
    for x, z in cells:
        p.set(x, LOW - 1, z, "minecraft:water[level=0]")
        assert p.get(x, LOW - 2, z) not in (None, AIR)


def _debris(p, chance=0.18):
    """Pebbles, slabs of fallen rock and gravel lumps along the foot of the rock walls."""
    for x, z in sorted({(x, z) for x in range(W) for z in range(D)}):
        if p.get(x, LOW, z) != AIR or p.get(x, LOW - 1, z) in (None, AIR):
            continue
        by_rock = any(block_name(p.get(x + dx, LOW, z + dz) or AIR) in ROCK_IDS
                      for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        if by_rock and p.rnd.random() < chance:
            pick = p.rnd.randrange(4)
            if pick == 0:
                p.set(x, LOW, z, state("minecraft:stone_button", face="floor", facing="north", powered=False))
            elif pick == 1:
                p.slab(x, LOW, z, p.rnd.choice(("cobblestone", "andesite", "stone")))
            elif pick == 2:
                p.set(x, LOW, z, "minecraft:gravel")
            else:
                p.stairs(x, LOW, z, "cobblestone", p.rnd.choice(("north", "east", "south", "west")))


def _dripstone(p, cells):
    """Short dripstone points hanging from the rock roof (the roof above must be rock)."""
    for x, y, z in cells:
        if p.get(x, y + 1, z) not in (None, AIR) and p.get(x, y, z) == AIR:
            p.set(x, y, z, state("minecraft:pointed_dripstone", thickness="tip", vertical_direction="down",
                                 waterlogged=False))


def _crate(p, x, y, z):
    """A decorative barrel lying on its side."""
    p.barrel(x, y, z, facing=p.rnd.choice(("north", "east", "south", "west")))


def _table(p, x, z, top="spruce"):
    p.fence(x, LOW, z, WOOD)
    p.set(x, LOW + 1, z, state(f"minecraft:{top}_pressure_plate", powered=False))


# ------------------------------------------------------------------ carving plan
HUB = (13, LOW, 13, 25, 7, 25)
TOOL_ROOM = (12, LOW, 2, 26, 6, 7)
NOOK = (30, LOW, 14, 36, 5, 24)
CACHE = (15, LOW, 33, 23, 4, 36)
TUNNELS = {
    "north": (17, LOW, 8, 21, 5, 12),
    "south": (17, LOW, 26, 21, 5, 32),
    "west": (3, LOW, 17, 12, 5, 21),
    "east": (26, LOW, 17, 29, 5, 21),
}


def _carve_all(p):
    air = set()
    _carve(p, air, HUB, rough=0.25)
    _carve(p, air, (14, 8, 13, 14, 10, 13))               # ladder shaft stub going up
    _carve(p, air, TOOL_ROOM, rough=0.2)
    _carve(p, air, NOOK, rough=0.3)
    _carve(p, air, CACHE, rough=0.3)
    for box in TUNNELS.values():
        _carve(p, air, box, rough=0.3)
    return air


# ------------------------------------------------------------------ areas
def _hub(p):
    """Timbered junction: posts round the walls, a ring beam and cross beams with broken
    plank lagging, the hoist over a covered shaft, the ladder stub, a rest corner."""
    x0, _, z0, x1, top, z1 = HUB
    posts = [(x0, z0), (x1, z0), (x0, z1), (x1, z1)]
    posts += [(x, z) for x in (16, 22) for z in (z0, z1)] + [(x, z) for x in (x0, x1) for z in (16, 22)]
    for x, z in posts:
        for y in range(LOW, top):
            p.log(x, y, z, WOOD)
    for x in range(x0, x1 + 1):                           # ring beam north and south, cross beams
        for z in (z0, z1, 16, 22):
            p.log(x, top, z, WOOD, axis="x")
    for z in range(z0 + 1, z1):
        if z not in (16, 22):
            for x in (x0, x1):
                p.log(x, top, z, WOOD, axis="z")
    for x in range(x0 + 1, x1):                           # lagging between the beams, half gone
        for z in range(z0 + 1, z1):
            if z not in (16, 22) and p.get(x, top, z) == AIR and p.rnd.random() < 0.45:
                p.slab(x, top, z, WOOD, type="top")
    _hoist(p)
    p.ladder_column(14, 13, LOW, 9, "south")              # shaft stub, choked with gravel
    p.set(14, 10, 13, "minecraft:gravel")
    p.trapdoor(14, 7, 13, WOOD, "south", half="top", open=True)
    # rest corner (south-west): table, benches, a lantern, crates and an ore pile
    _table(p, 15, 23)
    p.lantern(15, LOW + 1, 23)
    p.stairs(14, LOW, 23, WOOD, "west")
    p.stairs(15, LOW, 24, WOOD, "south")
    for x, y, z in ((14, LOW, 15), (14, LOW, 14), (15, LOW, 14), (14, LOW + 1, 14)):
        _crate(p, x, y, z)
    for x, z in ((23, 23), (24, 23), (24, 24), (23, 24), (22, 24)):
        p.set(x, LOW, z, p.rnd.choice(("minecraft:coal_ore", "minecraft:gravel", "minecraft:iron_ore",
                                       "minecraft:cobblestone")))
    p.set(24, LOW + 1, 24, "minecraft:coal_ore")
    p.slab(23, LOW + 1, 24, "cobblestone")
    p.hanging_lantern(19, top - 1, 22, chain=0)
    _puddle(p, ((14, 21), (14, 20)))
    p.set(x1, top - 1, z1 - 1, "minecraft:cobweb")
    p.set(x0 + 1, top - 1, z1, "minecraft:cobweb")


def _hoist(p):
    """Hoist frame in the north-east of the hub: two posts and a winch beam over a hatch,
    the chain run down to the bucket (a cauldron), a grindstone for the crank."""
    for x in (22, 25):
        for y in range(LOW, 6):
            p.log(x, y, 15, WOOD)
    for x in range(22, 26):
        p.log(x, 6, 15, WOOD, axis="x", stripped=True)
    for x in (23, 24):
        for z in (14, 15, 16):
            p.trapdoor(x, LOW, z, WOOD, "north")
    p.trapdoor(24, LOW, 16, WOOD, "south", open=True)
    p.set(23, LOW, 15, "minecraft:cauldron")
    for y in (3, 4, 5):
        p.chain(23, y, 15)
    p.set(22, 4, 16, state("minecraft:grindstone", face="wall", facing="south"))


def _rails(p):
    """The track: from the west face, through the hub, turning south into the collapse.
    Gaps where rails were pulled, one twisted loose."""
    for x in range(5, 19):
        if x not in (8, 14):
            _rail(p, x, 19, "east_west")
    _rail(p, 19, 19, "south_west")
    for z in range(20, 29):
        if z != 24:
            _rail(p, 19, z, "north_south")
    _rail(p, 11, 19, "north_east")                         # twisted
    p.set(8, LOW, 18, state("minecraft:rail", shape="north_south", waterlogged=False))  # pulled aside
    p.log(4, LOW, 19, WOOD, axis="z")                       # buffer beam at the end of the line


def _west_face(p):
    """The worked-out face: three timber sets, ore thick in the last few blocks, a puddle,
    a lantern, a pick rack and spoil."""
    for x in (12, 9, 6):
        _timber_set(p, "x", x, 17, 21, 5, missing=("braces",) if x == 6 else ())
    for z in range(16, 23):                                # ore-rich face
        for y in range(LOW, 6):
            if p.get(2, y, z) not in (None, AIR) and p.rnd.random() < 0.45:
                p.set(2, y, z, p.rnd.choice(("minecraft:coal_ore", "minecraft:iron_ore", f"{NS}:colosifiteore",
                                             f"{NS}:aquiteore", "minecraft:copper_ore")))
    p.hanging_lantern(9, 4, 19, chain=0)
    _puddle(p, ((8, 21), (9, 21), (9, 20)))
    for x, z in ((4, 17), (5, 17), (4, 21)):               # spoil heap
        p.set(x, LOW, z, "minecraft:gravel")
    p.slab(4, LOW + 1, 17, "cobblestone")
    p.stairs(3, LOW, 18, "cobblestone", "west")
    p.fence(4, LOW, 20, WOOD)                               # pick rack: post with a hook
    p.set(4, LOW + 1, 20, state("minecraft:tripwire_hook", attached=False, facing="east", powered=False))
    p.set(3, 4, 21, "minecraft:cobweb")


def _north_tunnel(p):
    for z in (12, 9):
        _timber_set(p, "z", z, 17, 21, 5)
    p.set(17, 4, 10, "minecraft:cobweb")


def _tool_room(p):
    """Tool room: workbench wall, furnaces, anvil, sorting barrels with ore, the stores
    (two loot barrels among plain ones), a coal pile; timber posts and caps."""
    x0, _, z0, x1, top, z1 = TOOL_ROOM
    for x in (14, 19, 24):
        for z in (z0, z1):
            for y in range(LOW, top):
                p.log(x, y, z, WOOD)
        for z in range(z0, z1 + 1):
            p.log(x, top, z, WOOD, axis="z")
    # west end: smelting
    p.set(x0, LOW, 3, state("minecraft:furnace", facing="east", lit=False))
    p.set(x0, LOW, 4, state("minecraft:furnace", facing="east", lit=False))
    p.set(x0, LOW + 1, 3, "minecraft:cobblestone")
    p.slab(x0, LOW + 1, 4, "cobblestone")
    p.set(x0, LOW, 5, "minecraft:crafting_table")
    for x, z in ((x0, 6), (x0 + 1, 6)):
        p.set(x, LOW, z, p.rnd.choice(("minecraft:coal_block", "minecraft:coal_ore")))
    p.set(x0, LOW + 1, 6, "minecraft:coal_ore")
    # north wall: workbench of slabs on barrels, tools on it
    for x in range(15, 19):
        p.barrel(x, LOW, z0, facing="south")
        p.slab(x, LOW + 1, z0, WOOD)
    p.set(16, LOW + 1, z0, state("minecraft:chipped_anvil", facing="east"))
    p.candle(17, LOW + 2, z0, candles=2)
    p.set(18, LOW + 2, z0, state("minecraft:grindstone", face="floor", facing="east"))
    for x in range(15, 19):                               # tool boards on the wall above
        p.trapdoor(x, 4, z0, WOOD, "south", open=True)
    # sorting: barrels with ore and a stonecutter by the east posts
    for x, z in ((21, z0), (22, z0)):
        p.barrel(x, LOW, z, facing="up", open=True)
    p.set(23, LOW, z0, state("minecraft:stonecutter", facing="south"))
    for x, z in ((21, 4), (22, 4)):
        p.set(x, LOW, z, p.rnd.choice(("minecraft:iron_ore", f"{NS}:colosifiteore", "minecraft:copper_ore")))
    # stores in the east end: crates stacked, two with loot
    p.chest(x1, LOW, 3, "miners_cache", facing="west", block="minecraft:barrel")
    p.chest(x1 - 1, LOW, z0, "miners_cache", facing="south", block="minecraft:barrel")
    for x, y, z in ((x1, LOW, z0), (x1, LOW + 1, z0), (x1, LOW + 1, 3), (x1, LOW, 4), (x1 - 1, LOW + 1, z0),
                    (x1, LOW, 5)):
        _crate(p, x, y, z)
    # table and bench in the middle
    _table(p, 20, 5)
    p.stairs(20, LOW, 6, WOOD, "south")
    p.hanging_lantern(19, top - 1, 4, chain=0)
    p.set(x0 + 1, top - 1, z0, "minecraft:cobweb")
    p.set(x1, top - 1, z1, "minecraft:cobweb")


def _east_tunnel(p):
    for x in (26, 29):
        _timber_set(p, "x", x, 17, 21, 5, missing=("lo",) if x == 29 else ())
    p.log(27, LOW, 17, WOOD, axis="x")                      # the fallen post


def _nook(p):
    """Sleeping nook: two bunks with a barrel between, cold campfire ringed with stone,
    wash cauldron, rug, a lantern on a table; corner posts and a cap."""
    x0, _, z0, x1, top, z1 = NOOK
    for x, z in ((x0, z0), (x1, z0), (x0, z1), (x1, z1)):
        for y in range(LOW, top):
            p.log(x, y, z, WOOD)
    for x in range(x0, x1 + 1):
        for z in (z0, z1):
            p.log(x, top, z, WOOD, axis="x")
    p.bed(x1, LOW, 16, "brown", "north")
    p.bed(x1, LOW, 19, "brown", "south")
    p.barrel(x1, LOW, 18, facing="up")
    p.candle(x1, LOW + 1, 18, candles=1, lit=False)
    for x in range(33, 36):
        for z in range(16, 20):
            p.carpet(x, LOW, z, "brown" if (x + z) % 2 else "gray")
    p.set(33, LOW, 22, state("minecraft:campfire", facing="north", lit=False, signal_fire=False, waterlogged=False))
    for x, z in ((32, 22), (34, 22), (33, 21), (33, 23)):
        p.slab(x, LOW, z, "cobblestone")
    p.stairs(31, LOW, 22, WOOD, "west")                    # seat by the fire
    p.set(x1, LOW, 23, state("minecraft:water_cauldron", level=2))
    _table(p, 31, 15)
    p.lantern(31, LOW + 1, 15)
    p.stairs(32, LOW, 15, WOOD, "east")
    _crate(p, x1, LOW, z0 + 1)
    _crate(p, x1 - 1, LOW, z0)
    p.set(x0, top - 1, z1 - 1, "minecraft:cobweb")
    p.set(x1, top - 1, z1 - 1, "minecraft:cobweb")


def _south_collapse(p):
    """The south tunnel caved in: a broken set, a slope of rubble filling it to the roof."""
    _timber_set(p, "z", 26, 17, 21, 5)
    _timber_set(p, "z", 29, 17, 21, 5, missing=("hi", "braces"))
    rubble = p.mix(("minecraft:gravel", 5), ("minecraft:cobblestone", 3), ("minecraft:stone", 2),
                   ("minecraft:coarse_dirt", 2), ("minecraft:andesite", 1))
    for z in range(29, 33):
        for x in range(16, 23):
            for y in range(LOW, 7):
                if p.get(x, y, z) == AIR:
                    p.set(x, y, z, rubble)
    for x in range(17, 22):                               # the spill slope in front
        p.stairs(x, LOW, 28, "cobblestone", "south")
        if p.rnd.random() < 0.6:
            p.slab(x, LOW, 27, p.rnd.choice(("cobblestone", "stone")))
    p.set(18, LOW + 1, 28, "minecraft:gravel")
    p.log(20, LOW + 1, 28, WOOD, axis="z")                 # the cap log, fallen
    p.set(19, 4, 28, "minecraft:cobweb")


def _cache(p):
    """Behind the collapse: the miner who was cut off, his barrel and supplies, a dead candle."""
    x0, _, z0, x1, top, z1 = CACHE
    for x in (x0, x1):
        for y in range(LOW, top):
            p.log(x, y, z1, WOOD)
    for x in range(x0, x1 + 1):
        p.log(x, top, z1, WOOD, axis="x")
    p.chest(19, LOW, z1, "miners_cache", facing="north", block="minecraft:barrel")
    for x, y, z in ((20, LOW, z1), (18, LOW, z1), (20, LOW + 1, z1)):
        _crate(p, x, y, z)
    p.skull(17, LOW, 34, rotation=6)
    p.set(16, LOW, 34, state("minecraft:bone_block", axis="x"))
    p.candle(21, LOW, 34, candles=3, lit=False)
    p.set(22, LOW, 35, state("minecraft:rail", shape="east_west", waterlogged=False))
    p.set(x0 + 1, top, z0, "minecraft:cobweb")


def build():
    p = Piece("miners_cache", W, H, D, "miners_cache")
    _skin(p, _carve_all(p))
    _hub(p)
    _rails(p)
    _west_face(p)
    _north_tunnel(p)
    _tool_room(p)
    _east_tunnel(p)
    _nook(p)
    _south_collapse(p)
    _cache(p)
    _debris(p)
    _dripstone(p, ((7, 5, 18), (10, 5, 21), (5, 5, 20), (31, 5, 20), (20, 6, 3)))
    return p


PLACE = {
    "name": "miners_cache",
    "pieces": {"miners_cache": build},
    "step": "underground_structures",
    "start_height": (0, 40),
    "surface": False,
    "terrain": "none",
    "biomes": [
        "#minecraft:is_overworld",
    ],
    "spacing": 18,
    "separation": 6,
    "salt": 418200107,
}
