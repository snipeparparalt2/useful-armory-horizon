"""Colosifite watchtower: a round-cornered stone tower with sentries (surface). Brief:
docs/design/places.md section 4.

Layout (x east, z south; the tower stands north of the middle, the gate is on the south):
  * tower, 11 wide with cut corners, centred on (CX, CZ): a battered cobble plinth, stone
    walls with polished andesite quoins and string courses, iron-barred arrow slits.
    Four floors joined by one ladder against the west wall (north-west quarter):
      y 1..4    store room (door on the south side): barrels, crates, sacks, firewood, chest
      y 6..9    bunk room: four beds, table and benches, stove, tower sentry spawner
      y 11..14  armoury: weapon racks, anvil, grindstone, colosifite bullion, chest
      y 16..19  lookout: wide windows, map table, tower sentry spawner
  * the top: a walkway (y 20) wider than the tower, carried on upside-down stair
    machicolations, behind a crenellated parapet; a conical deepslate roof on four posts with
    a colosifite block finial, the best chest and a signal fire (campfire on hay) under it.
  * a ruined curtain wall round the yard: the north and west runs have mostly fallen, the
    east run still carries a stable lean-to, the south run has the gatehouse stub with a
    broken arch and portcullis; a well, a vegetable plot, a woodpile, an archery butt.
Loot (chests/colosifite_watchtower): store room, armoury, and the best one on the roof.
Spawners (useful_armory:tower_sentry): bunk room and lookout, both under a roof.
"""
from structkit import AIR, NS, Piece, state

W, H, D = 33, 31, 35
CX, CZ = 14, 13                   # tower centre
R = 5                             # tower wall radius: 11 wide
FLOORS = (0, 5, 10, 15)           # floor layer of each storey; rooms are the 4 layers above
TOP = 20                          # walkway floor
LX, LZ = CX - 4, CZ - 2           # the ladder column (against the west wall)
CWX0, CWX1, CWZ0, CWZ1 = 2, 30, 2, 29   # curtain wall line
GATE = (13, 14, 15)               # gate passage through the south curtain
SX0, SX1, SZ0, SZ1 = 25, 29, 5, 14      # stable floor (under the lean-to)

GRASS = "minecraft:grass_block[snowy=false]"
SIDES = ("north", "east", "south", "west")
STEP = {"north": (0, -1), "south": (0, 1), "east": (1, 0), "west": (-1, 0)}
TABLE = "colosifite_watchtower"
SENTRY = f"{NS}:tower_sentry"
COLO_BLOCK = f"{NS}:colosfiteblock"
COLO_ORE = f"{NS}:colosifiteore"
COLO_DEEP = f"{NS}:deepslate_colosifite_ore"


# ------------------------------------------------------------------ small helpers
def _pick(p, *weighted):
    names, weights = zip(*weighted)
    return p.rnd.choices(names, weights)[0]


def _inside(dx, dz, r):
    """The round-cornered footprint of radius r (2r+1 wide, corners cut by a step)."""
    ax, az = abs(dx), abs(dz)
    if ax > r or az > r:
        return False
    if (ax == r and az >= r - 1) or (az == r and ax >= r - 1):
        return False
    return True


def _edge(dx, dz, r):
    """True for a cell of the footprint with a side neighbour outside it."""
    return _inside(dx, dz, r) and any(not _inside(dx + a, dz + b, r) for a, b in STEP.values())


def _ring(r):
    """Cells of footprint r that are not in footprint r-1, as (x, z, [sides toward the inside])."""
    out = []
    for dx in range(-r, r + 1):
        for dz in range(-r, r + 1):
            if _inside(dx, dz, r) and not _inside(dx, dz, r - 1):
                inward = [s for s, (a, b) in STEP.items() if _inside(dx + a, dz + b, r - 1)]
                out.append((CX + dx, CZ + dz, inward))
    return out


def _stone(p, y, worn=False):
    """Tower stone: more cracks and moss low down and near openings."""
    if y <= 3 or worn:
        return _pick(p, ("minecraft:stone_bricks", 4), ("minecraft:cracked_stone_bricks", 3),
                     ("minecraft:mossy_stone_bricks", 3), ("minecraft:cobblestone", 1),
                     ("minecraft:andesite", 1))
    return _pick(p, ("minecraft:stone_bricks", 9), ("minecraft:cracked_stone_bricks", 2),
                 ("minecraft:mossy_stone_bricks", 1), ("minecraft:andesite", 1))


def _plinth(p):
    return _pick(p, ("minecraft:cobblestone", 4), ("minecraft:mossy_cobblestone", 3),
                 ("minecraft:stone", 1), ("minecraft:andesite", 1))


def _vine(p, x, y, z, wall_side):
    if p.in_bounds(x, y, z) and p.get(x, y, z) in (None, AIR):
        p.set(x, y, z, state("minecraft:vine", up=False, **{d: d == wall_side for d in SIDES}))


def _lichen(p, x, y, z, wall_side):
    if p.in_bounds(x, y, z) and p.get(x, y, z) in (None, AIR):
        p.set(x, y, z, state("minecraft:glow_lichen", up=False, down=False, waterlogged=False,
                             **{d: d == wall_side for d in SIDES}))


