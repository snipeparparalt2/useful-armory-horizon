"""Infested mine (underground, Y -20 to 40; common): an abandoned mine overrun by spiders.

One 46 x 15 x 46 piece on two levels (x east, z south):
  main gallery     x 19..26, z 2..30, six high, timber sets in poor repair, broken rails
  loading bay      east of the gallery's north half: platform, sidings, chute, crates (chest)
  lower drifts     A west (z 6..10, cave spider) and B east (z 17..21, cave spider)
  upper drifts     C west (floor y 9), reached by a stair ramp from the gallery; its far end
                   is an old stone-brick section full of infested bricks (silverfish), and a
                   ladder shaft drops from it to drift A.
                   D east (floor y 9), reached by a ladder from the gallery (cave spider,
                   a miner's barrel at its end)
  pool chamber     west of the gallery's south half: a sealed two-deep pool, a sunken chest
  the nest         a wide webbed dome at the south end: egg sacs, bones, two spider
                   spawners, the best chest
Air is carved as a set of cells and wrapped in a rock skin (26-neighbour dilation), so the
piece is a closed shell with irregular walls. Floors are three thick (y 0..2) so the pool is
sealed; the lowest rock is deepslate.
"""
import math

from structkit import AIR, NS, Piece, block_name, state

W, H, D = 46, 15, 46
LOW = 3                                # lower-level air starts here; y 0..2 is floor
UP = 10                                # upper-level air starts here; floor at y 9
WOOD = "oak"

ROCK = (("minecraft:stone", 12), ("minecraft:andesite", 2), ("minecraft:tuff", 2),
        ("minecraft:cobblestone", 1))
DEEP = (("minecraft:deepslate[axis=y]", 8), ("minecraft:cobbled_deepslate", 2), ("minecraft:tuff", 2))
FLOOR = (("minecraft:stone", 4), ("minecraft:gravel", 4), ("minecraft:cobblestone", 3),
         ("minecraft:coarse_dirt", 2), ("minecraft:tuff", 1))
PATCHES = (("minecraft:gravel", 14, 1), ("minecraft:cobblestone", 10, 1), ("minecraft:andesite", 8, 2),
           ("minecraft:tuff", 8, 1), ("minecraft:diorite", 4, 1), ("minecraft:mossy_cobblestone", 8, 1),
           ("minecraft:dirt", 4, 1))
# (stone ore, deepslate ore, pockets)
ORES = (("minecraft:coal_ore", "minecraft:deepslate_coal_ore", 16),
        ("minecraft:iron_ore", "minecraft:deepslate_iron_ore", 10),
        ("minecraft:copper_ore", "minecraft:deepslate_copper_ore", 7),
        (f"{NS}:aquiteore", f"{NS}:deepslate_aquite_ore", 6),
        (f"{NS}:colosifiteore", f"{NS}:deepslate_colosifite_ore", 6),
        (f"{NS}:shadowore", f"{NS}:deepslate_shadow_ore", 5))
ROCK_IDS = ({n for n, _ in ROCK} | {block_name(n) for n, _ in DEEP} | {n for n, _, _ in PATCHES}
            | {o for pair in ORES for o in pair[:2]})

GALLERY = (19, LOW, 2, 26, 8, 30)
BAY = (27, LOW, 10, 40, 7, 15)
DRIFT_A = (3, LOW, 6, 18, 6, 10)
DRIFT_B = (27, LOW, 17, 42, 6, 21)
DRIFT_C = (3, UP, 13, 12, 13, 17)
DRIFT_D = (28, UP, 5, 42, 13, 9)
POOL_ROOM = (8, LOW, 19, 18, 7, 27)
NEST = (23, 37, 15.5, 6.0, 10)         # centre x, centre z, radius x, radius z, height


# ------------------------------------------------------------------ rock helpers
def _inner(c):
    x, y, z = c
    return 2 <= x <= W - 3 and LOW <= y <= H - 2 and 2 <= z <= D - 3


def _carve(p, air, box, rough=0.0):
    """Add box to the air set; with rough > 0 the walls and roof get one-block bulges."""
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


def _touches(c, air):
    x, y, z = c
    return any(n in air for n in ((x + 1, y, z), (x - 1, y, z), (x, y, z + 1), (x, y, z - 1),
                                  (x, y + 1, z), (x, y - 1, z)))


