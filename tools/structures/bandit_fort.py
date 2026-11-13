"""Bandit fort: a log palisade fort (surface; plains, forests, taiga, savanna; common).
Brief: docs/design/places.md section 10.

Layout (x east, z south; the gate is in the middle of the south wall):
  * palisade x PX0..PX1, z PZ0..PZ1 with chamfered corners: spruce logs four high with
    fence stakes on top, a plank walkway behind it at y 3 on log posts, ladders up from the
    yard. Two log towers flank the gate, joined over it by a fighting bridge.
  * north-west: the longhouse (log frame, plank infill, cobble footing, dark oak gabled
    roof): bunks at the west end, a long table in the middle, the kitchen at the east end.
  * north-east: the leader's tent (red and black cloth) on a raised plank platform, and a
    lookout tower on log stilts in the corner.
  * the yard: a central fire with log benches, an iron-bar cage, the stolen-goods pile
    (south-west), training dummies and a target line (south-east), a woodpile, a water butt,
    skulls on stakes outside the gate.
Spawners: pillager just inside the gate, pillager by the fire, pillager at the training
ground, vindicator in the longhouse. Loot (chests/bandit_fort): longhouse, tent, goods pile.
"""
from structkit import AIR, Piece, state

W, H, D = 41, 18, 41
PX0, PX1, PZ0, PZ1 = 3, 37, 3, 36      # palisade line
CUT = 3                                 # corner chamfer
GATE = (19, 20, 21)                     # gate opening in the south wall
TW = (14, 18)                           # west gate tower x range (east tower mirrored)
TE = (22, 26)
TZ = (34, 38)                           # gate towers z range
LH = (6, 19, 7, 14)                     # longhouse outer walls x0, x1, z0, z1
TP = (23, 30, 7, 14)                    # tent platform
LK = (32, 35, 6, 9)                     # lookout stilts
FX, FZ = 20, 22                         # the fire

GRASS = "minecraft:grass_block[snowy=false]"
SIDES = ("north", "east", "south", "west")
STEP = {"north": (0, -1), "south": (0, 1), "east": (1, 0), "west": (-1, 0)}
TABLE = "bandit_fort"


# ------------------------------------------------------------------ small helpers
def _pick(p, *weighted):
    names, weights = zip(*weighted)
    return p.rnd.choices(names, weights)[0]


def _inside(x, z):
    """Inside the palisade line (chamfered rectangle), the line itself included."""
    if not (PX0 <= x <= PX1 and PZ0 <= z <= PZ1):
        return False
    return min(x - PX0, PX1 - x) + min(z - PZ0, PZ1 - z) >= CUT


def _on_line(x, z):
    return _inside(x, z) and any(not _inside(x + a, z + b) for a, b in STEP.values())


def _trodden(p):
    return _pick(p, ("minecraft:coarse_dirt", 5), ("minecraft:dirt", 2), ("minecraft:dirt_path", 1),
                 ("minecraft:packed_mud", 1), (GRASS, 2), ("minecraft:podzol[snowy=false]", 1))


def _log(p):
    return _pick(p, ("minecraft:spruce_log[axis=y]", 8), ("minecraft:dark_oak_log[axis=y]", 2),
                 ("minecraft:stripped_spruce_log[axis=y]", 1))


def _cobweb(p, x, y, z):
    if p.get(x, y, z) == AIR:
        p.set(x, y, z, "minecraft:cobweb")


def _path(p, a, b, wide=1):
    (x0, z0), (x1, z1) = a, b
    n = max(abs(x1 - x0), abs(z1 - z0))
    for i in range(n + 1):
        x = round(x0 + (x1 - x0) * i / n)
        z = round(z0 + (z1 - z0) * i / n)
        for d in range(wide):
            xx, zz = (x + d, z) if abs(z1 - z0) >= abs(x1 - x0) else (x, z + d)
            if p.is_set(xx, 0, zz):
                p.set(xx, 0, zz, "minecraft:dirt_path" if p.rnd.random() < 0.8 else "minecraft:coarse_dirt")


# ------------------------------------------------------------------ the site
def _site(p):
    cx, cz = (W - 1) / 2, (D - 1) / 2
    for x in range(W):
        for z in range(D):
            r = abs((x - cx) / (W / 2)) ** 4 + abs((z - cz) / (D / 2)) ** 4
            if r > 0.95 + p.rnd.uniform(-0.07, 0.07):
                continue
            p.set(x, 0, z, _trodden(p) if _inside(x, z) else
                  _pick(p, (GRASS, 12), ("minecraft:coarse_dirt", 2), ("minecraft:dirt", 1)))
            for y in range(1, H):
                p.set(x, y, z, AIR)