def _rubble(p, x, z, high=1):
    """A heap of fallen wall stone at (x, z), `high` blocks tall."""
    for y in range(1, high + 1):
        if y < high:
            p.set(x, y, z, _pick(p, ("minecraft:cobblestone", 3), ("minecraft:gravel", 1),
                                 ("minecraft:cracked_stone_bricks", 2), ("minecraft:mossy_cobblestone", 2)))
            continue
        roll = p.rnd.random()
        if roll < 0.3:
            p.stairs(x, y, z, p.rnd.choice(("stone_bricks", "cobblestone", "mossy_stone_bricks")),
                     p.rnd.choice(SIDES))
        elif roll < 0.6:
            p.slab(x, y, z, p.rnd.choice(("cobblestone", "stone_bricks", "mossy_cobblestone")))
        else:
            p.set(x, y, z, _pick(p, ("minecraft:cobblestone", 2), ("minecraft:mossy_cobblestone", 2),
                                 ("minecraft:cracked_stone_bricks", 1)))


def _cobweb(p, x, y, z):
    if p.get(x, y, z) == AIR:
        p.set(x, y, z, "minecraft:cobweb")


# ------------------------------------------------------------------ the site
def _site(p):
    """Air over a rounded site with natural ground; the far corners are left to the world."""
    cx, cz = (W - 1) / 2, (D - 1) / 2
    for x in range(W):
        for z in range(D):
            r = abs((x - cx) / (W / 2)) ** 4 + abs((z - cz) / (D / 2)) ** 4
            if r > 0.9 + p.rnd.uniform(-0.08, 0.08):
                continue
            p.set(x, 0, z, _pick(p, (GRASS, 14), ("minecraft:coarse_dirt", 3), ("minecraft:dirt", 1),
                                 ("minecraft:gravel", 1)))
            for y in range(1, H):
                p.set(x, y, z, AIR)
    # the yard inside the curtain is trodden: more bare earth and gravel
    for x in range(CWX0 + 1, CWX1):
        for z in range(CWZ0 + 1, CWZ1):
            if p.rnd.random() < 0.35:
                p.set(x, 0, z, _pick(p, ("minecraft:coarse_dirt", 3), ("minecraft:gravel", 1),
                                     ("minecraft:dirt", 1)))


def _path(p):
    """A path from the south edge through the gate to the tower door, worn at the edges."""
    for z in range(CZ + R + 1, D):
        for x in range(CX - 1, CX + 2):
            if not p.is_set(x, 0, z):
                continue
            edge = x != CX
            p.set(x, 0, z, p.rnd.choice(("minecraft:gravel", "minecraft:coarse_dirt", "minecraft:dirt_path"))
                  if edge and p.rnd.random() < 0.5 else "minecraft:dirt_path")
    for z in range(CWZ1 - 1, CWZ1 + 2):                       # cobbled gate passage
        for x in GATE:
            p.set(x, 0, z, _pick(p, ("minecraft:cobblestone", 3), ("minecraft:mossy_cobblestone", 1),
                                 ("minecraft:gravel", 1)))


# ------------------------------------------------------------------ the tower shell
def _tower_walls(p):
    """Walls from the ground to the walkway, quoins on the cut corners, string courses."""
    for dx in range(-R, R + 1):
        for dz in range(-R, R + 1):
            if not _edge(dx, dz, R):
                continue
            x, z = CX + dx, CZ + dz
            corner = abs(dx) == R - 1 and abs(dz) == R - 1
            p.set(x, 0, z, _plinth(p))
            for y in range(1, TOP):
                if y <= 2:
                    b = _plinth(p)
                elif y in (5, 10, 15):
                    b = _pick(p, ("minecraft:polished_andesite", 5), ("minecraft:andesite", 1))
                elif corner:
                    b = "minecraft:polished_andesite" if y % 2 else "minecraft:stone_bricks"
                elif y >= 18 and p.rnd.random() < 0.08:
                    b = COLO_ORE
                elif y <= 4 and p.rnd.random() < 0.04:
                    b = COLO_DEEP
                else:
                    b = _stone(p, y)
                p.set(x, y, z, b)


def _plinth_and_courses(p):
    """A battered plinth (blocks then stairs) round the foot and a stair string course at y 10."""
    for x, z, inward in _ring(R + 1):
        if z == CZ + R + 1 and abs(x - CX) <= 1:
            continue                                          # in front of the door
        p.set(x, 1, z, _plinth(p))
        if len(inward) == 1:
            p.stairs(x, 2, z, p.rnd.choice(("cobblestone", "mossy_cobblestone", "stone_bricks")), inward[0])
            p.stairs(x, 10, z, "stone_bricks", inward[0], half="top")
        else:
            p.slab(x, 2, z, "cobblestone")
            p.slab(x, 10, z, "stone_bricks", type="top")


def _pilasters(p):
    """Shallow pilasters on every face, a few missing stones and sills under the lookout."""
    for a, b in ((3, R + 1), (-3, R + 1), (3, -R - 1), (-3, -R - 1),
                 (R + 1, 3), (R + 1, -3), (-R - 1, 3), (-R - 1, -3)):
        x, z = CX + a, CZ + b
        for y in range(3, TOP - 1):
            p.set(x, y, z, "minecraft:polished_andesite" if y in (5, 10, 15) else _stone(p, y))
    for side in SIDES:                                        # stair sills under the lookout windows
        a, b = STEP[side]
        offs = (0, 1, 2) if side == "west" else (-1, 0, 1)
        inward = SIDES[(SIDES.index(side) + 2) % 4]
        for o in offs:
            x, z = (CX + a * (R + 1), CZ + o) if a else (CX + o, CZ + b * (R + 1))
            p.stairs(x, 16, z, "stone_bricks", inward, half="top")
    for x, y, z in ((CX + 2, 13, CZ - R), (CX - R, 8, CZ - 1), (CX + R, 17, CZ - 3)):
        p.set(x, y, z, "minecraft:mossy_cobblestone")         # patched holes