def _skin(p, air):
    """Wrap the air in rock (deepslate low down), with blotches, ore pockets and a worn
    floor, then set the air."""
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
    rock, deep, floor = p.mix(*ROCK), p.mix(*DEEP), p.mix(*FLOOR)
    for x, y, z in shell:
        p.set(x, y, z, deep if y <= LOW - 1 + p.rnd.randint(-1, 1) else rock)
    for x, y, z in shell:
        if (x, y + 1, z) in air:
            p.set(x, y, z, floor)
            for below in (y - 1, y - 2):
                if below >= 0 and not p.is_set(x, below, z):
                    p.set(x, below, z, deep)
    faces = [c for c in shell if (c[0], c[1] + 1, c[2]) not in air and _touches(c, air)]
    in_shell = set(shell)
    for block, n, r in PATCHES:
        for _ in range(n):
            cx, cy, cz = p.rnd.choice(faces)
            for c in Piece.box_cells((cx - r, cy - r, cz - r, cx + r, cy + r, cz + r)):
                if c in in_shell and abs(c[0] - cx) + abs(c[1] - cy) + abs(c[2] - cz) <= r:
                    p.set(*c, block)
    for stone_ore, deep_ore, n in ORES:
        for _ in range(n):
            c = p.rnd.choice(faces)
            near = [c] + [m for m in _around(c) if m in in_shell and _touches(m, air)]
            for m in near[:1] + p.rnd.sample(near[1:], min(len(near) - 1, p.rnd.randint(0, 3))):
                host = block_name(p.get(*m))
                p.set(*m, deep_ore if "deepslate" in host else stone_ore)
    for c in sorted(air):
        p.set(*c, AIR)


def _around(c):
    x, y, z = c
    return [(x + 1, y, z), (x - 1, y, z), (x, y + 1, z), (x, y - 1, z), (x, y, z + 1), (x, y, z - 1)]


# ------------------------------------------------------------------ timber and props
def _timber_set(p, along, at, lo, hi, floor, top, missing=()):
    """Timber set across a tunnel (posts at lo and hi from floor to top - 1, cap log at
    top, knee braces). along 'z': the tunnel runs north-south. `missing` leaves parts out:
    'lo', 'hi' (posts), 'braces', 'cap' (the cap is then a stub over the standing post)."""
    pos = (lambda u, y: (u, y, at)) if along == "z" else (lambda u, y: (at, y, u))  # noqa: E731
    toward_lo, toward_hi = ("west", "east") if along == "z" else ("north", "south")
    cap_axis = "x" if along == "z" else "z"
    for side, u in (("lo", lo), ("hi", hi)):
        if side not in missing:
            for y in range(floor, top):
                p.log(*pos(u, y), WOOD)
    span = range(lo, hi + 1)
    if "cap" in missing:
        span = range(lo, lo + 3) if "lo" not in missing else range(hi - 2, hi + 1)
    for u in span:
        p.log(*pos(u, top), WOOD, axis=cap_axis)
    if "braces" not in missing:
        if "lo" not in missing:
            p.stairs(*pos(lo + 1, top - 1), WOOD, toward_lo, half="top")
        if "hi" not in missing and "cap" not in missing:
            p.stairs(*pos(hi - 1, top - 1), WOOD, toward_hi, half="top")


def _decay(p, rnd):
    """Missing parts for a set in poor repair."""
    pick = rnd.random()
    if pick < 0.25:
        return ("hi", "cap", "braces") if rnd.random() < 0.5 else ("lo", "cap", "braces")
    if pick < 0.5:
        return ("braces",)
    return ()


def _rail(p, x, y, z, shape):
    p.set(x, y, z, state("minecraft:rail", shape=shape, waterlogged=False))


def _debris(p, floors, chance=0.15):
    """Pebbles, fallen slabs and gravel lumps at the foot of the rock walls on each floor."""
    for y in floors:
        for x in range(W):
            for z in range(D):
                if p.get(x, y, z) != AIR or p.get(x, y - 1, z) in (None, AIR):
                    continue
                by_rock = any(block_name(p.get(x + dx, y, z + dz) or AIR) in ROCK_IDS
                              for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)))
                if not by_rock or p.rnd.random() >= chance:
                    continue
                pick = p.rnd.randrange(4)
                if pick == 0:
                    p.set(x, y, z, state("minecraft:stone_button", face="floor", facing="north", powered=False))
                elif pick == 1:
                    p.slab(x, y, z, p.rnd.choice(("cobblestone", "andesite", "cobbled_deepslate")))
                elif pick == 2:
                    p.set(x, y, z, "minecraft:gravel")
                else:
                    p.stairs(x, y, z, "cobblestone", p.rnd.choice(("north", "east", "south", "west")))


