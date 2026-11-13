"""Ruined forge: a burned-out stone smithy (surface). Brief: docs/design/places.md section 1.

Layout (x east, z south; the hall's long axis runs east-west):
  * forge hall, outer walls x 7..23, z 9..19: stone walls on a cobble plinth with corner piers,
    pilasters, corbels and a trim course. The west half keeps its deepslate tile roof over
    spruce rafters; the east half has fallen in, leaving bare rafters and a broken ridge beam.
  * chimney stack in the east gable (x 22..24, z 13..15) rising above the ridge, with the
    campfire hearth, two blast furnaces, a hood and a bellows at its foot.
  * lean-to store against the west gable (x 1..6, z 11..17) under a dark oak shed roof.
  * yard: a path from the south, the collapsed south wall spilling rubble, an overgrown cart,
    a woodpile, the stumps of an old fence and wild plants.
Loot (chests/ruined_forge): one chest in the store, one buried under rubble in the hall.
"""
from structkit import AIR, OPPOSITE, Piece, state

W, H, D = 32, 18, 29
X0, X1, Z0, Z1 = 7, 23, 9, 19     # hall outer walls
EAVE = 7                          # wall top (trim course) and the lowest roof course
RIDGE_Z = (Z0 + Z1) // 2          # 14
BREAK_X = 15                      # the roof east of about here has fallen in
DOOR_X = 11                       # west leaf of the double door (the east leaf is x 12)
GAP = range(17, 21)               # collapsed stretch of the south wall
LEAN_X0, LEAN_Z0, LEAN_Z1 = 1, 11, 17   # lean-to outer wall line and side walls

GRASS = "minecraft:grass_block[snowy=false]"
PODZOL = "minecraft:podzol[snowy=false]"
SIDES = ("north", "east", "south", "west")


# ------------------------------------------------------------------ small helpers
def _pick(p, *weighted):
    names, weights = zip(*weighted)
    return p.rnd.choices(names, weights)[0]


def _stone(p, y, worn=False):
    """Wall stone: more cracks and moss low down and around openings."""
    if y <= 2 or worn:
        return _pick(p, ("minecraft:stone_bricks", 3), ("minecraft:cracked_stone_bricks", 3),
                     ("minecraft:mossy_stone_bricks", 3), ("minecraft:cobblestone", 2),
                     ("minecraft:mossy_cobblestone", 1))
    return _pick(p, ("minecraft:stone_bricks", 7), ("minecraft:cracked_stone_bricks", 2),
                 ("minecraft:mossy_stone_bricks", 1), ("minecraft:andesite", 1))


def _plinth(p):
    return _pick(p, ("minecraft:cobblestone", 4), ("minecraft:mossy_cobblestone", 3),
                 ("minecraft:stone", 1))


def _vine(p, x, y, z, wall_side):
    """A vine on the face of the block at `wall_side` of the cell (only into air)."""
    if p.get(x, y, z) in (None, AIR):
        p.set(x, y, z, state("minecraft:vine", up=False, **{d: d == wall_side for d in SIDES}))


def _lichen(p, x, y, z, wall_side):
    if p.get(x, y, z) in (None, AIR):
        p.set(x, y, z, state("minecraft:glow_lichen", up=False, down=False, waterlogged=False,
                             **{d: d == wall_side for d in SIDES}))


def _roof_y(z):
    """Height of the roof course over row z (eaves at Z0-1 / Z1+1)."""
    return EAVE + min(z - (Z0 - 1), (Z1 + 1) - z)