def _floors(p):
    """Floor layers of every storey: patterned, with a hole for the ladder."""
    for dx in range(-R + 1, R):
        for dz in range(-R + 1, R):
            if not _inside(dx, dz, R) or _edge(dx, dz, R):
                continue
            x, z = CX + dx, CZ + dz
            border = abs(dx) == R - 1 or abs(dz) == R - 1 or (abs(dx) == R - 2 and abs(dz) == R - 2)
            # store room: stone brick border, cobble field, a polished cross in the middle
            if border:
                b = "minecraft:stone_bricks"
            elif dx == 0 or dz == 0:
                b = "minecraft:polished_andesite"
            else:
                b = _pick(p, ("minecraft:cobblestone", 3), ("minecraft:andesite", 2),
                          ("minecraft:gravel", 1), ("minecraft:mossy_cobblestone", 1))
            p.set(x, 0, z, b)
            # bunk room: spruce boards with a dark oak border
            p.set(x, 5, z, "minecraft:dark_oak_planks" if border else "minecraft:spruce_planks")
            # armoury: polished andesite border, stone bricks, a colosifite inlay
            if border:
                b = "minecraft:polished_andesite"
            elif dx == 0 and dz == 0:
                b = COLO_BLOCK
            elif abs(dx) + abs(dz) == 1:
                b = "minecraft:chiseled_stone_bricks"
            else:
                b = _pick(p, ("minecraft:stone_bricks", 5), ("minecraft:cracked_stone_bricks", 1))
            p.set(x, 10, z, b)
            # lookout: spruce with a dark oak cross
            p.set(x, 15, z, "minecraft:dark_oak_planks" if dx == 0 or dz == 0 or border
                  else "minecraft:spruce_planks")
    # joists: stripped log beams under the timber floors, seen from below
    for x in range(CX - 3, CX + 4):
        for z in (CZ - 2, CZ + 2):
            if (x, z) != (LX, LZ):
                p.set(x, 5, z, "minecraft:stripped_spruce_log[axis=x]")
                p.set(x, 15, z, "minecraft:stripped_spruce_log[axis=x]")
    for y in (5, 10, 15, TOP):
        p.set(LX, y, LZ, AIR)
    p.ladder_column(LX, LZ, 1, TOP, "east")


def _openings(p):
    """The door, iron-barred arrow slits on three storeys, wide lookout windows."""
    door_z = CZ + R
    p.door(CX, 1, door_z, "spruce", "north", hinge="left")
    p.set(CX, 3, door_z, "minecraft:chiseled_stone_bricks")             # keystone
    p.stairs(CX - 1, 3, door_z + 1, "stone_bricks", "east", half="top")  # hood over the door
    p.stairs(CX, 3, door_z + 1, "stone_bricks", "north", half="top")
    p.stairs(CX + 1, 3, door_z + 1, "stone_bricks", "west", half="top")
    p.wall_torch(CX - 1, 2, door_z + 1, "south")
    p.set(CX, 0, door_z, "minecraft:polished_andesite")                 # threshold
    # arrow slits: two high, barred, with cracked stone round them
    for base in (0, 5, 10):
        for dx, dz in ((R, 0), (-R, 0), (0, -R), (0, R), (R, 2), (-R, 2)):
            if base == 0 and (dx, dz) == (0, R):
                continue                                                 # the door
            if base == 5 and (dx, dz) == (-R, 2):
                continue                                                 # behind the stove
            x, z = CX + dx, CZ + dz
            for y in (base + 2, base + 3):
                p.set(x, y, z, AIR)
                p.bars(x, y, z)
            if p.rnd.random() < 0.6:
                p.set(x, base + 4, z, "minecraft:cracked_stone_bricks")
    # lookout windows: three per side, two high, a polished sill
    for side in SIDES:
        a, b = STEP[side]
        offs = (0, 1, 2) if side == "west" else (-1, 0, 1)
        for o in offs:
            x, z = (CX + a * R, CZ + o) if a else (CX + o, CZ + b * R)
            p.set(x, 16, z, "minecraft:polished_andesite")
            for y in (17, 18):
                p.set(x, y, z, AIR)
        if side != "west":                                               # bars in the middle one
            x, z = (CX + a * R, CZ) if a else (CX, CZ + b * R)
            p.bars(x, 18, z)