def _crate(p, x, y, z):
    p.barrel(x, y, z, facing=p.rnd.choice(("north", "east", "south", "west", "up")))


def _egg_sac(p, x, y, z, big=False):
    """A spider egg sac: white wool (and a bone block for a big one) wrapped in web."""
    p.set(x, y, z, "minecraft:white_wool")
    if big:
        p.set(x, y + 1, z, "minecraft:white_wool")
        p.set(x + 1, y, z, state("minecraft:bone_block", axis="y"))
    for c in _around((x, y, z)) + _around((x, y + 1, z)) * big:
        if p.get(*c) == AIR:
            p.set(*c, "minecraft:cobweb")


def _webs(p, box, chance, high_bias=True):
    """Cobwebs in empty cells of box, thicker toward the roof."""
    x0, y0, z0, x1, y1, z1 = box
    for x, y, z in Piece.box_cells(box):
        if p.get(x, y, z) != AIR:
            continue
        k = chance * (0.4 + 1.2 * (y - y0) / max(1, y1 - y0)) if high_bias else chance
        if p.rnd.random() < k:
            p.set(x, y, z, "minecraft:cobweb")


def _lichen(p, x, y, z, side):
    """Glow lichen on one face of an air cell (side = the solid block's direction)."""
    faces = {d: d == side for d in ("north", "east", "south", "west", "up", "down")}
    p.set(x, y, z, state("minecraft:glow_lichen", waterlogged=False, **faces))


# ------------------------------------------------------------------ carving
def _carve_all(p):
    air = set()
    _carve(p, air, GALLERY, rough=0.3)
    _carve(p, air, BAY, rough=0.25)
    for box in (DRIFT_A, DRIFT_B, DRIFT_D):
        _carve(p, air, box, rough=0.3)
    _carve(p, air, DRIFT_C, rough=0.15)
    _carve(p, air, POOL_ROOM, rough=0.35)
    for i, x in enumerate(range(18, 12, -1)):               # the stair ramp up to drift C
        _carve(p, air, (x, LOW + i, 14, x, LOW + i + 4, 16))
    _carve(p, air, (4, LOW, 11, 4, 13, 11))                 # ladder shaft A <-> C
    _carve(p, air, (4, UP, 12, 4, 12, 12))
    _carve(p, air, (27, LOW, 7, 27, 12, 7))                 # ladder shaft gallery -> D
    cx, cz, rx, rz, h = NEST
    for x in range(W):
        for z in range(D):
            for y in range(LOW, LOW + h):
                r = ((x - cx) / rx) ** 2 + ((z - cz) / rz) ** 2 + ((y - LOW) / h) ** 2
                wobble = 0.12 * math.sin(x * 1.3 + z * 0.7) + 0.1 * math.cos(z * 1.7 - y)
                if r <= 1 + wobble and _inner((x, y, z)):
                    air.add((x, y, z))
    _carve(p, air, (20, LOW, 30, 25, 7, 33))                # the gallery runs into the nest
    return air


# ------------------------------------------------------------------ areas
def _gallery(p):
    """Main gallery: eight timber sets in poor repair, the broken track down the middle,
    a fallen cap, a few sparse lanterns, webs."""
    x0, _, z0, x1, top, z1 = GALLERY
    for i, z in enumerate(range(4, 30, 4)):
        missing = _decay(p, p.rnd) if i not in (0, 2) else ()
        _timber_set(p, "z", z, x0, x1, LOW, top, missing)
    for z in range(z0 + 1, 30):
        if z % 7 in (3, 4) or z in (17, 18):
            continue                                       # pulled or buried rails
        _rail(p, 22, LOW, z, "north_south")
    _rail(p, 23, LOW, 17, "east_west")                      # knocked askew
    for x in range(21, 25):                                 # a fallen cap across the track
        p.log(x, LOW, 18, WOOD, axis="x")
    p.set(20, LOW, 18, "minecraft:gravel")
    p.set(25, LOW, 19, "minecraft:gravel")
    p.hanging_lantern(22, top - 1, 8, chain=0)
    p.hanging_lantern(23, top - 1, 24, chain=0)
    # the stair ramp up to drift C, its foot in the gallery's west wall
    for i, x in enumerate(range(18, 12, -1)):
        for z in (14, 15, 16):
            p.stairs(x, LOW + i, z, "cobblestone" if (x + z) % 3 else "mossy_cobblestone", "west")
    # the ladder up to drift D
    p.ladder_column(27, 7, LOW, UP - 1, "west")
    _webs(p, (x0, LOW, z0, x1, top, z1), 0.05)