def _rubble(p, x, z, high=1):
    """A heap of fallen stone and roof tiles at (x, z), `high` blocks tall."""
    for y in range(1, high + 1):
        if y < high:
            p.set(x, y, z, _pick(p, ("minecraft:cobblestone", 3), ("minecraft:gravel", 2),
                                 ("minecraft:cracked_stone_bricks", 2), ("minecraft:mossy_cobblestone", 1)))
            continue
        roll = p.rnd.random()
        if roll < 0.3:
            p.stairs(x, y, z, p.rnd.choice(("stone_bricks", "cobblestone", "deepslate_tiles")),
                     p.rnd.choice(SIDES))
        elif roll < 0.55:
            p.slab(x, y, z, p.rnd.choice(("cobblestone", "stone_bricks", "deepslate_tiles", "mossy_cobblestone")))
        elif roll < 0.7:
            p.set(x, y, z, "minecraft:gravel")
        else:
            p.set(x, y, z, _pick(p, ("minecraft:cobblestone", 2), ("minecraft:mossy_cobblestone", 2),
                                 ("minecraft:cracked_stone_bricks", 1)))


# ------------------------------------------------------------------ the site
def _site(p):
    """Air over a rounded site with natural ground; the far corners are left to the world."""
    cx, cz = (W - 1) / 2, (D - 1) / 2
    for x in range(W):
        for z in range(D):
            r = abs((x - cx) / (W / 2)) ** 3 + abs((z - cz) / (D / 2)) ** 3
            if r > 0.95 + p.rnd.uniform(-0.1, 0.1):
                continue
            p.set(x, 0, z, _pick(p, (GRASS, 14), ("minecraft:coarse_dirt", 3), (PODZOL, 1),
                                 ("minecraft:dirt", 1)))
            for y in range(1, H):
                p.set(x, y, z, AIR)