def _top(p):
    """Machicolations, the walkway, the crenellated parapet, posts and the conical roof."""
    for x, z, inward in _ring(R + 1):                         # corbels under the walkway
        if len(inward) == 1:
            p.stairs(x, TOP - 1, z, "stone_bricks", inward[0], half="top")
        else:
            p.set(x, TOP - 1, z, "minecraft:polished_andesite")
    for dx in range(-R - 1, R + 2):
        for dz in range(-R - 1, R + 2):
            if not _inside(dx, dz, R + 1):
                continue
            x, z = CX + dx, CZ + dz
            if (x, z) == (LX, LZ):
                continue
            p.set(x, TOP, z, _pick(p, ("minecraft:stone_bricks", 4), ("minecraft:cracked_stone_bricks", 1),
                                   ("minecraft:polished_andesite", 1)) if _edge(dx, dz, R + 1)
                  else "minecraft:spruce_planks" if abs(dx) <= 3 and abs(dz) <= 3
                  else "minecraft:stone_bricks")
            if not _edge(dx, dz, R + 1):
                continue
            p.set(x, TOP + 1, z, _stone(p, TOP + 1))
            if (dx + dz) % 2 == 0:                            # merlons, a few knocked off
                cardinal = dx == 0 or dz == 0
                if cardinal:
                    p.set(x, TOP + 2, z, COLO_BLOCK)
                elif p.rnd.random() < 0.85:
                    p.set(x, TOP + 2, z, _stone(p, TOP + 2))
                else:
                    p.slab(x, TOP + 2, z, "stone_bricks")
    # posts and the roof
    for dx in (-3, 3):
        for dz in (-3, 3):
            for y in range(TOP + 1, TOP + 4):
                p.set(CX + dx, y, CZ + dz, "minecraft:stripped_spruce_log[axis=y]")
    for x in range(CX - 2, CX + 3):                            # tie beams between the posts
        for z in (CZ - 3, CZ + 3):
            p.set(x, TOP + 3, z, "minecraft:spruce_slab[type=top,waterlogged=false]")
    for z in range(CZ - 2, CZ + 3):
        for x in (CX - 3, CX + 3):
            p.set(x, TOP + 3, z, "minecraft:spruce_slab[type=top,waterlogged=false]")
    roof_y = TOP + 4
    p.hip_roof(CX - 3, CX + 3, CZ - 3, CZ + 3, roof_y, "deepslate_tiles", overhang=1,
               ridge_slab=COLO_BLOCK)
    for x in range(CX - 4, CX + 5):                            # weathered tiles
        for z in range(CZ - 4, CZ + 5):
            for y in range(roof_y, roof_y + 4):
                b = p.get(x, y, z)
                if b and b.startswith("minecraft:deepslate_tile_stairs") and p.rnd.random() < 0.2:
                    p.set(x, y, z, b.replace("deepslate_tile_stairs", "cobbled_deepslate_stairs"))
    p.set(CX, roof_y + 5, CZ, state("minecraft:lightning_rod", facing="up", powered=False, waterlogged=False))
    # signal fire on a hay bed under the roof, with a stone kerb
    p.set(CX, TOP, CZ, "minecraft:hay_block[axis=y]")
    p.set(CX, TOP + 1, CZ, state("minecraft:campfire", facing="south", lit=True, signal_fire=True,
                                 waterlogged=False))
    for side in SIDES:
        a, b = STEP[side]
        p.stairs(CX + a, TOP + 1, CZ + b, "stone_bricks", ("north", "east", "south", "west")[(SIDES.index(side) + 2) % 4])
    # the best chest, a look-out's kit and a lantern under the cone
    p.chest(CX + 2, TOP + 1, CZ + 2, TABLE, "west")
    p.barrel(CX + 2, TOP + 1, CZ - 2, facing="west")
    p.set(CX + 2, TOP + 2, CZ - 2, "minecraft:lantern[hanging=false,waterlogged=false]")
    p.set(CX - 2, TOP + 1, CZ + 2, "minecraft:fletching_table")
    p.set(CX - 2, TOP + 1, CZ - 2, "minecraft:spruce_trapdoor[facing=east,half=bottom,open=true,powered=false,waterlogged=false]")
    p.lantern(CX + 1, TOP + 3, CZ - 2, hanging=True)
    p.chain(CX + 1, TOP + 4, CZ - 2)
    p.chain(CX + 1, TOP + 5, CZ - 2)


# ------------------------------------------------------------------ the rooms
def _store_room(p):
    """Ground floor: barrels, crates, sacks, firewood, a water butt; the chest behind hay."""
    y = 1
    for x in range(CX - 2, CX + 3):                           # barrels along the north wall
        p.barrel(x, y, CZ - 4, facing=p.rnd.choice(("up", "south", "up", "east")))
        if x != CX:
            p.barrel(x, y + 1, CZ - 4, facing=p.rnd.choice(("up", "south")))
    p.set(CX, y + 1, CZ - 4, "minecraft:decorated_pot[cracked=false,facing=south,waterlogged=false]")
    # crates (planks with trapdoor lids) and sacks against the east wall
    for z in (CZ - 2, CZ - 1):
        p.set(CX + 4, y, z, "minecraft:spruce_planks")
        p.trapdoor(CX + 4, y + 1, z, "spruce", "west")
    p.set(CX + 4, y, CZ, "minecraft:brown_wool")
    p.set(CX + 4, y, CZ + 1, "minecraft:white_wool")
    p.set(CX + 4, y + 1, CZ, "minecraft:brown_carpet")
    p.set(CX + 3, y, CZ - 3, "minecraft:spruce_planks")
    p.trapdoor(CX + 3, y + 1, CZ - 3, "spruce", "south")
    # firewood stack in the south-east
    for z in (CZ + 2, CZ + 3):
        for yy in (y, y + 1):
            p.set(CX + 4, yy, z, p.rnd.choice(("minecraft:spruce_log[axis=z]", "minecraft:oak_log[axis=z]")))
        p.slab(CX + 3, y, z, "spruce")
    # the chest, tucked behind hay bales in the south-west corner
    p.chest(CX - 4, y, CZ + 3, TABLE, "north")
    p.set(CX - 3, y, CZ + 3, "minecraft:hay_block[axis=x]")
    p.set(CX - 3, y, CZ + 2, "minecraft:hay_block[axis=y]")
    p.set(CX - 3, y + 1, CZ + 3, "minecraft:hay_block[axis=z]")
    p.set(CX - 4, y, CZ + 1, "minecraft:water_cauldron[level=2]")
    p.set(CX - 4, y, CZ + 2, "minecraft:crafting_table")
    p.set(CX - 2, y, CZ + 4, "minecraft:composter[level=3]")
    # light and age
    p.lantern(CX + 1, 4, CZ, hanging=True)
    p.wall_torch(CX - 3, 3, CZ - 4, "south")
    for x, z in ((CX + 3, CZ - 3), (CX - 3, CZ + 3), (CX + 3, CZ + 3)):
        _cobweb(p, x, 4, z)
    _cobweb(p, CX + 4, 3, CZ + 1)