def _loading_bay(p):
    """Loading bay: two sidings off the gallery track ending at buffers, a raised plank
    platform, the chute from above, stacked crates and the bay chest."""
    x0, _, z0, x1, top, z1 = BAY
    _rail(p, 22, LOW, 12, "north_east")
    for x in range(23, 38):
        if x not in (28, 33):
            _rail(p, x, LOW, 12, "east_west")
    for x in range(26, 36):
        if x != 30:
            _rail(p, x, LOW, 14, "east_west")
    for z in (12, 14):                                      # buffers
        p.log(x1 - 1, LOW, z, WOOD, axis="x")
    for x in range(30, 39):                                 # platform along the north side
        p.set(x, LOW, 10, "minecraft:oak_planks")
        p.slab(x, LOW, 11, WOOD)
    for x in (30, 34, 38):
        p.fence(x, LOW + 1, 10, WOOD)
    p.chest(36, LOW + 1, 10, "infested_mine", "south")
    for x, y, z in ((37, LOW + 1, 10), (38, LOW + 1, 10), (32, LOW + 1, 10), (x1, LOW, 13), (x1, LOW, 14),
                    (x1, LOW + 1, 14), (x1, LOW, 15)):
        _crate(p, x, y, z)
    for y in range(LOW + 2, top + 1):                       # ore chute down from the roof
        p.trapdoor(34, y, 13, WOOD, "south", open=True)
    for x, z in ((33, 13), (34, 13), (35, 13), (34, 12)):
        if p.get(x, LOW, z) == AIR or block_name(p.get(x, LOW, z)) == "minecraft:rail":
            p.set(x, LOW, z, p.rnd.choice(("minecraft:gravel", "minecraft:coal_ore", "minecraft:iron_ore")))
    for x in (31, 37):                                      # timber posts holding the roof
        for z in (z0, z1):
            for y in range(LOW + (z == z0), top):
                p.log(x, y, z, WOOD)
        for z in range(z0, z1 + 1):
            p.log(x, top, z, WOOD, axis="z")
    p.hanging_lantern(34, top - 1, 15, chain=0)
    _webs(p, BAY, 0.07)


def _drift_a(p):
    """Lower west drift: sets every four blocks, the old track, a cave spider spawner in a
    web-choked stretch, egg sacs in the dead end."""
    x0, _, z0, x1, top, z1 = DRIFT_A
    for x in range(x1 - 1, x0, -4):
        _timber_set(p, "x", x, z0, z1, LOW, top, _decay(p, p.rnd))
    for x in range(x0 + 2, x1 + 1):
        if p.rnd.random() < 0.75:
            _rail(p, x, LOW, 8, "east_west")
    p.spawner(9, LOW, 8, "minecraft:cave_spider")
    _egg_sac(p, x0, LOW, z0 + 1)
    _egg_sac(p, x0 + 1, top - 1, z1)
    _webs(p, DRIFT_A, 0.16)


def _drift_b(p):
    """Lower east drift: collapsing sets, a cave spider spawner, a rubble slide at the end."""
    x0, _, z0, x1, top, z1 = DRIFT_B
    for x in range(x0 + 1, x1, 4):
        _timber_set(p, "x", x, z0, z1, LOW, top, _decay(p, p.rnd))
    for x in range(x0, x1 - 3):
        if p.rnd.random() < 0.7:
            _rail(p, x, LOW, 19, "east_west")
    p.spawner(35, LOW, 19, "minecraft:cave_spider")
    for z in range(z0, z1 + 1):                             # rubble slide at the end
        for y in range(LOW, top + 1):
            for x in range(x1 - 1, x1 + 1):
                if p.get(x, y, z) == AIR and y - LOW <= (x - (x1 - 2)) * 2:
                    p.set(x, y, z, p.rnd.choice(("minecraft:gravel", "minecraft:cobblestone", "minecraft:stone")))
        p.stairs(x1 - 2, LOW, z, "cobblestone", "east")
    _egg_sac(p, 39, LOW, z0, big=True)
    _webs(p, DRIFT_B, 0.16)