def _paths(p):
    _path(p, (FX - 1, D - 1), (FX - 1, FZ + 3), wide=3)         # the road in through the gate
    _path(p, (FX - 2, FZ - 2), (12, LH[3] + 1))                  # to the longhouse door
    _path(p, (FX + 2, FZ - 2), (26, TP[3] + 2), wide=2)          # to the leader's platform
    _path(p, (FX - 3, FZ + 1), (12, 26))                         # to the goods pile
    _path(p, (FX + 3, FZ + 2), (28, 26))                         # to the training ground


# ------------------------------------------------------------------ palisade and walkway
def _palisade(p):
    for x in range(PX0, PX1 + 1):
        for z in range(PZ0, PZ1 + 1):
            if not _on_line(x, z):
                continue
            p.set(x, 0, z, "minecraft:coarse_dirt")
            for y in range(1, 5):
                p.set(x, y, z, _log(p))
            p.fence(x, 5, z, "spruce")                            # stakes, some taller
            if (x + z) % 2 == 0 and p.rnd.random() < 0.7:
                p.fence(x, 6, z, "spruce")
    # raking props against the outside every few logs
    for x in range(PX0, PX1 + 1):
        for z in range(PZ0, PZ1 + 1):
            if not _on_line(x, z) or (x * 7 + z * 3) % 6 or (z == PZ1 and TW[0] - 1 <= x <= TE[1] + 1):
                continue
            out = [s for s, (a, b) in STEP.items() if not _inside(x + a, z + b)]
            if len(out) != 1:
                continue
            a, b = STEP[out[0]]
            if p.is_set(x + a, 0, z + b):
                back = {"north": "south", "south": "north", "east": "west", "west": "east"}[out[0]]
                p.set(x + a, 1, z + b, "minecraft:stripped_spruce_log[axis=y]")
                p.stairs(x + a, 2, z + b, "spruce", back)
    # a patched breach on the west side and a leaning stretch of stakes
    for z in (18, 19):
        p.set(PX0, 4, z, AIR)
        p.set(PX0, 5, z, AIR)
        p.set(PX0, 6, z, AIR)
        p.set(PX0, 3, z, "minecraft:spruce_planks")
    p.set(PX0 - 1, 1, 18, "minecraft:spruce_log[axis=z]")


def _walkway(p):
    """Planks at y 3 behind the wall, on log posts with stair braces; ladders up from the yard."""
    walk = []
    for x in range(PX0 + 1, PX1):
        for z in range(PZ0 + 1, PZ1):
            if not _inside(x, z) or _on_line(x, z):
                continue
            if any(_on_line(x + a, z + b) for a in (-1, 0, 1) for b in (-1, 0, 1)):
                walk.append((x, z))
    for i, (x, z) in enumerate(sorted(walk)):
        if TW[0] <= x <= TE[1] and z >= TZ[0]:
            continue                                              # gate towers and gate
        p.set(x, 3, z, _pick(p, ("minecraft:spruce_planks", 6), ("minecraft:dark_oak_planks", 1)))
        if (x + z) % 5 == 0:
            p.set(x, 1, z, "minecraft:stripped_spruce_log[axis=y]")
            p.set(x, 2, z, "minecraft:stripped_spruce_log[axis=y]")
        else:
            inward = [s for s, (a, b) in STEP.items() if _inside(x + a, z + b) and not
                      any(_on_line(x + a + c, z + b + d) for c in (-1, 0, 1) for d in (-1, 0, 1))]
            if len(inward) == 1 and (x + z) % 5 in (1, 4):
                p.stairs(x, 2, z, "spruce", {"north": "south", "south": "north", "east": "west",
                                             "west": "east"}[inward[0]], half="top")
    # ladders up from the yard, each against a post under the walkway
    for x, z, facing, post in ((PX0 + 2, 26, "east", (PX0 + 1, 26)), (10, PZ0 + 2, "south", (10, PZ0 + 1)),
                               (PX1 - 2, 24, "west", (PX1 - 1, 24)), (31, PZ1 - 2, "north", (31, PZ1 - 1))):
        px, pz = post
        p.set(px, 1, pz, "minecraft:stripped_spruce_log[axis=y]")
        p.set(px, 2, pz, "minecraft:stripped_spruce_log[axis=y]")
        p.ladder_column(x, z, 1, 3, facing)
    # torches along the walkway
    for x, z, facing in ((PX0 + 1, 12, "east"), (PX1 - 1, 15, "west"), (25, PZ0 + 1, "south"),
                         (PX0 + 1, 30, "east")):
        p.wall_torch(x, 4, z, facing) if p.get(x, 4, z) == AIR else None