def _bunk_room(p):
    """Second floor: four beds on the east wall, a table, a stove, the first sentry spawner."""
    y = 6
    for z, colour in ((CZ - 3, "red"), (CZ - 1, "brown"), (CZ + 1, "red"), (CZ + 3, "gray")):
        p.bed(CX + 3, y, z, colour, "east")
    p.barrel(CX + 4, y, CZ - 2, facing="up")                  # night stands between the beds
    p.candle(CX + 4, y + 1, CZ - 2, candles=2, lit=False)
    p.set(CX + 4, y, CZ, "minecraft:chiseled_bookshelf[facing=west,slot_0_occupied=true,slot_1_occupied=false,"
          "slot_2_occupied=true,slot_3_occupied=false,slot_4_occupied=false,slot_5_occupied=true]")
    p.barrel(CX + 4, y, CZ + 2, facing="west")
    p.set(CX + 2, y, CZ - 3, "minecraft:red_carpet")
    p.set(CX + 2, y, CZ + 3, "minecraft:gray_carpet")
    # table with benches in the south-west
    for x in (CX - 2, CX - 1):
        p.fence(x, y, CZ + 3, "spruce")
        p.set(x, y + 1, CZ + 3, "minecraft:spruce_pressure_plate[powered=false]")
        p.stairs(x, y, CZ + 2, "spruce", "north")
    p.stairs(CX, y, CZ + 3, "spruce", "west")
    p.set(CX - 1, y + 1, CZ + 3, "minecraft:candle[candles=3,lit=true,waterlogged=false]")
    # stove and a kettle on the west wall
    p.set(CX - 4, y, CZ + 2, "minecraft:smoker[facing=east,lit=false]")
    p.set(CX - 4, y, CZ + 3, "minecraft:cauldron")
    p.set(CX - 4, y + 1, CZ + 2, "minecraft:spruce_trapdoor[facing=east,half=bottom,open=false,powered=false,waterlogged=false]")
    # a rug and the spawner where the sentries muster
    for x in range(CX - 1, CX + 2):
        for z in range(CZ - 1, CZ + 2):
            p.carpet(x, y, z, "red" if (x + z) % 2 else "brown")
    p.spawner(CX, y, CZ, SENTRY)
    # light and age
    p.lantern(CX - 1, 9, CZ - 2, hanging=True)
    p.lantern(CX + 2, 9, CZ + 1, hanging=True)
    for x, z in ((CX - 3, CZ - 3), (CX + 3, CZ + 3), (CX + 3, CZ - 3)):
        _cobweb(p, x, 9, z)


def _armoury(p):
    """Third floor: weapon racks, smithing corner, bullion stack and the second chest."""
    y = 11
    for x in range(CX - 2, CX + 3):                           # rack of spears on the north wall
        p.fence(x, y, CZ - 4, "spruce")
        p.set(x, y + 1, CZ - 4, state("minecraft:lightning_rod", facing="up", powered=False, waterlogged=False)
              if x % 2 else state("minecraft:tripwire_hook", facing="south", attached=False, powered=False))
        p.set(x, y + 2, CZ - 4, state("minecraft:spruce_shelf", facing="south", powered=False,
                                      side_chain="unconnected", waterlogged=False))
    p.trapdoor(CX - 3, y, CZ - 3, "spruce", "east", open=True)            # rack ends
    p.trapdoor(CX + 3, y, CZ - 3, "spruce", "west", open=True)
    # smithing corner on the east wall
    p.set(CX + 4, y, CZ - 2, "minecraft:smithing_table")
    p.set(CX + 3, y, CZ - 1, "minecraft:anvil[facing=north]")
    p.set(CX + 4, y, CZ, "minecraft:grindstone[face=floor,facing=north]")
    p.set(CX + 4, y, CZ + 1, "minecraft:water_cauldron[level=1]")
    # bullion and ore under guard in the south-east
    p.set(CX + 4, y, CZ + 3, COLO_BLOCK)
    p.set(CX + 4, y, CZ + 2, COLO_BLOCK)
    p.set(CX + 3, y, CZ + 3, COLO_ORE)
    p.set(CX + 4, y + 1, CZ + 3, COLO_BLOCK)
    p.slab(CX + 4, y + 1, CZ + 2, "smooth_stone")
    p.set(CX + 2, y, CZ + 4, "minecraft:iron_block")
    # the chest and armour boxes on the west wall
    p.chest(CX - 4, y, CZ + 2, TABLE, "east")
    p.barrel(CX - 4, y, CZ + 3, facing="east")
    p.barrel(CX - 4, y, CZ + 1, facing="up")
    p.set(CX - 4, y + 1, CZ + 1, "minecraft:skeleton_skull[powered=false,rotation=12]")
    # a practice dummy in the middle-south
    p.fence(CX - 1, y, CZ + 3, "spruce")
    p.set(CX - 1, y + 1, CZ + 3, "minecraft:hay_block[axis=y]")
    p.set(CX - 1, y + 2, CZ + 3, "minecraft:carved_pumpkin[facing=north]")
    # light and age
    p.lantern(CX, 14, CZ - 1, hanging=True)
    p.lantern(CX + 1, 14, CZ + 2, hanging=True)
    for x, z in ((CX - 3, CZ + 3), (CX + 3, CZ + 3)):
        _cobweb(p, x, 14, z)