def _drift_c(p):
    """Upper west drift: the head of the ramp, then an old stone-brick lined section
    riddled with infested bricks (silverfish spawner) and the ladder down to drift A."""
    x0, _, z0, x1, top, z1 = DRIFT_C
    _timber_set(p, "x", 12, z0, z1, UP, top)
    bricks = p.mix(("minecraft:stone_bricks", 3), ("minecraft:cracked_stone_bricks", 2),
                   ("minecraft:mossy_stone_bricks", 2), ("minecraft:infested_stone_bricks", 3),
                   ("minecraft:infested_cracked_stone_bricks", 2), ("minecraft:infested_mossy_stone_bricks", 2))
    for x in range(x0 - 1, 11):                             # line the section with bricks
        for y in range(UP - 1, top + 2):
            for z in range(z0 - 1, z1 + 2):
                b = p.get(x, y, z)
                if b not in (None, AIR) and block_name(b) in ROCK_IDS:
                    p.set(x, y, z, bricks)
    for x in (10, 6):                                       # brick arches over the section
        for z in (z0, z1):
            for y in range(UP, top):
                p.set(x, y, z, "minecraft:stone_bricks")
        p.stairs(x, top - 1, z0 + 1, "stone_bricks", "north", half="top")
        p.stairs(x, top - 1, z1 - 1, "stone_bricks", "south", half="top")
        for z in range(z0 + 2, z1 - 1):
            p.set(x, top, z, "minecraft:chiseled_stone_bricks")
    p.spawner(8, UP, 15, "minecraft:silverfish")
    for x, z in ((7, 14), (9, 16)):
        p.slab(x, UP, z, "stone_bricks")
    p.ladder_column(4, 11, LOW, UP, "east")
    p.set(5, UP, 12, "minecraft:cobweb")
    _webs(p, DRIFT_C, 0.1)


def _drift_d(p):
    """Upper east drift: off the gallery ladder, sagging sets, a cave spider spawner, the
    dead miner's barrel at the end behind webs."""
    x0, _, z0, x1, top, z1 = DRIFT_D
    for x in range(x0 + 2, x1, 4):
        _timber_set(p, "x", x, z0, z1, UP, top, _decay(p, p.rnd))
    p.spawner(36, UP, 7, "minecraft:cave_spider")
    p.chest(x1, UP, 7, "infested_mine", facing="west", block="minecraft:barrel")
    p.skull(x1 - 1, UP, 8, rotation=4)
    p.set(x1 - 1, UP, 6, state("minecraft:bone_block", axis="z"))
    _egg_sac(p, 32, UP, z1)
    p.set(x1 - 2, UP, 7, "minecraft:cobweb")
    p.set(x1 - 2, UP + 1, 7, "minecraft:cobweb")
    _webs(p, DRIFT_D, 0.18)


def _pool(p):
    """Pool chamber: a two-deep pool sunk into the floor (rock all round and under it),
    glow lichen and aquite ore at the edges for light, a sunken chest on the bottom."""
    x0, _, z0, x1, top, z1 = POOL_ROOM
    cells = [(x, z) for x in range(10, 17) for z in range(22, 27)
             if not ((x in (10, 16)) and (z in (22, 26)))]
    for x, z in cells:
        for y in (LOW - 2, LOW - 1):
            p.set(x, y, z, "minecraft:water[level=0]")
    for x, z in cells:                                      # check it is sealed
        assert p.get(x, LOW - 3, z) not in (None, AIR, "minecraft:water[level=0]")
        for nx, nz in ((x + 1, z), (x - 1, z), (x, z + 1), (x, z - 1)):
            if (nx, nz) not in cells:
                for y in (LOW - 2, LOW - 1):
                    assert p.get(nx, y, nz) not in (None, AIR), (nx, y, nz)
    p.chest(13, LOW - 2, 24, "infested_mine", "north")
    nbt = p.get_nbt(13, LOW - 2, 24)
    p.set(13, LOW - 2, 24, state("minecraft:chest", facing="north", type="single", waterlogged=True), nbt)
    for x, z in ((x0, 21), (x0, 25), (x1 - 1, z1)):
        p.set(x - 1 if x == x0 else x, LOW - 1, z, f"{NS}:aquiteore")
    for x, y, z, side in ((x0, 5, 23, "west"), (x0, 6, 24, "west"), (x0, 4, 26, "west"),
                          (11, top, 21, "up"), (14, top, 25, "up")):
        if p.get(x, y, z) == AIR:
            _lichen(p, x, y, z, side)
    for x, z in ((17, 21), (17, 27), (9, 27)):              # dripstone over the water's edge
        if p.get(x, top + 1, z) not in (None, AIR):
            p.set(x, top, z, state("minecraft:pointed_dripstone", thickness="tip", vertical_direction="down",
                                   waterlogged=False))
    p.set(x0, LOW, z1, "minecraft:mossy_cobblestone")
    p.slab(x0 + 1, LOW, z1, "mossy_cobblestone")
    _webs(p, POOL_ROOM, 0.04)