# ------------------------------------------------------------------ gate and towers
def _tower(p, x0, x1, side_door):
    """A 5x5 log tower: plank walls, a mid floor level with the walkway, a top platform with
    rails under a hipped roof, one ladder inside."""
    z0, z1 = TZ
    lx, lz = (x0 + x1) // 2, z1 - 1
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            edge = x in (x0, x1) or z in (z0, z1)
            corner = x in (x0, x1) and z in (z0, z1)
            p.set(x, 0, z, "minecraft:cobblestone" if edge else "minecraft:coarse_dirt")
            for y in range(1, 11):
                if corner:
                    p.set(x, y, z, "minecraft:spruce_log[axis=y]" if y <= 10 else AIR)
                elif edge and y <= 6:
                    if y == 1:
                        b = "minecraft:cobblestone"
                    elif y in (3, 6):
                        b = "minecraft:stripped_spruce_log[axis=x]" if z in (z0, z1) else "minecraft:stripped_spruce_log[axis=z]"
                    else:
                        b = _pick(p, ("minecraft:spruce_planks", 5), ("minecraft:dark_oak_planks", 1))
                    p.set(x, y, z, b)
                else:
                    p.set(x, y, z, AIR)
            if not edge:
                p.set(x, 3, z, "minecraft:spruce_planks")         # mid floor
    for x in range(x0 - 1, x1 + 2):                               # top platform, one wider
        for z in range(z0 - 1, z1 + 2):
            if p.in_bounds(x, 7, z):
                p.set(x, 7, z, "minecraft:spruce_planks" if x0 <= x <= x1 and z0 <= z <= z1
                      else state("minecraft:spruce_slab", type="top", waterlogged=False))
    for x in range(x0 - 1, x1 + 2):                               # stair braces under the overhang
        for z in range(z0 - 1, z1 + 2):
            if not (x0 <= x <= x1 and z0 <= z <= z1):
                if (x in (x0 - 1, x1 + 1)) != (z in (z0 - 1, z1 + 1)):
                    inward = "east" if x == x0 - 1 else "west" if x == x1 + 1 else "south" if z == z0 - 1 else "north"
                    p.stairs(x, 6, z, "spruce", inward, half="top")
    for x in range(x0, x1 + 1):                                   # rails
        for z in range(z0, z1 + 1):
            if (x in (x0, x1) or z in (z0, z1)) and not (x in (x0, x1) and z in (z0, z1)):
                p.fence(x, 8, z, "spruce")
    p.hip_roof(x0, x1, z0, z1, 11, "dark_oak", overhang=1, ridge_slab="minecraft:spruce_planks")
    p.fence(lx, 14, (z0 + z1) // 2, "spruce")                     # flag pole
    p.set(lx, 15, (z0 + z1) // 2, "minecraft:black_banner[rotation=4]")
    # ladder from the ground to the platform, holes in the floors
    p.ladder_column(lx, lz, 1, 7, "north")
    p.ladder(lx, 3, lz, "north")
    p.ladder(lx, 7, lz, "north")
    # ground door toward the yard; walkway door on the outer side; arrow loops
    p.set(lx, 1, z0, AIR)
    p.set(lx, 2, z0, AIR)
    p.door(lx, 1, z0, "spruce", "south", hinge="left", open=True)
    sx = x0 if side_door == "west" else x1
    for y in (4, 5):
        p.set(sx, y, PZ1 - 1, AIR)
    for x in (x0 + 1, x1 - 1):
        p.set(x, 5, z1, AIR)
        p.trapdoor(x, 5, z1 + 1, "spruce", "south", open=True) if p.rnd.random() < 0.5 else None
    p.lantern(lx + 1, 2, z0 + 1, hanging=True)
    p.barrel(x0 + 1, 4, z0 + 1, facing="up")
    p.barrel(x1 - 1, 1, z1 - 1, facing="up")


def _gate(p):
    for x in GATE:
        for y in range(1, 5):
            p.set(x, y, PZ1, AIR)
        p.set(x, 0, PZ1, "minecraft:cobblestone")
        p.set(x, 5, PZ1, "minecraft:spruce_log[axis=x]")
        p.set(x, 6, PZ1, "minecraft:stripped_spruce_log[axis=x]")
        p.stairs(x, 6, PZ1 - 1, "spruce", "south", half="top")
        p.stairs(x, 6, PZ1 + 1, "spruce", "north", half="top")
        for z in (PZ1 - 1, PZ1, PZ1 + 1):
            p.set(x, 7, z, "minecraft:spruce_planks")
        p.fence(x, 8, PZ1 - 1, "spruce")
        p.fence(x, 8, PZ1 + 1, "spruce")
        for z in (PZ1 - 1, PZ1 + 1):
            if p.get(x, 1, z) not in (None, AIR):
                p.set(x, 1, z, AIR)
    # gate leaves standing open, a lantern under the lintel
    p.fence_gate(GATE[0], 1, PZ1, "spruce", "south", open=True)
    p.fence_gate(GATE[-1], 1, PZ1, "spruce", "south", open=True)
    p.lantern(GATE[1], 4, PZ1, hanging=True)
    # skulls on stakes outside the gate, a warning
    for x in (GATE[0] - 3, GATE[-1] + 3):
        z = PZ1 + 3
        if p.is_set(x, 0, z):
            p.fence(x, 1, z, "spruce")
            p.fence(x, 2, z, "spruce")
            p.skull(x, 3, z, rotation=0)


# ------------------------------------------------------------------ the longhouse
def _longhouse(p):
    x0, x1, z0, z1 = LH
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            edge = x in (x0, x1) or z in (z0, z1)
            if edge:
                p.set(x, 0, z, "minecraft:cobblestone")
            else:
                border = x in (x0 + 1, x1 - 1) or z in (z0 + 1, z1 - 1)
                p.set(x, 0, z, "minecraft:dark_oak_planks" if border else
                      _pick(p, ("minecraft:spruce_planks", 6), ("minecraft:stripped_spruce_wood[axis=x]", 1)))
            for y in range(1, 5):
                if not edge:
                    p.set(x, y, z, AIR)
                    continue
                post = (x in (x0, x1) and z in (z0, z1)) or (z in (z0, z1) and (x - x0) % 4 == 0) or \
                       (x in (x0, x1) and z == (z0 + z1) // 2 + 1)
                if y == 1:
                    b = _pick(p, ("minecraft:cobblestone", 3), ("minecraft:mossy_cobblestone", 1))
                elif post:
                    b = "minecraft:spruce_log[axis=y]"
                elif y == 4:
                    b = "minecraft:stripped_spruce_log[axis=x]" if z in (z0, z1) else "minecraft:stripped_spruce_log[axis=z]"
                else:
                    b = _pick(p, ("minecraft:spruce_planks", 6), ("minecraft:stripped_spruce_log[axis=y]", 1))
                p.set(x, y, z, b)
    p.gable_roof(x0, x1, z0, z1, 5, "dark_oak", "x", overhang=1, gable_fill="minecraft:spruce_planks")
    for x in range(x0 - 1, x1 + 2):                                # weathered shingles
        for z in range(z0 - 1, z1 + 2):
            for y in range(5, 10):
                b = p.get(x, y, z)
                if b and b.startswith("minecraft:dark_oak_stairs") and p.rnd.random() < 0.18:
                    p.set(x, y, z, b.replace("dark_oak_stairs", "spruce_stairs"))
    for x in (x0, x1):                                              # gable trim and smoke hole
        p.set(x, 5, (z0 + z1) // 2, "minecraft:stripped_spruce_log[axis=y]")
        p.set(x, 6, (z0 + z1) // 2 + 1, "minecraft:stripped_spruce_log[axis=y]")
    for x in (x0 + 4, x0 + 8, x1 - 1):                              # tie beams
        for z in range(z0 + 1, z1):
            p.set(x, 5, z, "minecraft:stripped_spruce_log[axis=z]")
    # doors: the main door south toward the fire, a back door east toward the tent
    door_x = 12
    p.door(door_x, 1, z1, "spruce", "north", hinge="right")
    p.wall_torch(door_x + 1, 3, z1 + 1, "south")
    p.door(x1, 1, z0 + 2, "spruce", "west", hinge="left")
    p.set(x1 + 1, 0, z0 + 2, "minecraft:dirt_path")
    # shuttered windows
    for x, z, out in ((8, z0, "north"), (15, z0, "north"), (9, z1, "south"), (16, z1, "south"),
                      (x0, z0 + 3, "west")):
        p.set(x, 2, z, AIR)
        p.set(x, 3, z, AIR)
        dx, dz = STEP[out]
        ox, oz = x + dx, z + dz
        if out in ("north", "south"):
            p.trapdoor(ox - 1, 3, oz, "spruce", out, open=True) if p.get(ox - 1, 3, oz) in (None, AIR) else None
            p.trapdoor(ox + 1, 3, oz, "spruce", out, open=True) if p.get(ox + 1, 3, oz) in (None, AIR) else None
        else:
            p.trapdoor(ox, 3, oz - 1, "spruce", out, open=True)
        p.fence(x, 2, z, "spruce") if out == "west" else None
    # west end: bunks
    for x in (x0 + 1, x0 + 3):
        p.bed(x, 1, z0 + 2, "brown", "north")
        p.bed(x, 1, z1 - 2, "red" if x == x0 + 1 else "brown", "south")
    p.barrel(x0 + 2, 1, z0 + 1, facing="up")
    p.candle(x0 + 2, 2, z0 + 1, candles=2, lit=False)
    p.barrel(x0 + 2, 1, z1 - 1, facing="north")
    p.chest(x0 + 1, 1, (z0 + z1) // 2, TABLE, "east")              # the longhouse chest
    p.barrel(x0 + 1, 1, (z0 + z1) // 2 + 1, facing="east")
    p.set(x0 + 1, 2, (z0 + z1) // 2 + 1, "minecraft:white_carpet")
    for z in range(z0 + 3, z1 - 2):
        p.carpet(x0 + 3, 1, z, "brown")
    # the hall: long table with benches
    for x in range(13, 17):
        p.fence(x, 1, 11, "spruce")
        p.set(x, 2, 11, "minecraft:spruce_pressure_plate[powered=false]" if x % 2 else
              state("minecraft:spruce_slab", type="bottom", waterlogged=False))
        p.stairs(x, 1, 10, "spruce", "north")
        p.stairs(x, 1, 12, "spruce", "south")
    p.stairs(12, 1, 11, "spruce", "west")
    p.set(15, 2, 11, "minecraft:candle[candles=3,lit=true,waterlogged=false]")
    p.spawner(11, 1, 10, "minecraft:vindicator")
    # the kitchen at the east end
    p.set(x1 - 1, 1, z1 - 1, "minecraft:smoker[facing=west,lit=true]")
    p.set(x1 - 1, 1, z1 - 2, "minecraft:furnace[facing=west,lit=false]")
    p.set(x1 - 1, 1, z1 - 3, "minecraft:water_cauldron[level=2]")
    p.set(x1 - 2, 1, z1 - 1, "minecraft:barrel[facing=up,open=false]")
    p.set(x1 - 2, 2, z1 - 1, "minecraft:decorated_pot[cracked=false,facing=north,waterlogged=false]")
    p.set(x1 - 1, 2, z1 - 1, "minecraft:spruce_trapdoor[facing=west,half=bottom,open=false,powered=false,waterlogged=false]")
    p.set(x1 - 1, 1, z0 + 1, "minecraft:crafting_table")
    p.set(x1 - 2, 1, z0 + 1, "minecraft:hay_block[axis=x]")
    p.set(x1 - 1, 3, z1 - 2, "minecraft:spruce_shelf[facing=west,powered=false,side_chain=unconnected,waterlogged=false]")
    # light and dust
    p.lantern(x0 + 4, 4, (z0 + z1) // 2, hanging=True)
    p.lantern(x0 + 8, 4, 10, hanging=True)
    p.lantern(x1 - 1, 4, 11, hanging=True)
    for x, z in ((x0 + 1, z0 + 1), (x1 - 1, z0 + 1), (x0 + 1, z1 - 1)):
        _cobweb(p, x, 4, z)


# ------------------------------------------------------------------ the leader's tent
def _leader(p):
    x0, x1, z0, z1 = TP
    for x in range(x0, x1 + 1):                                   # the raised platform
        for z in range(z0, z1 + 1):
            edge = x in (x0, x1) or z in (z0, z1)
            p.set(x, 0, z, "minecraft:coarse_dirt")
            p.set(x, 1, z, ("minecraft:stripped_dark_oak_log[axis=x]" if z in (z0, z1) else
                            "minecraft:stripped_dark_oak_log[axis=z]") if edge else
                  _pick(p, ("minecraft:spruce_planks", 5), ("minecraft:dark_oak_planks", 1)))
    for x in (x0, x1):
        for z in (z0, z1):
            p.set(x, 1, z, "minecraft:dark_oak_log[axis=y]")
            p.fence(x, 2, z, "dark_oak")
            p.set(x, 3, z, "minecraft:lantern[hanging=false,waterlogged=false]") if z == z1 else None
    for x in (26, 27):                                            # steps up from the yard
        p.stairs(x, 1, z1 + 1, "dark_oak", "north")
    # the tent: red and black cloth, upright sides then stepping to a ridge, ridge along z
    tx0, tx1, tz0, tz1 = x0 + 1, x1 - 1, z0 + 1, z1 - 2          # x 24..29, z 8..12
    prof = {tx0: (2, 3), tx1: (2, 3), tx0 + 1: (4, 4), tx1 - 1: (4, 4), tx0 + 2: (5, 5), tx1 - 2: (5, 5)}
    for z in range(tz0, tz1 + 1):
        cloth = "minecraft:red_wool" if z % 2 else "minecraft:black_wool"
        for x, (ya, yb) in prof.items():
            for y in range(ya, yb + 1):
                p.set(x, y, z, cloth)
        if z == tz0:                                              # closed back
            for x in range(tx0 + 1, tx1):
                for y in range(2, prof[x][0]):
                    p.set(x, y, z, "minecraft:black_wool")
        if z == tz1:                                              # front, flaps tied back
            for x in (tx0 + 1, tx1 - 1):
                p.set(x, 2, z, "minecraft:red_wool")
                p.set(x, 3, z, "minecraft:red_wool")
    for z in range(tz0 - 1, tz1 + 2):
        p.set((tx0 + tx1) // 2, 6, z, "minecraft:stripped_spruce_log[axis=z]")   # ridge pole
    for y in range(2, 6):                                         # back pole to the ground
        p.fence((tx0 + tx1) // 2, y, tz0 - 1, "spruce")
    for y in (4, 5):                                              # front pole lashed short,
        p.fence((tx0 + tx1) // 2, y, tz1 + 1, "spruce")           # so the doorway stays clear
    p.fence((tx0 + tx1) // 2, 7, tz1 + 1, "spruce")
    p.set((tx0 + tx1) // 2, 8, tz1 + 1, "minecraft:red_banner[rotation=0]")
    # inside: bed, the leader's chest, a table with a candle, a rug
    for x in range(tx0 + 1, tx1):
        for z in range(tz0 + 1, tz1 + 1):
            p.carpet(x, 2, z, "red" if (x + z) % 2 else "black")
    p.bed(tx0 + 1, 2, tz0 + 2, "red", "north")
    p.chest(tx1 - 1, 2, tz0 + 1, TABLE, "west")
    p.barrel(tx1 - 1, 2, tz0 + 2, facing="west")
    p.set(tx1 - 1, 3, tz0 + 2, "minecraft:candle[candles=2,lit=true,waterlogged=false]")
    p.set(tx0 + 2, 2, tz0 + 1, "minecraft:cartography_table")
    p.lantern(tx0 + 2, 4, tz0 + 3, hanging=True)
    # out front: a throne of stairs, a weapon rack and a brazier
    p.stairs(x0 + 1, 2, z1 - 1, "dark_oak", "west")
    p.fence(x1 - 1, 2, z1 - 1, "spruce")
    p.set(x1 - 1, 3, z1 - 1, state("minecraft:lightning_rod", facing="up", powered=False, waterlogged=False))
    p.set(x1 - 2, 2, z1 - 1, "minecraft:grindstone[face=floor,facing=east]")


def _lookout(p):
    x0, x1, z0, z1 = LK
    top = 12
    for x in (x0, x1):
        for z in (z0, z1):
            for y in range(1, top):
                p.set(x, y, z, "minecraft:spruce_log[axis=y]")
    for y in (5, 9):                                              # cross ties
        for x in range(x0 + 1, x1):
            p.fence(x, y, z0, "spruce")
            p.fence(x, y, z1, "spruce")
        for z in range(z0 + 1, z1):
            p.fence(x0, y, z, "spruce")
            p.fence(x1, y, z, "spruce")
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            p.set(x, top, z, "minecraft:spruce_planks")
            edge = x in (x0, x1) or z in (z0, z1)
            corner = x in (x0, x1) and z in (z0, z1)
            if corner:
                p.set(x, top + 1, z, "minecraft:spruce_log[axis=y]")
                p.set(x, top + 2, z, "minecraft:spruce_log[axis=y]")
            elif edge and (x, z) != (x0, z1):
                p.fence(x, top + 1, z, "spruce")
    p.hip_roof(x0, x1, z0, z1, top + 3, "spruce", overhang=1)
    p.ladder_column(x0, z1 + 1, 1, top, "south")
    p.set(x0, top + 1, z1, AIR)
    p.set(x0 + 1, top + 1, z0 + 1, "minecraft:bell[attachment=floor,facing=south,powered=false]")
    p.barrel(x1 - 1, top + 1, z1 - 1, facing="up")
    p.lantern(x1 - 1, top + 2, z1 - 1)


# ------------------------------------------------------------------ the yard
def _fire(p):
    for dx in range(-2, 3):
        for dz in range(-2, 3):
            d = abs(dx) + abs(dz)
            if d <= 3:
                p.set(FX + dx, 0, FZ + dz, "minecraft:gravel" if d <= 1 else "minecraft:cobblestone")
            if d == 2 and p.rnd.random() < 0.6:
                p.slab(FX + dx, 1, FZ + dz, p.rnd.choice(("cobblestone", "mossy_cobblestone")))
    p.set(FX, 1, FZ, state("minecraft:campfire", facing="north", lit=True, signal_fire=False, waterlogged=False))
    # log benches on three sides and stair seats
    for x in range(FX - 1, FX + 2):
        p.set(x, 1, FZ - 4, "minecraft:spruce_log[axis=x]")
    for z in range(FZ - 1, FZ + 2):
        p.set(FX - 4, 1, z, "minecraft:oak_log[axis=z]")
    p.stairs(FX + 4, 1, FZ - 1, "spruce", "east")
    p.stairs(FX + 4, 1, FZ + 1, "spruce", "east")
    # a spit: two fences and a stripped log over the fire? kept clear: a cooking cauldron beside
    p.set(FX + 2, 1, FZ - 2, "minecraft:cauldron")
    p.barrel(FX - 2, 1, FZ - 3, facing="up")
    p.spawner(FX + 3, 1, FZ - 3, "minecraft:pillager")


def _cage(p):
    x0, x1, z0, z1 = 30, 33, 18, 21
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            edge = x in (x0, x1) or z in (z0, z1)
            corner = x in (x0, x1) and z in (z0, z1)
            p.set(x, 0, z, "minecraft:cobblestone" if edge else "minecraft:gravel")
            for y in (1, 2, 3):
                if corner:
                    p.set(x, y, z, "minecraft:spruce_log[axis=y]")
                elif edge:
                    p.bars(x, y, z)
            p.slab(x, 4, z, "dark_oak", type="bottom")
    p.door(x0, 1, z0 + 1, "iron", "east", hinge="left", open=True)
    p.set(x1, 3, z0 + 2, AIR)                                    # a bent-out bar
    p.skull(x0 + 2, 1, z0 + 2, rotation=6)
    p.set(x0 + 1, 1, z0 + 2, "minecraft:bone_block[axis=x]")
    p.set(x1 - 1, 1, z0 + 1, "minecraft:cobweb")
    p.chain(x0 + 1, 3, z0 + 1)


def _goods(p):
    """The stolen-goods pile: barrels, a chest, hay, bolts of wool, a broken cart."""
    rows = (
        (6, 27, ("barrel", "barrel", "hay")), (7, 27, ("barrel", "wool")), (8, 27, ("hay", "hay", "wool")),
        (6, 28, ("wool", "barrel")), (7, 28, ("barrel",)), (6, 29, ("hay", "barrel")),
        (9, 27, ("barrel",)), (6, 30, ("barrel",)), (6, 31, ("wool",)),
    )
    wools = ("white", "light_blue", "yellow", "lime", "purple", "orange")
    for x, z, stack in rows:
        for i, kind in enumerate(stack):
            y = i + 1
            if kind == "barrel":
                p.barrel(x, y, z, facing=p.rnd.choice(("up", "east", "south", "north")))
            elif kind == "hay":
                p.set(x, y, z, f"minecraft:hay_block[axis={p.rnd.choice(('x', 'y', 'z'))}]")
            else:
                p.set(x, y, z, f"minecraft:{p.rnd.choice(wools)}_wool")
    p.chest(8, 1, 29, TABLE, "east")                              # the goods chest
    p.set(7, 1, 29, "minecraft:decorated_pot[cracked=true,facing=east,waterlogged=false]")
    p.set(7, 1, 30, "useful_armory:colosifiteore")
    p.set(9, 1, 28, "minecraft:spruce_planks")
    p.trapdoor(9, 2, 28, "spruce", "east")
    p.carpet(9, 1, 30, "purple")
    p.carpet(10, 1, 28, "light_blue")
    p.set(10, 1, 27, "minecraft:white_wool")
    # a cart with a missing wheel tipped against the pile
    for x in (11, 12):
        for z in (30, 31):
            p.slab(x, 1, z, "spruce", type="top")
    p.trapdoor(11, 1, 32, "spruce", "south", open=True)
    p.trapdoor(12, 1, 29, "spruce", "north", open=True)
    p.fence(13, 1, 30, "spruce")
    p.barrel(11, 2, 30, facing="up")
    p.set(12, 2, 31, "minecraft:hay_block[axis=z]")
    p.lantern(10, 1, 31)


def _training(p):
    """Target dummies (hay on a fence with fence arms) and a target line on the east side."""
    for x, z in ((27, 28), (30, 28), (33, 28)):
        p.fence(x, 1, z, "spruce")
        p.set(x, 2, z, "minecraft:hay_block[axis=y]")
        p.fence(x - 1, 2, z, "spruce")
        p.fence(x + 1, 2, z, "spruce")
        p.set(x, 3, z, "minecraft:carved_pumpkin[facing=north]")
    for z in (30, 31):
        p.set(34, 1, z, "minecraft:hay_block[axis=z]")
    p.set(34, 2, 30, "minecraft:target[power=0]")
    p.set(34, 1, 32, "minecraft:target[power=0]")
    p.barrel(27, 1, 31, facing="up")
    p.set(28, 1, 31, "minecraft:fletching_table")
    p.spawner(29, 1, 25, "minecraft:pillager")


def _yard(p):
    # pillager spawner just inside the gate, west of the road
    p.spawner(GATE[0] - 2, 1, PZ1 - 5, "minecraft:pillager")
    # woodpile against the north palisade, a chopping block
    for x in range(21, 26):
        for y in (1, 2):
            p.set(x, y, PZ0 + 2, p.rnd.choice(("minecraft:spruce_log[axis=z]", "minecraft:oak_log[axis=z]")))
    p.set(22, 1, PZ0 + 4, "minecraft:stripped_oak_log[axis=y]")
    # water butt and a trough by the longhouse
    p.barrel(LH[1] + 2, 1, LH[3], facing="up")
    p.set(LH[1] + 2, 1, LH[3] - 1, "minecraft:water_cauldron[level=3]")
    # lantern posts
    for x, z in ((15, 18), (25, 18), (14, 28)):
        p.fence(x, 1, z, "spruce")
        p.fence(x, 2, z, "spruce")
        p.set(x, 3, z, "minecraft:lantern[hanging=false,waterlogged=false]")
    # a drying rack of hides (carpet on fences)
    for z in (17, 18, 19):
        p.fence(5, 1, z, "spruce") if z != 18 else None
    # weeds along the wall foot and outside
    plants = p.mix(("minecraft:short_grass", 10), ("minecraft:fern", 3), ("minecraft:dandelion", 1),
                   ("minecraft:poppy", 1), ("minecraft:sweet_berry_bush[age=2]", 1))
    p.scatter((0, 1, 0, W - 1, 1, D - 1), plants, 0.22, only_on=GRASS)


def build():
    p = Piece("bandit_fort", W, H, D, "bandit_fort")
    _site(p)
    _paths(p)
    _palisade(p)
    _walkway(p)
    _tower(p, TW[0], TW[1], "west")
    _tower(p, TE[0], TE[1], "east")
    _gate(p)
    _longhouse(p)
    _leader(p)
    _lookout(p)
    _fire(p)
    _cage(p)
    _goods(p)
    _training(p)
    _yard(p)
    return p


PLACE = {
    "name": "bandit_fort",
    "pieces": {"bandit_fort": build},
    "step": "surface_structures",
    "start_height": 0,  # piece bottom lands at surface top block + start_height, so layer 0 replaces the top block
    "surface": True,
    "terrain": "beard_thin",
    "biomes": [
        "#minecraft:is_forest",
        "#minecraft:is_taiga",
        "#minecraft:is_savanna",
        "minecraft:plains",
        "minecraft:sunflower_plains",
        "minecraft:meadow",
    ],
    "spacing": 20,
    "separation": 8,
    "salt": 418200109,
}