def _lookout(p):
    """Top floor: map table, lectern, a bench under each window and the second spawner."""
    y = 16
    p.set(CX + 4, y, CZ - 3, "minecraft:cartography_table")
    p.set(CX + 3, y, CZ - 3, "minecraft:lectern[facing=south,has_book=false,powered=false]")
    p.barrel(CX - 3, y, CZ + 3, facing="up")
    p.barrel(CX - 3, y + 1, CZ + 3, facing="north")
    p.barrel(CX + 3, y, CZ + 3, facing="up")
    p.set(CX + 3, y + 1, CZ + 3, "minecraft:lantern[hanging=false,waterlogged=false]")
    p.set(CX - 2, y, CZ - 4, "minecraft:spruce_stairs[facing=south,half=bottom,shape=straight,waterlogged=false]")
    p.set(CX + 2, y, CZ - 4, "minecraft:spruce_stairs[facing=south,half=bottom,shape=straight,waterlogged=false]")
    p.set(CX - 4, y, CZ - 3, "minecraft:spruce_stairs[facing=west,half=bottom,shape=straight,waterlogged=false]")
    p.spawner(CX, y, CZ + 1, SENTRY)
    p.lantern(CX - 1, 19, CZ - 1, hanging=True)
    p.lantern(CX + 2, 19, CZ, hanging=True)
    _cobweb(p, CX + 3, 19, CZ + 3)
    _cobweb(p, CX - 3, 19, CZ + 3)


# ------------------------------------------------------------------ the curtain wall and yard
def _curtain_height(p):
    """A random walk of wall heights along each run: low where it has fallen."""
    heights = {}
    runs = (("n", [(x, CWZ0) for x in range(CWX0, CWX1 + 1)], (0, 3)),
            ("w", [(CWX0, z) for z in range(CWZ0 + 1, CWZ1)], (0, 4)),
            ("e", [(CWX1, z) for z in range(CWZ0 + 1, CWZ1)], (3, 6)),
            ("s", [(x, CWZ1) for x in range(CWX0, CWX1 + 1)], (2, 5)))
    for _, cells, (lo, hi) in runs:
        h = (lo + hi) // 2
        for c in cells:
            h = max(lo, min(hi, h + p.rnd.choice((-1, 0, 0, 1))))
            heights[c] = h
    for z in range(SZ0 - 1, SZ1 + 2):                          # the stable keeps its wall
        heights[(CWX1, z)] = 7
    return heights


def _curtain(p):
    heights = _curtain_height(p)
    for (x, z), h in heights.items():
        if z == CWZ1 and x in GATE:
            continue
        p.set(x, 0, z, _plinth(p))
        for y in range(1, h + 1):
            p.set(x, y, z, _plinth(p) if y == 1 else _stone(p, y, worn=h <= 3))
        if h >= 4 and (x + z) % 2 == 0 and not (x == CWX1 and SZ0 - 1 <= z <= SZ1 + 1):
            p.set(x, h + 1, z, _stone(p, h + 1))             # surviving merlons
        elif h >= 2 and p.rnd.random() < 0.3:
            p.slab(x, h + 1, z, p.rnd.choice(("stone_bricks", "cobblestone", "mossy_cobblestone")))
        if h <= 1:                                            # fallen stretch: rubble both sides
            for side in (-1, 1):
                rx, rz = (x + side, z) if x in (CWX0, CWX1) else (x, z + side)
                if p.in_bounds(rx, 1, rz) and p.get(rx, 1, rz) == AIR and p.rnd.random() < 0.55:
                    _rubble(p, rx, rz, 1)
    # buttresses on the outside of the standing runs
    for z in range(CWZ0 + 3, CWZ1 - 1, 5):
        if heights[(CWX1, z)] >= 3:
            for y in range(1, heights[(CWX1, z)]):
                p.set(CWX1 + 1, y, z, _plinth(p) if y == 1 else _stone(p, y))
            p.stairs(CWX1 + 1, heights[(CWX1, z)], z, "stone_bricks", "west")
    for x in range(CWX0 + 3, CWX1 - 1, 5):
        if x in range(9, 20):
            continue
        if heights[(x, CWZ1)] >= 3:
            for y in range(1, heights[(x, CWZ1)]):
                p.set(x, y, CWZ1 + 1, _plinth(p) if y == 1 else _stone(p, y))
            p.stairs(x, heights[(x, CWZ1)], CWZ1 + 1, "stone_bricks", "north")