def _path(p):
    """A worn path from the south edge to the door, with gravel and coarse dirt verges."""
    for z in range(Z1 + 1, D):
        wobble = 0 if z < Z1 + 4 else (1 if (z // 3) % 2 else 0)
        for dx in (0, 1):
            p.set(DOOR_X + dx + wobble, 0, z, "minecraft:dirt_path")
        for dx in (-1, 2):
            if p.rnd.random() < 0.55 and p.is_set(DOOR_X + dx + wobble, 0, z):
                p.set(DOOR_X + dx + wobble, 0, z, p.rnd.choice(("minecraft:gravel", "minecraft:coarse_dirt")))


# ------------------------------------------------------------------ the hall
def _hall_floor(p):
    """Stone-brick border, cobble and andesite field, a polished anvil square, scorched patches."""
    for x in range(X0, X1 + 1):
        for z in range(Z0, Z1 + 1):
            p.set(x, 0, z, "minecraft:stone_bricks")
    for x in range(X0 + 2, X1 - 1):
        for z in range(Z0 + 2, Z1 - 1):
            p.set(x, 0, z, _pick(p, ("minecraft:cobblestone", 4), ("minecraft:andesite", 2),
                                 ("minecraft:mossy_cobblestone", 1), ("minecraft:stone", 1)))
    for x in range(14, 19):                                   # the anvil square
        for z in range(12, 17):
            edge = x in (14, 18) or z in (12, 16)
            p.set(x, 0, z, "minecraft:polished_andesite" if edge else "minecraft:smooth_stone")
    p.set(16, 0, 14, "minecraft:chiseled_stone_bricks")
    for x in range(19, 23):                                   # scorched hearth apron
        for z in range(12, 17):
            p.set(x, 0, z, _pick(p, ("minecraft:blackstone", 2), ("minecraft:polished_blackstone", 2),
                                 ("minecraft:coal_block", 1)))
    # where the roof came down: dirt and weeds through the floor
    for x, z in ((17, 11), (18, 11), (19, 17), (20, 11), (16, 17), (21, 17)):
        p.set(x, 0, z, p.rnd.choice(("minecraft:coarse_dirt", "minecraft:gravel", GRASS)))


def _hall_walls(p):
    """Plinth course, worn stone walls, trim course; the south wall has collapsed in one place."""
    for x in range(X0, X1 + 1):
        for z in range(Z0, Z1 + 1):
            if x not in (X0, X1) and z not in (Z0, Z1):
                continue
            top = EAVE
            if z == Z1 and x in GAP:
                top = p.rnd.choice((0, 1, 1, 2, 3))
            for y in range(1, top + 1):
                if y == 1:
                    b = _plinth(p)
                elif y == EAVE:
                    b = _pick(p, ("minecraft:polished_andesite", 4), ("minecraft:andesite", 1))
                else:
                    near_gap = z == Z1 and (GAP.start - 1 <= x <= GAP.stop)
                    b = _stone(p, y, worn=near_gap)
                p.set(x, y, z, b)
    # gable triangles: timber over the store (west), stone round the chimney (east)
    for z in range(Z0 + 1, Z1):
        for y in range(EAVE + 1, _roof_y(z)):
            p.set(X0, y, z, "minecraft:stripped_spruce_log[axis=y]" if z % 2 == 0 else "minecraft:spruce_planks")
            if y < _roof_y(z) - (1 if p.rnd.random() < 0.4 else 0):      # crumbled top
                p.set(X1, y, z, _stone(p, y, worn=y > EAVE + 3))
    for z in range(Z0 + 1, Z1):                               # sill beam under the timber gable
        p.set(X0, EAVE + 1, z, "minecraft:stripped_spruce_log[axis=z]")


def _wall_depth(p):
    """Corner piers, pilasters, plinth skirting stairs and corbels under the eaves."""
    for cx, cz, ox, oz in ((X0, Z0, -1, -1), (X1, Z0, 1, -1), (X0, Z1, -1, 1), (X1, Z1, 1, 1)):
        for y in range(1, EAVE):
            for px, pz in ((cx + ox, cz), (cx, cz + oz), (cx + ox, cz + oz)):
                if p.in_bounds(px, y, pz):
                    p.set(px, y, pz, _plinth(p) if y <= 2 else _stone(p, y))
        p.slab(cx + ox, EAVE, cz + oz, "stone_bricks")
    pilasters = (15, 19)
    for x in pilasters:
        for z, out in ((Z0 - 1, "north"), (Z1 + 1, "south")):
            if z == Z1 + 1 and x in GAP:
                continue
            for y in range(1, EAVE):
                p.set(x, y, z, _plinth(p) if y == 1 else _stone(p, y))
    # skirting stairs at the foot of the long walls, corbels under the eaves
    for x in range(X0 + 1, X1):
        for z, inward in ((Z0 - 1, "south"), (Z1 + 1, "north")):
            if x in pilasters or (z == Z1 + 1 and (x in GAP or x in (DOOR_X, DOOR_X + 1))):
                continue
            p.stairs(x, 1, z, p.rnd.choice(("cobblestone", "mossy_cobblestone", "stone_bricks")), inward)
            p.stairs(x, EAVE - 1, z, "stone_bricks", inward, half="top")
    for z in range(Z0 + 1, Z1):                               # skirting on the east gable
        if not (13 <= z <= 15):
            p.stairs(X1 + 1, 1, z, p.rnd.choice(("cobblestone", "mossy_cobblestone")), "west")


def _openings(p):
    """Double door with one leaf gone, barred and glazed windows, shuttered north windows."""
    for dx in (0, 1):
        for y in (1, 2):
            p.set(DOOR_X + dx, y, Z1, AIR)
    p.door(DOOR_X, 1, Z1, "dark_oak", "north", hinge="left", open=True)
    for x in range(DOOR_X - 1, DOOR_X + 3):                   # lintel
        p.set(x, 3, Z1, "minecraft:stripped_spruce_log[axis=x]")
    for x in range(DOOR_X - 1, DOOR_X + 3):                   # a stone hood over the door
        p.stairs(x, 4, Z1 + 1, "stone_bricks", "north", half="top")
    p.stairs(DOOR_X - 2, 4, Z1 + 1, "stone_bricks", "east", half="top")
    p.stairs(DOOR_X + 3, 4, Z1 + 1, "stone_bricks", "west", half="top")
    # windows: (x, wall z, outward side, glazing)
    for x, z, out, kind in ((9, Z1, "south", "bars"), (13, Z1, "south", "pane"),
                            (11, Z0, "north", "shutter"), (17, Z0, "north", "shutter"),
                            (21, Z0, "north", "bars")):
        ox = {"south": 1, "north": -1}[out]
        for y in (3, 4):
            p.set(x, y, z, AIR)
            if kind == "bars":
                p.bars(x, y, z)
            elif kind == "pane" and y == 3:
                p.pane(x, y, z)                               # the upper pane is broken out
        p.stairs(x, 2, z + ox, "stone_bricks", OPPOSITE[out], half="top")      # sill
        for dx in (-1, 0, 1):
            p.set(x + dx, 5, z, "minecraft:stripped_spruce_log[axis=x]")      # lintel
        if kind == "shutter":
            for y in (3, 4):
                p.trapdoor(x - 1, y, z + ox, "spruce", out, open=True)
                if x == 11:                                   # one shutter has fallen off
                    p.trapdoor(x + 1, y, z + ox, "spruce", out, open=True)
    # a doorway through the west gable into the store
    p.door(X0, 1, RIDGE_Z, "spruce", "west", hinge="right")
    p.set(X0, 3, RIDGE_Z, "minecraft:stripped_spruce_log[axis=z]")


def _roof(p):
    """Deepslate tiles over spruce rafters on the west half; the east half has fallen in."""
    rafters = (8, 11, 14, 17, 20)
    tile = lambda: _pick(p, ("deepslate_tiles", 5), ("cobbled_deepslate", 1), ("deepslate_bricks", 1))  # noqa: E731
    for i in range(RIDGE_Z - Z0 + 2):
        y = EAVE + i
        for z, facing in ((Z0 - 1 + i, "south"), (Z1 + 1 - i, "north")):
            reach = BREAK_X + max(0, 3 - i) + p.rnd.randint(-1, 1)       # ragged break line
            for x in range(X0 - 1, X1 + 2):
                if not p.in_bounds(x, y, z) or (X1 - 1 <= x <= X1 + 1 and 13 <= z <= 15):
                    continue                                            # chimney stack
                ridge = z == RIDGE_Z
                if x < reach:
                    if ridge:
                        p.slab(x, y, z, "deepslate_tiles")
                    else:
                        p.stairs(x, y, z, tile(), facing)
                elif x in rafters and not ridge and (x != 20 or i < 4):
                    p.stairs(x, y, z, "spruce", facing)                 # bare charred rafter
                if x in rafters and Z0 < z < Z1 and not ridge and i >= 2 and x < reach:
                    p.stairs(x, y - 1, z, "spruce", OPPOSITE[facing], half="top")
    for x in range(X0, 19):                                   # ridge beam, snapped
        p.set(x, _roof_y(RIDGE_Z) - 1, RIDGE_Z, "minecraft:stripped_spruce_log[axis=x]")
    for x in (10, 14, 18):                                    # tie beams across the hall
        for z in range(Z0, Z1 + 1):
            if x == 18 and z > 12:
                continue                                      # this one broke and fell
            p.set(x, EAVE, z, "minecraft:stripped_spruce_log[axis=z]")
    for z in range(13, 18):                                   # the fallen half of the beam
        p.set(18 + (z - 13) // 3, 1, z, "minecraft:stripped_spruce_log[axis=z]")
    # cobwebs where the roof still stands
    for x, y, z in ((8, 8, 10), (8, 8, 18), (9, 9, 11), (12, 11, 13), (8, 11, 15), (13, 9, 17)):
        if p.get(x, y, z) == AIR:
            p.set(x, y, z, "minecraft:cobweb")


# ------------------------------------------------------------------ forge works
def _chimney(p):
    """Square stack through the east gable: hearth with a campfire, hood, two blast furnaces."""
    top = 16
    for y in range(1, top + 1):
        for x in range(X1 - 1, X1 + 2):
            for z in range(13, 16):
                if y == top and (x == X1 or z == 14):
                    p.set(x, y, z, AIR)
                    continue
                if y == top:
                    p.wall(x, y, z, "cobblestone")
                elif y == top - 1:
                    p.set(x, y, z, "minecraft:polished_andesite")
                else:
                    p.set(x, y, z, _plinth(p) if y <= 2 else _stone(p, y, worn=y > 11))
    for y in range(2, top):                                   # the flue
        p.set(X1, y, 14, AIR)
    p.set(X1, 1, 14, state("minecraft:campfire", facing="west", lit=True, signal_fire=False,
                           waterlogged=False))
    for y in (1, 2):                                          # hearth mouth
        p.set(X1 - 1, y, 14, AIR)
    p.set(X1 - 1, 3, 14, "minecraft:chiseled_stone_bricks")
    for z in (13, 14, 15):                                    # hood
        p.stairs(X1 - 2, 3, z, "stone_bricks", "east", half="top")
    p.set(X1 - 2, 1, 13, "minecraft:blast_furnace[facing=west,lit=false]")
    p.set(X1 - 2, 1, 15, "minecraft:blast_furnace[facing=west,lit=false]")
    p.slab(X1 - 2, 1, 14, "smooth_stone")                     # hearth plate
    for z in (12, 16):                                        # vines and lichen on the stack
        _lichen(p, X1 - 1, p.rnd.randint(5, 8), z, "south" if z == 12 else "north")
    for y in range(6, 12):
        _vine(p, X1 + 2, y, 15 if y % 2 else 14, "west")


def _bellows(p):
    """A barrel on its side blowing into the hearth, with trapdoor boards for the bellows."""
    p.barrel(X1 - 1, 1, 12, facing="south")
    p.trapdoor(X1 - 1, 2, 12, "spruce", "south")
    p.trapdoor(X1 - 1, 1, 11, "spruce", "north", open=True)


def _smithy(p):
    """Anvils on the polished square, quench troughs, tool wall, smithing table, coal pile."""
    p.set(16, 1, 14, "minecraft:anvil[facing=east]")
    p.set(17, 1, 13, "minecraft:damaged_anvil[facing=north]")
    for x in (15, 16):                                        # quench trough
        p.set(x, 1, 16, "minecraft:water_cauldron[level=3]" if x == 15 else "minecraft:water_cauldron[level=1]")
    p.set(14, 1, 13, "minecraft:grindstone[face=floor,facing=east]")
    p.set(14, 1, Z0 + 1, "minecraft:smithing_table")
    p.set(13, 1, Z0 + 1, "minecraft:chipped_anvil[facing=west]")
    # tool wall on the north wall: shelves, pokers (lightning rods), hooks
    for x in (8, 9, 10, 12):
        p.set(x, 3, Z0 + 1, state("minecraft:spruce_shelf", facing="south", powered=False,
                                  side_chain="unconnected", waterlogged=False))
    for x in (8, 9, 12):
        p.set(x, 2, Z0 + 1, state("minecraft:lightning_rod", facing="south", powered=False, waterlogged=False))
        p.set(x, 4, Z0 + 1, state("minecraft:tripwire_hook", facing="south", attached=False, powered=False))
    p.set(10, 1, Z0 + 1, "minecraft:stonecutter[facing=south]")
    # a workbench of slabs on barrels along the south wall, with a candle and a crock
    for x in (13, 14, 15):
        p.barrel(x, 1, Z1 - 1, facing="north")
        p.slab(x, 2, Z1 - 1, "spruce", type="bottom")
    p.candle(13, 3, Z1 - 1, candles=2, lit=False)
    p.set(15, 3, Z1 - 1, "minecraft:decorated_pot[cracked=true,facing=north,waterlogged=false]")
    # coal pile in the north-west corner
    for x, z, h in ((8, 16, 2), (8, 17, 1), (9, 17, 1), (8, 18, 1), (9, 18, 2)):
        for y in range(1, h + 1):
            p.set(x, y, z, "minecraft:coal_block")
    p.slab(9, 1, 16, "blackstone")
    p.slab(10, 1, 18, "blackstone")


def _hall_fittings(p):
    """Work table and bench in the west half, a water barrel by the door, hanging lanterns."""
    for x in (10, 11, 12):                                   # fence-post table with iron plates
        p.fence(x, 1, 14, "spruce")
        p.set(x, 2, 14, "minecraft:heavy_weighted_pressure_plate[power=0]" if x != 11
              else "minecraft:spruce_pressure_plate[powered=false]")
    for x in (10, 12):
        p.stairs(x, 1, 15, "spruce", "south")                 # bench seats facing the table
    p.stairs(11, 1, 13, "spruce", "north")
    p.barrel(8, 1, Z1 - 1, facing="up")                       # rain barrel and buckets by the door
    p.barrel(9, 1, Z1 - 1, facing="north")
    p.set(8, 2, Z1 - 1, "minecraft:cauldron")
    for x, z in ((10, 12), (14, 15)):                         # lanterns on chains from tie beams
        p.hanging_lantern(x, EAVE - 2, z, chain=1)
    p.wall_torch(8, 3, 15, "east")


def _charcoal_clamp(p):
    """A burnt-out charcoal clamp in the north-west yard: a low mound of earth and coal."""
    for x in range(3, 7):
        for z in range(3, 7):
            edge = x in (3, 6) or z in (3, 6)
            if edge and (x, z) in ((3, 3), (6, 3), (3, 6), (6, 6)):
                continue
            p.set(x, 0, z, "minecraft:coarse_dirt")
            p.set(x, 1, z, p.rnd.choice(("minecraft:coarse_dirt", "minecraft:coal_block", "minecraft:podzol[snowy=false]"))
                  if edge else "minecraft:coal_block")
            if not edge:
                p.slab(x, 2, z, p.rnd.choice(("blackstone", "cobbled_deepslate")))
    p.set(7, 1, 5, "minecraft:dead_bush")
    p.set(7, 1, 3, "minecraft:stripped_spruce_log[axis=z]")


def _ruin(p):
    """Roof rubble in the east half, the buried chest and the half-buried ingot stacks."""
    p.chest(20, 1, 17, "ruined_forge", "north")               # the find: under the heap
    for x, z, h in ((19, 17, 2), (20, 17, 0), (21, 17, 2), (20, 18, 2), (19, 18, 1), (20, 16, 1),
                    (21, 16, 1), (19, 16, 1), (18, 18, 1), (17, 17, 1)):
        if h:
            _rubble(p, x, z, h)
    p.set(20, 2, 17, "minecraft:gravel")
    p.slab(20, 3, 17, "deepslate_tiles")
    p.set(22, 1, 18, "useful_armory:colosfiteblock")          # ingot stacks in the rubble
    p.set(22, 1, 17, "useful_armory:shadowblock")
    p.set(22, 2, 18, "useful_armory:colosfiteblock")
    p.set(21, 1, 18, "minecraft:iron_block")
    p.slab(21, 2, 18, "cobblestone")
    p.stairs(22, 2, 17, "deepslate_tiles", "west")
    for x, z in ((16, 11), (17, 10), (19, 10), (20, 14), (18, 15), (17, 18), (16, 18)):
        if p.get(x, 1, z) == AIR:
            _rubble(p, x, z, 1)
    for x, z in ((17, 11), (19, 17), (16, 17)):              # weeds where the sky gets in
        if p.get(x, 1, z) == AIR and p.get(x, 0, z) in (GRASS, "minecraft:coarse_dirt"):
            p.set(x, 1, z, p.rnd.choice(("minecraft:short_grass", "minecraft:fern")))
    for x, y, z, side in ((X1 - 1, 4, 11, "east"), (X1 - 1, 5, 17, "east"), (21, 3, Z0 + 1, "north"),
                          (19, 2, Z0 + 1, "north")):
        _lichen(p, x, y, z, side)


def _spill(p):
    """The collapsed south wall spills stone and tiles into the yard."""
    for x in range(GAP.start - 1, GAP.stop + 1):
        for z in range(Z1 + 1, Z1 + 5):
            dist = z - Z1 + abs(x - 18.5) / 2
            if p.rnd.random() < 1.1 - dist * 0.22:
                _rubble(p, x, z, 2 if dist < 1.6 and p.rnd.random() < 0.6 else 1)
    p.set(18, 0, Z1 + 2, "minecraft:gravel")
    p.set(17, 1, Z1 + 3, "minecraft:moss_carpet")


# ------------------------------------------------------------------ the store
def _store(p):
    """Lean-to store: cobble footing, spruce boarding, dark oak shed roof; crates and the chest."""
    x0, x1 = LEAN_X0, X0 - 1
    for x in range(x0, x1 + 1):
        roof = 3 + (x - (x0 - 1))                             # shed roof course over column x
        for z in range(LEAN_Z0, LEAN_Z1 + 1):
            if x == x0:                                       # eave over the outer wall
                p.stairs(x - 1, roof - 1, z, "dark_oak", "east")
            p.stairs(x, roof, z, p.rnd.choice(("dark_oak", "dark_oak", "dark_oak", "spruce")), "east")
            wall = x == x0 or z in (LEAN_Z0, LEAN_Z1)
            for y in range(1, roof):
                if wall:
                    corner = x == x0 and z in (LEAN_Z0, LEAN_Z1)
                    if y == 1:
                        b = _plinth(p)
                    elif corner or (z in (LEAN_Z0, LEAN_Z1) and x == x1):
                        b = "minecraft:stripped_spruce_log[axis=y]"
                    else:
                        b = _pick(p, ("minecraft:spruce_planks", 5), ("minecraft:stripped_spruce_log[axis=y]", 1))
                    p.set(x, y, z, b)
                else:
                    p.set(x, y, z, AIR)
            p.set(x, 0, z, "minecraft:spruce_planks" if not wall else "minecraft:cobblestone")
    # floor: spruce boards with a dirt-trodden strip to the door
    for x in range(x0 + 1, x1 + 1):
        p.set(x, 0, RIDGE_Z, "minecraft:coarse_dirt" if x > x0 + 2 else "minecraft:spruce_planks")
    # a shuttered window in the outer wall
    p.set(x0, 2, RIDGE_Z, AIR)
    p.pane(x0, 2, RIDGE_Z)
    p.trapdoor(x0 - 1, 2, RIDGE_Z - 1, "dark_oak", "west", open=True)
    # contents
    p.chest(x0 + 1, 1, LEAN_Z1 - 1, "ruined_forge", "east")
    p.barrel(x0 + 1, 1, LEAN_Z0 + 1, facing="up")
    p.barrel(x0 + 1, 2, LEAN_Z0 + 1, facing="east")
    p.barrel(x0 + 2, 1, LEAN_Z0 + 1, facing="south")
    for x in (x0 + 3, x0 + 4):                                # crates of iron
        p.set(x, 1, LEAN_Z0 + 1, "minecraft:spruce_planks")
        p.trapdoor(x, 2, LEAN_Z0 + 1, "spruce", "south")
    p.set(x0 + 5, 1, LEAN_Z0 + 1, "minecraft:iron_block")
    p.set(x0 + 2, 1, LEAN_Z1 - 1, "useful_armory:colosifiteore")      # unworked ore
    p.set(x0 + 3, 1, LEAN_Z1 - 1, "minecraft:raw_iron_block")
    p.set(x0 + 4, 1, LEAN_Z1 - 1, "minecraft:coal_block")
    p.set(x0 + 4, 2, LEAN_Z1 - 1, "useful_armory:shadowore")
    for z in (LEAN_Z0 + 2, LEAN_Z1 - 2):                      # shelves on the back wall
        p.set(x0 + 1, 2, z, state("minecraft:spruce_shelf", facing="east", powered=False,
                                  side_chain="unconnected", waterlogged=False))
    p.hanging_lantern(x0 + 3, 4, RIDGE_Z, chain=1)
    p.set(x0 + 1, 3, LEAN_Z0 + 1, "minecraft:cobweb")


# ------------------------------------------------------------------ the yard
def _cart(p):
    """An overgrown hand cart east of the hall, one wheel gone."""
    bx, bz = 27, 21                                           # bed x 27..28, z 21..23
    for x in (bx, bx + 1):
        for z in range(bz, bz + 3):
            p.slab(x, 1, z, "spruce", type="top")
    p.trapdoor(bx - 1, 1, bz + 1, "spruce", "west", open=True)        # west wheel
    for z in (bz, bz + 2):
        p.fence(bx, 2, z, "spruce")
        p.fence(bx + 1, 2, z, "spruce")
    p.fence(bx, 1, bz - 1, "spruce")                          # the shaft, resting on the ground
    p.fence(bx, 1, bz - 2, "spruce")
    p.set(bx + 1, 2, bz + 1, "minecraft:hay_block[axis=z]")
    p.set(bx, 2, bz + 1, "minecraft:moss_carpet")
    p.set(bx + 2, 1, bz + 2, "minecraft:sweet_berry_bush[age=2]")
    p.set(bx + 2, 1, bz, "minecraft:tall_grass[half=lower]")
    p.set(bx + 2, 2, bz, "minecraft:tall_grass[half=upper]")


def _woodpile(p):
    """Split logs stacked against the north wall under a slab lid, a chopping block beside."""
    for x in range(12, 15):
        for y in (1, 2):
            p.set(x, y, Z0 - 2, p.rnd.choice(("minecraft:spruce_log[axis=z]", "minecraft:oak_log[axis=z]",
                                               "minecraft:stripped_spruce_log[axis=z]")))
        p.slab(x, 3, Z0 - 2, "spruce")
    p.set(16, 1, Z0 - 3, "minecraft:stripped_oak_log[axis=y]")
    p.set(17, 1, Z0 - 3, "minecraft:oak_log[axis=x]")


def _fence(p):
    """Rotting fence stubs along the south of the yard, a gate standing open at the path."""
    z = D - 4
    for x in range(3, 26):
        if x in (DOOR_X, DOOR_X + 1, DOOR_X + 2) or not p.is_set(x, 0, z):
            continue
        if p.rnd.random() < 0.6:
            p.fence(x, 1, z, "spruce")
    p.fence_gate(DOOR_X - 1, 1, z, "spruce", "south", open=True)
    p.fence(DOOR_X - 2, 1, z, "spruce")
    p.fence(DOOR_X + 3, 1, z, "spruce")
    p.set(DOOR_X - 2, 2, z, "minecraft:lantern[hanging=false,waterlogged=false]")


def _greenery(p):
    """Grass, ferns and flowers on the open ground; vines down the shaded north wall."""
    plants = p.mix(("minecraft:short_grass", 10), ("minecraft:fern", 3), ("minecraft:poppy", 1),
                   ("minecraft:dandelion", 1), ("minecraft:oxeye_daisy", 1))
    p.scatter((0, 1, 0, W - 1, 1, D - 1), plants, 0.22, only_on=GRASS)
    for x in range(X0, X1 + 1):
        if p.rnd.random() < 0.45:
            for y in range(EAVE - 1, EAVE - 1 - p.rnd.randint(1, 4), -1):
                _vine(p, x, y, Z0 - 1, "south")


def build():
    p = Piece("ruined_forge", W, H, D, "forge")
    _site(p)
    _path(p)
    _hall_floor(p)
    _hall_walls(p)
    _wall_depth(p)
    _openings(p)
    _roof(p)
    _chimney(p)
    _bellows(p)
    _smithy(p)
    _hall_fittings(p)
    _ruin(p)
    _spill(p)
    _store(p)
    _cart(p)
    _woodpile(p)
    _charcoal_clamp(p)
    _fence(p)
    _greenery(p)
    return p


PLACE = {
    "name": "ruined_forge",
    "pieces": {"ruined_forge": build},
    "step": "surface_structures",
    "start_height": -1,
    "surface": True,
    "terrain": "beard_thin",
    "biomes": [
        "#minecraft:is_forest",
        "minecraft:plains",
        "minecraft:sunflower_plains",
        "minecraft:meadow",
    ],
    "spacing": 28,
    "separation": 10,
    "salt": 418200101,
}