def _nest(p):
    """The nest: a webbed dome with egg-sac clusters on the floor and walls, bone piles,
    two spider spawners, and the best chest walled in by webs on a rock shelf."""
    cx, cz, rx, rz, h = NEST
    box = (int(cx - rx) - 1, LOW, int(cz - rz) - 1, int(cx + rx) + 1, LOW + h, int(cz + rz) + 1)
    for x, z in ((14, 33), (31, 36), (22, 39), (17, 37), (28, 31), (11, 36), (34, 33)):
        if p.get(x, LOW, z) == AIR:
            _egg_sac(p, x, LOW, z, big=(x + z) % 2 == 0)
    for x, z in ((20, 33), (26, 37), (16, 31), (30, 39)):   # bone piles
        if p.get(x, LOW, z) == AIR:
            p.set(x, LOW, z, state("minecraft:bone_block", axis=p.rnd.choice("xyz")))
            if p.get(x + 1, LOW, z) == AIR:
                p.skull(x + 1, LOW, z, rotation=p.rnd.randrange(16))
    for x, z, h in ((12, 37, 9), (34, 38, 9), (27, 41, 7)):  # rock pillars left standing
        for y in range(LOW, LOW + h):
            if p.get(x, y, z) == AIR:
                p.set(x, y, z, p.rnd.choice(("minecraft:stone", "minecraft:tuff", "minecraft:cobblestone")))
    for x, z in ((15, 40), (16, 40), (31, 33), (32, 33), (32, 34), (20, 42), (9, 36)):  # mounds
        if p.get(x, LOW, z) == AIR:
            p.set(x, LOW, z, p.rnd.choice(("minecraft:gravel", "minecraft:dirt", "minecraft:cobblestone")))
    p.spawner(18, LOW, 35, "minecraft:spider")
    p.spawner(29, LOW, 34, "minecraft:spider")
    # the chest on a raised rock shelf at the back of the nest
    for x in range(21, 26):
        for z in (40, 41):
            if p.get(x, LOW, z) == AIR:
                p.set(x, LOW, z, "minecraft:cobblestone" if x % 2 else "minecraft:mossy_cobblestone")
    p.chest(23, LOW + 1, 40, "infested_mine", "north")
    for x in (22, 24):
        p.skull(x, LOW + 1, 40, rotation=8)
    for c in ((23, LOW + 2, 40), (22, LOW + 1, 39), (23, LOW + 1, 39), (24, LOW + 1, 39)):
        if p.get(*c) == AIR:
            p.set(*c, "minecraft:cobweb")
    for x, y, z, side in ((23, LOW + 7, 34, "up"), (15, LOW + 4, 34, "up"), (31, LOW + 4, 35, "up")):
        if p.get(x, y, z) == AIR and p.get(x, y + 1, z) not in (None, AIR):
            _lichen(p, x, y, z, side)
    _webs(p, box, 0.22)


def build():
    p = Piece("infested_mine", W, H, D, "infested_mine")
    _skin(p, _carve_all(p))
    _gallery(p)
    _loading_bay(p)
    _drift_a(p)
    _drift_b(p)
    _drift_c(p)
    _drift_d(p)
    _pool(p)
    _nest(p)
    _debris(p, (LOW, UP))
    return p


PLACE = {
    "name": "infested_mine",
    "pieces": {"infested_mine": build},
    "step": "underground_structures",
    "start_height": (-20, 40),
    "surface": False,
    "terrain": "none",
    "biomes": ["#minecraft:is_overworld"],
    "spacing": 16,
    "separation": 6,
    "salt": 418200110,
}