def _gatehouse(p):
    """Two square stubs flanking the gate, a broken arch with a rusted portcullis."""
    tops = {}
    for x0, top in ((GATE[0] - 3, 7), (GATE[-1] + 1, 6)):
        for x in range(x0, x0 + 3):
            for z in range(CWZ1 - 1, CWZ1 + 2):
                hh = top - (1 if p.rnd.random() < 0.35 else 0) - (1 if (x, z) == (x0 + 2, CWZ1 + 1) else 0)
                tops[(x, z)] = hh
                p.set(x, 0, z, _plinth(p))
                for y in range(1, hh + 1):
                    corner = x in (x0, x0 + 2) and z in (CWZ1 - 1, CWZ1 + 1)
                    p.set(x, y, z, _plinth(p) if y <= 1 else
                          ("minecraft:polished_andesite" if corner and y % 2 else _stone(p, y, worn=y > 4)))
        p.set(x0 + 1, 4, CWZ1 + 1, AIR)                       # slit over the field
        p.bars(x0 + 1, 4, CWZ1 + 1)
    for z in range(CWZ1 - 1, CWZ1 + 2):                       # the arch
        p.stairs(GATE[0], 4, z, "stone_bricks", "west", half="top")
        p.stairs(GATE[-1], 4, z, "stone_bricks", "east", half="top")
        p.slab(GATE[1], 4, z, "stone_bricks", type="top")
        for x in GATE:
            if not (x == GATE[-1] and z == CWZ1 + 1):         # a bite out of the arch
                p.set(x, 5, z, _stone(p, 5, worn=True))
    p.set(GATE[1], 5, CWZ1 + 1, "minecraft:chiseled_stone_bricks")
    for x in GATE:                                            # the portcullis, rusted half up
        p.bars(x, 3, CWZ1)
    p.wall_torch(GATE[0] - 1, 3, CWZ1 + 2, "south")
    p.wall_torch(GATE[-1] + 1, 3, CWZ1 + 2, "south")
    # fallen arch stones in the passage verge
    _rubble(p, GATE[-1] + 4, CWZ1 + 3, 1)
    _rubble(p, GATE[0] - 3, CWZ1 + 2, 1)


def _stable(p):
    """A lean-to against the east curtain: slab shed roof on posts, stalls, hay and a trough."""
    roof = {SX0 - 1: (4, "bottom"), SX0: (4, "top"), SX0 + 1: (5, "bottom"), SX0 + 2: (5, "top"),
            SX0 + 3: (6, "bottom"), SX0 + 4: (6, "top")}
    for x, (y, kind) in roof.items():
        for z in range(SZ0 - 1, SZ1 + 2):
            p.slab(x, y, z, p.rnd.choice(("spruce", "spruce", "dark_oak")), type=kind)
    for z in (SZ0 - 1, (SZ0 + SZ1) // 2, SZ1 + 1):            # posts
        for y in range(1, 5):
            p.set(SX0, y, z, "minecraft:spruce_log[axis=y]")
    for x in range(SX0 + 1, SX1 + 1):                         # end boards
        for z in (SZ0 - 1, SZ1 + 1):
            for y in range(1, roof[x][0] + (0 if roof[x][1] == "bottom" else 1)):
                p.set(x, y, z, "minecraft:spruce_planks" if y > 1 else "minecraft:cobblestone")
    for x in range(SX0, SX1 + 1):                             # floor: straw and earth
        for z in range(SZ0, SZ1 + 1):
            p.set(x, 0, z, _pick(p, ("minecraft:coarse_dirt", 3), ("minecraft:dirt", 1), ("minecraft:packed_mud", 1)))
    for z in (SZ0 + 3, SZ0 + 6):                              # stall partitions
        for x in range(SX0 + 2, SX1 + 1):
            p.fence(x, 1, z, "spruce")
    # mangers, hay, a trough
    for z in (SZ0, SZ0 + 1, SZ0 + 4, SZ0 + 7, SZ0 + 8):
        p.set(SX1, 1, z, "minecraft:hay_block[axis=z]")
    p.set(SX1, 2, SZ0, "minecraft:hay_block[axis=x]")
    p.set(SX1, 1, SZ0 + 5, "minecraft:water_cauldron[level=3]")
    p.set(SX1, 1, SZ0 + 2, "minecraft:water_cauldron[level=2]")
    p.set(SX1, 1, SZ1, "minecraft:composter[level=5]")
    p.set(SX1 - 1, 1, SZ1, "minecraft:hay_block[axis=y]")
    for x, z in ((SX0 + 2, SZ0 + 1), (SX0 + 3, SZ0 + 5), (SX0 + 2, SZ0 + 8)):
        p.set(x, 1, z, "minecraft:moss_carpet")
    p.set(SX1, 3, SZ0 + 4, "minecraft:tripwire_hook[attached=false,facing=west,powered=false]")
    p.lantern(SX0 + 1, 4, (SZ0 + SZ1) // 2 - 1, hanging=True)
    p.lantern(SX0 + 1, 4, SZ0 + 1, hanging=True)
    _cobweb(p, SX1, 5, SZ0)


def _well(p):
    """A small roofed well in the south-west of the yard."""
    wx, wz = 6, 23
    for dx in (-1, 0, 1):
        for dz in (-1, 0, 1):
            x, z = wx + dx, wz + dz
            if dx == 0 and dz == 0:
                p.set(x, 0, z, "minecraft:water[level=0]")
                continue
            p.set(x, 0, z, "minecraft:cobblestone")
            p.set(x, 1, z, _pick(p, ("minecraft:stone_bricks", 2), ("minecraft:mossy_stone_bricks", 2),
                                 ("minecraft:cobblestone", 1)))
    for dx in (-1, 1):
        for y in (2, 3):
            p.fence(wx + dx, y, wz, "spruce")
    for x in range(wx - 2, wx + 3):
        p.stairs(x, 4, wz - 1, "spruce", "south")
        p.stairs(x, 4, wz + 1, "spruce", "north")
        p.slab(x, 4, wz, "spruce", type="bottom") if x in (wx - 2, wx + 2) else p.set(x, 4, wz, "minecraft:spruce_planks")
    p.set(wx, 4, wz, "minecraft:stripped_spruce_log[axis=x]")
    p.chain(wx, 3, wz)
    p.chain(wx, 2, wz)
    p.set(wx + 2, 1, wz + 1, "minecraft:cauldron")
    p.barrel(wx + 2, 1, wz - 1, facing="up")


def _yard(p):
    """Vegetable plot, woodpile, archery butt, cart; grass, flowers, vines."""
    # vegetable plot behind a low fence in the north-west
    for x in range(CWX0 + 2, CWX0 + 6):
        for z in range(CWZ0 + 3, CWZ0 + 9):
            if x == CWX0 + 4 and z == CWZ0 + 5:
                p.set(x, 0, z, "minecraft:water[level=0]")
                p.set(x, 1, z, "minecraft:spruce_trapdoor[facing=north,half=bottom,open=false,powered=false,waterlogged=false]")
                continue
            p.set(x, 0, z, "minecraft:farmland[moisture=7]")
            crop = p.rnd.choice(("minecraft:wheat[age=%d]", "minecraft:carrots[age=%d]", "minecraft:potatoes[age=%d]"))
            p.set(x, 1, z, crop % p.rnd.randint(2, 7))
    for x in range(CWX0 + 1, CWX0 + 7):
        if p.rnd.random() < 0.8:
            p.fence(x, 1, CWZ0 + 9, "spruce")
    # woodpile against the south curtain, east of the gate
    for x in range(GATE[-1] + 5, GATE[-1] + 9):
        for y in (1, 2):
            p.set(x, y, CWZ1 - 1, p.rnd.choice(("minecraft:spruce_log[axis=z]", "minecraft:oak_log[axis=z]",
                                                "minecraft:stripped_spruce_log[axis=z]")))
        p.slab(x, 3, CWZ1 - 1, "spruce")
    p.set(GATE[-1] + 6, 1, CWZ1 - 3, "minecraft:stripped_oak_log[axis=y]")
    # archery butt and a hand cart in the east yard
    p.set(27, 1, 20, "minecraft:hay_block[axis=y]")
    p.set(27, 2, 20, "minecraft:target[power=0]")
    p.set(27, 1, 21, "minecraft:hay_block[axis=x]")
    p.fence(27, 1, 19, "spruce")
    for x in (22, 23):
        for z in (22, 23):
            p.slab(x, 1, z, "spruce", type="top")
    p.trapdoor(21, 1, 22, "spruce", "west", open=True)
    p.trapdoor(24, 1, 23, "spruce", "east", open=True)
    p.fence(22, 1, 21, "spruce")
    p.set(23, 2, 22, "minecraft:hay_block[axis=x]")
    p.barrel(22, 2, 23, facing="up")
    # a lantern post at the yard crossing
    p.fence(CX + 3, 1, 23, "spruce")
    p.fence(CX + 3, 2, 23, "spruce")
    p.set(CX + 3, 3, 23, "minecraft:lantern[hanging=false,waterlogged=false]")
    # greenery
    plants = p.mix(("minecraft:short_grass", 10), ("minecraft:fern", 2), ("minecraft:poppy", 1),
                   ("minecraft:dandelion", 1), ("minecraft:cornflower", 1))
    p.scatter((0, 1, 0, W - 1, 1, D - 1), plants, 0.2, only_on=GRASS)
    # ivy up the shaded north face of the tower, lichen in the corners
    for dx in range(-3, 4):
        if p.rnd.random() < 0.55:
            top = p.rnd.randint(4, 12)
            for y in range(3, top):
                _vine(p, CX + dx, y, CZ - R - 1, "south")
    for dz in range(-3, 4):
        if p.rnd.random() < 0.35:
            for y in range(3, p.rnd.randint(4, 9)):
                _vine(p, CX - R - 1, y, CZ + dz, "east")
    _lichen(p, CX - 3, 1, CZ - 3, "north")


def build():
    p = Piece("colosifite_watchtower", W, H, D, "tower")
    _site(p)
    _path(p)
    _curtain(p)
    _gatehouse(p)
    _tower_walls(p)
    _plinth_and_courses(p)
    _pilasters(p)
    _floors(p)
    _openings(p)
    _top(p)
    _store_room(p)
    _bunk_room(p)
    _armoury(p)
    _lookout(p)
    _stable(p)
    _well(p)
    _yard(p)
    return p


PLACE = {
    "name": "colosifite_watchtower",
    "pieces": {"colosifite_watchtower": build},
    "step": "surface_structures",
    "start_height": 0,  # piece bottom lands at surface top block + start_height, so layer 0 replaces the top block
    "surface": True,
    "terrain": "beard_thin",
    "biomes": [
        "#minecraft:is_hill",
        "#minecraft:is_savanna",
        "#minecraft:is_badlands",
    ],
    "spacing": 34,
    "separation": 12,
    "salt": 418200104,
}
