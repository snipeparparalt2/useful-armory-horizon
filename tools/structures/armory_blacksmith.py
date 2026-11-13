"""Armory blacksmith: a village smithy appended to the vanilla village house pools.
Brief: docs/design/places.md section 9.

Plan (x east, z south; the street is to the south; piece 15 x 13 x 13):

    x  0   1 ............ 9  10 .. 12  13  14
    z0     margin (roof overhang)
    z1     +-- shop -------+-- chimney --+ post
           | loft  (x2..4) |  hearth     |
           | counter       |  forge porch|  (open south and east, on posts)
    z9     +----door-------+-------------+ post
    z10           step / path stub
    z12           street connector (x 5)

* y = 0 is the foundation layer (it replaces the terrain's top block); the building stands
  from y = 1. Air is set over the footprint and a one-block margin, nothing else is painted.
* One long gabled spruce roof (ridge east-west) covers the shop and the forge porch; the
  enclosed west part is the shop, the open east bay under the same roof is the porch.
* Shop: stone lower walls (plinth, cobble and stone brick mix), timber-framed upper walls
  (spruce posts and plates, packed mud infill), glazed and shuttered windows, a counter,
  barrels, display shelves, a smithing table, a sleeping loft up a ladder.
* Porch: stone chimney stack with a lit campfire in the hearth (smoke goes up the flue),
  blast furnace and furnace, anvil, grindstone, a water trough, tool rack, coal and a
  woodpile.
Loot (chests/village_blacksmith): one chest behind the counter, one in the loft.
"""
from structkit import AIR, Piece, state

W, H, D = 15, 13, 13
X0, X1, Z0, Z1 = 1, 13, 1, 9        # footprint (outer wall / post lines)
SHOP_X1 = 9                         # east wall of the shop (porch is x 10..13)
EAVE = 6                            # lowest roof course
DOOR_X = 5
RIDGE_Z = (Z0 + Z1) // 2            # 5
CHIM = (10, 12, 1, 3)               # chimney stack x0, x1, z0, z1
LOFT_X1 = 4                         # loft floor over x 2..4

POST = "minecraft:stripped_dark_oak_log"
PLANKS = "minecraft:spruce_planks"
SIDES = ("north", "east", "south", "west")


def _pick(p, *weighted):
    names, weights = zip(*weighted)
    return p.rnd.choices(names, weights)[0]


def _stone(p, y):
    if y <= 1:
        return _pick(p, ("minecraft:cobblestone", 4), ("minecraft:mossy_cobblestone", 2),
                     ("minecraft:stone_bricks", 2), ("minecraft:cracked_stone_bricks", 1))
    return _pick(p, ("minecraft:stone_bricks", 5), ("minecraft:cobblestone", 2),
                 ("minecraft:cracked_stone_bricks", 1), ("minecraft:andesite", 1))


def _infill(p):
    return _pick(p, ("minecraft:packed_mud", 5), ("minecraft:mud_bricks", 1))


def _log(axis):
    return f"{POST}[axis={axis}]"


def _roof_y(z):
    """Height of the roof course over row z."""
    return EAVE + min(z - (Z0 - 1), (Z1 + 1) - z)


# ------------------------------------------------------------------ site and foundation
def _site(p):
    """Air over the footprint plus a one-cell margin; foundation under the building; a short
    path from the door to the street connector."""
    for x in range(0, W):
        for z in range(0, Z1 + 2):
            for y in range(1, H):
                p.set(x, y, z, AIR)
    for x in range(X0, X1 + 1):
        for z in range(Z0, Z1 + 1):
            p.set(x, 0, z, _pick(p, ("minecraft:cobblestone", 3), ("minecraft:stone", 1)))
    # path stub: a stone step under the eaves, then a cobbled path to the street edge
    for x in (DOOR_X - 1, DOOR_X, DOOR_X + 1):
        p.set(x, 0, Z1 + 1, "minecraft:stone_bricks" if x == DOOR_X else "minecraft:polished_andesite")
    for z in range(Z1 + 2, D):
        for x in (DOOR_X - 1, DOOR_X, DOOR_X + 1):
            if x == DOOR_X:
                p.set(x, 0, z, _pick(p, ("minecraft:cobblestone", 3), ("minecraft:mossy_cobblestone", 1)))
            elif p.rnd.random() < 0.5:
                p.set(x, 0, z, _pick(p, ("minecraft:gravel", 1), ("minecraft:cobblestone", 1)))
        for x in (DOOR_X - 1, DOOR_X, DOOR_X + 1):
            if p.is_set(x, 0, z):
                p.set(x, 1, z, AIR)
                p.set(x, 2, z, AIR)


# ------------------------------------------------------------------ floors
def _floors(p):
    """Shop: spruce boards in a polished andesite border with a stone-brick threshold;
    porch: worn stone with a smooth stone pad under the anvil and a scorched hearth apron."""
    for x in range(X0 + 1, SHOP_X1):
        for z in range(Z0 + 1, Z1):
            edge = x in (X0 + 1, SHOP_X1 - 1) or z in (Z0 + 1, Z1 - 1)
            p.set(x, 0, z, "minecraft:polished_andesite" if edge else PLANKS)
    for z in range(Z0 + 2, Z1 - 1):                               # boards run east-west,
        p.set(DOOR_X, 0, z, "minecraft:stripped_spruce_wood[axis=z]" if z > 5 else PLANKS)
    for x in range(SHOP_X1 + 1, X1 + 1):
        for z in range(Z0, Z1 + 1):
            p.set(x, 0, z, _pick(p, ("minecraft:cobblestone", 3), ("minecraft:stone_bricks", 3),
                                 ("minecraft:andesite", 1), ("minecraft:gravel", 1)))
    for x in (10, 11, 12):
        for z in (6, 7):
            p.set(x, 0, z, "minecraft:smooth_stone")
    for x in (10, 11, 12):
        p.set(x, 0, 4, _pick(p, ("minecraft:blackstone", 1), ("minecraft:polished_blackstone", 1)))


# ------------------------------------------------------------------ shop walls
def _shop_walls(p):
    """Stone lower walls (y 1-2), timber frame above (posts, sill and top plates, mud infill)."""
    posts_x = (X0, 4, 6, SHOP_X1)                 # posts in the long walls
    posts_z = (Z0, RIDGE_Z, Z1)                   # posts in the end walls
    for x in range(X0, SHOP_X1 + 1):
        for z in range(Z0, Z1 + 1):
            if x not in (X0, SHOP_X1) and z not in (Z0, Z1):
                continue
            corner = x in (X0, SHOP_X1) and z in (Z0, Z1)
            for y in range(1, EAVE):
                if y <= 2:
                    b = _stone(p, y)
                    if corner:
                        b = "minecraft:stone_bricks" if y == 2 else "minecraft:cobblestone"
                elif y == EAVE - 1:
                    b = _log("x" if z in (Z0, Z1) and not corner else "z" if not corner else "y")
                elif corner or (z in (Z0, Z1) and x in posts_x) or (x in (X0, SHOP_X1) and z in posts_z):
                    b = _log("y")
                else:
                    b = _infill(p)
                p.set(x, y, z, b)
    # plinth: stone brick stairs along the foot of the shop walls, outside
    for x in range(X0, SHOP_X1 + 1):
        for z, facing in ((Z0 - 1, "south"), (Z1 + 1, "north")):
            if z == Z1 + 1 and DOOR_X - 1 <= x <= DOOR_X + 1:
                continue
            p.stairs(x, 1, z, _pick(p, ("stone_bricks", 3), ("cobblestone", 2), ("mossy_cobblestone", 1)), facing)
    for z in range(Z0, Z1 + 1):
        p.stairs(X0 - 1, 1, z, _pick(p, ("stone_bricks", 3), ("cobblestone", 2), ("mossy_cobblestone", 1)), "east")
    for x, z, shape in ((X0 - 1, Z0 - 1, "outer_left"), (X0 - 1, Z1 + 1, "outer_right")):
        p.stairs(x, 1, z, "stone_bricks", "east", shape=shape)


def _gables(p):
    """West gable timber with a loft window; the shop's east wall continues up to the roof as
    a boarded partition so the shop is closed from the porch; the porch gable is boarded too."""
    for z in range(Z0, Z1 + 1):
        top = _roof_y(z)
        for y in range(EAVE, top):
            for x in (X0, SHOP_X1, X1):
                if z in (Z0, Z1):
                    continue
                if x == X1 and y == EAVE:
                    b = _log("z")                               # tie beam over the posts
                elif z == RIDGE_Z:
                    b = _log("y")                               # king post
                else:
                    b = PLANKS if x != X0 else _pick(p, (PLANKS, 3), ("minecraft:spruce_log[axis=y]", 1))
                p.set(x, y, z, b)
    # loft window in the west gable, with a stair sill and shutters
    for z in (RIDGE_Z - 1, RIDGE_Z + 1):
        p.set(X0, 7, z, AIR)
        p.pane(X0, 7, z)
        p.stairs(X0 - 1, 6, z, "spruce", "east", half="top")
    p.trapdoor(X0 - 1, 7, RIDGE_Z - 2, "spruce", "west", open=True)
    p.trapdoor(X0 - 1, 7, RIDGE_Z + 2, "spruce", "west", open=True)
    p.set(X0, 7, RIDGE_Z, _log("y"))


def _roof(p):
    """Spruce stair roof over shop and porch, ridge east-west, a slab ridge, eaves 1 out, a
    dark oak fascia under the eaves of the gable ends."""
    p.gable_roof(X0, X1, Z0, Z1, EAVE, "spruce", "x", overhang=1)
    # the chimney passes through the north slope
    cx0, cx1, cz0, cz1 = CHIM
    # gable verge: dark oak stairs down the end slopes so the ends read as trimmed
    for z in range(Z0 - 1, Z1 + 2):
        y = _roof_y(z)
        if z == RIDGE_Z:
            continue
        facing = "south" if z < RIDGE_Z else "north"
        for x in (X0 - 1, X1 + 1):
            p.stairs(x, y, z, "dark_oak", facing)
    for x in (X0 - 1, X1 + 1):
        p.slab(x, _roof_y(RIDGE_Z), RIDGE_Z, "dark_oak")
    # ridge cap: a dark oak slab line
    for x in range(X0, X1 + 1):
        p.slab(x, _roof_y(RIDGE_Z), RIDGE_Z, "dark_oak")


def _openings(p):
    """Front door under a stair hood with a hanging lantern; glazed, shuttered windows with
    stair sills; a side door to the porch; a back window."""
    p.set(DOOR_X, 1, Z1, AIR)
    p.set(DOOR_X, 2, Z1, AIR)
    p.door(DOOR_X, 1, Z1, "spruce", "north", hinge="right")
    p.set(DOOR_X, 3, Z1, _log("x"))
    for x, facing in ((DOOR_X - 1, "east"), (DOOR_X + 1, "west")):
        p.stairs(x, 4, Z1 + 1, "spruce", facing, half="top")
    p.slab(DOOR_X, 4, Z1 + 1, "spruce", type="top")
    p.hanging_lantern(DOOR_X, 3, Z1 + 1, chain=0)
    # windows: (x0, x1, wall z, outward, rows). Front ones are one row high under a log
    # lintel (the door hood sits beside them); the back one is two rows high.
    for x0, x1, z, out, rows in ((2, 3, Z1, "south", (3,)), (7, 8, Z1, "south", (3,)),
                                 (5, 5, Z0, "north", (3, 4))):
        oz = 1 if out == "south" else -1
        for x in range(x0, x1 + 1):
            for y in rows:
                p.set(x, y, z, AIR)
                p.pane(x, y, z)
            if len(rows) == 1:
                p.set(x, 4, z, _infill(p))
            p.stairs(x, 2, z + oz, "spruce", "north" if out == "south" else "south", half="top")
        for y in rows:
            p.trapdoor(x0 - 1, y, z + oz, "spruce", out, open=True)
            p.trapdoor(x1 + 1, y, z + oz, "spruce", out, open=True)
    # a flower box on the inside sill of the back window
    p.set(5, 2, Z0 + 1, "minecraft:potted_cornflower")
    # side door from the shop into the porch
    p.set(SHOP_X1, 1, 7, AIR)
    p.set(SHOP_X1, 2, 7, AIR)
    p.door(SHOP_X1, 1, 7, "spruce", "east", hinge="left")
    # a small window over the counter into the porch (iron bars, the smith's hatch)
    p.set(SHOP_X1, 3, 4, AIR)
    p.bars(SHOP_X1, 3, 4)


# ------------------------------------------------------------------ the porch
def _porch_frame(p):
    """Posts on the open east and south sides with plates at y 5; fence posts between."""
    for z in (Z0, Z1):
        for y in range(1, EAVE - 1):
            p.set(X1, y, z, _log("y"))
    p.set(X1, 1, RIDGE_Z, "minecraft:cobblestone")
    for y in range(2, EAVE - 1):
        p.fence(X1, y, RIDGE_Z, "spruce")
    for y in range(1, EAVE - 1):
        p.fence(11, y, Z1, "spruce")
    p.set(11, 1, Z1, "minecraft:cobblestone")
    for x in range(SHOP_X1 + 1, X1):                            # plates
        p.set(x, EAVE - 1, Z1, _log("x"))
        p.set(x, EAVE - 1, Z0, _log("x"))
    for z in range(Z0 + 1, Z1):
        p.set(X1, EAVE - 1, z, _log("z"))
    # knee braces (upside-down stairs) under the plates at the posts
    p.stairs(X1, 4, RIDGE_Z - 1, "spruce", "south", half="top")
    p.stairs(X1, 4, RIDGE_Z + 1, "spruce", "north", half="top")
    p.stairs(10, 4, Z1, "spruce", "east", half="top")
    p.stairs(12, 4, Z1, "spruce", "west", half="top")
    p.stairs(X1, 4, Z1 - 1, "spruce", "north", half="top")
    # tie beam across the porch, carrying a lantern
    for z in range(Z0 + 1, Z1):
        if z > CHIM[3]:
            p.set(11, EAVE, z, _log("z"))
    p.hanging_lantern(11, 4, 6, chain=1)
    # a low stone kerb on the north side east of the chimney
    p.set(X1, 1, Z0 + 1, "minecraft:cobblestone_wall")


def _chimney(p):
    """Stone stack at the back of the porch: hearth open to the south with a lit campfire, a
    flue straight up through the roof (the smoke rises out of the top), a stone hood."""
    cx0, cx1, cz0, cz1 = CHIM
    top = H - 1
    for x in range(cx0, cx1 + 1):
        for z in range(cz0, cz1 + 1):
            for y in range(1, top + 1):
                if y == top:
                    b = "minecraft:stone_brick_wall" if (x, z) != (11, 2) else AIR
                elif y == top - 1:
                    b = "minecraft:polished_andesite"
                else:
                    b = _stone(p, 1 if y <= 2 else 2)
                p.set(x, y, z, b)
    for y in range(2, top + 1):
        p.set(11, y, 2, AIR)                                    # the flue
    p.set(11, 1, 2, state("minecraft:campfire", facing="south", lit=True, signal_fire=False, waterlogged=False))
    p.set(11, 1, 3, AIR)                                        # hearth mouth
    p.set(11, 2, 3, AIR)
    p.set(11, 0, 3, "minecraft:polished_blackstone")
    p.set(11, 3, 3, "minecraft:chiseled_stone_bricks")
    for x, facing in ((10, "east"), (12, "west")):
        p.stairs(x, 3, 4, "stone_bricks", facing, half="top")  # hood corbels
    p.stairs(11, 3, 4, "stone_bricks", "north", half="top")


def _forge(p):
    """Blast furnace and furnace either side of the hearth mouth, anvil on the stone pad,
    grindstone, water trough against the shop wall, tool rack, coal and a woodpile."""
    p.set(10, 1, 4, "minecraft:blast_furnace[facing=south,lit=false]")
    p.set(12, 1, 4, "minecraft:furnace[facing=south,lit=false]")
    p.set(11, 1, 6, "minecraft:anvil[facing=east]")
    p.set(12, 1, 8, "minecraft:grindstone[face=floor,facing=north]")
    # water trough: two cauldrons against the shop wall
    p.set(10, 1, 6, "minecraft:water_cauldron[level=3]")
    p.set(10, 1, 5, "minecraft:water_cauldron[level=2]")
    # tool rack on the shop's east wall (hooks, pokers) above the trough
    for z in (5, 6):
        p.set(10, 3, z, state("minecraft:tripwire_hook", facing="east", attached=False, powered=False))
    p.set(10, 2, 8, state("minecraft:lightning_rod", facing="east", powered=False, waterlogged=False))
    p.set(10, 1, 8, "minecraft:barrel[facing=up,open=false]")
    # coal and ingots by the furnace
    p.set(12, 1, 5, "minecraft:coal_block")
    p.slab(12, 2, 5, "blackstone")
    p.set(12, 1, 7, "minecraft:spruce_trapdoor[facing=north,half=top,open=false,powered=false,waterlogged=false]")
    # woodpile against the north-east, under the eaves
    for z in (Z0, ):
        p.set(13, 1, 2, "minecraft:spruce_log[axis=x]")
        p.set(13, 2, 2, "minecraft:spruce_log[axis=x]")
        p.set(13, 1, 3, "minecraft:oak_log[axis=x]")
        p.slab(13, 2, 3, "spruce")
    p.set(14, 1, 7, "minecraft:stripped_oak_log[axis=y]")   # chopping block outside the posts


# ------------------------------------------------------------------ inside the shop
def _shop_interior(p):
    """Counter across the room with a lift-up flap, barrels and the chest behind it, display
    shelves and a smithing table on the north wall, a rug by the door, lanterns, the loft."""
    # counter across the room at z 5: plank front with a slab top, a barrel at the end,
    # and a lift-up flap (a raised trapdoor) at x 4 to walk through
    for x in range(X0 + 1, SHOP_X1):
        if x == 4:
            p.trapdoor(x, 2, 5, "spruce", "south", half="top", open=True)
            continue
        p.set(x, 1, 5, "minecraft:barrel[facing=south,open=false]" if x == 8 else PLANKS)
        p.slab(x, 2, 5, "spruce", type="bottom")
    p.set(2, 1, 5, "minecraft:spruce_planks")
    p.set(7, 2, 5, "minecraft:lantern[hanging=false,waterlogged=false]")
    p.set(6, 2, 5, state("minecraft:decorated_pot", cracked=False, facing="south", waterlogged=False))
    p.set(3, 2, 5, "minecraft:heavy_weighted_pressure_plate[power=0]")   # a scale pan
    # behind the counter: the chest, barrels, smithing table, shelves
    p.chest(8, 1, 2, "village_blacksmith", "west")
    p.barrel(8, 1, 3, facing="west")
    p.barrel(8, 2, 3, facing="up")
    p.set(7, 1, 2, "minecraft:smithing_table")
    p.set(6, 1, 2, "minecraft:stonecutter[facing=south]")
    for x in (3, 7, 8):
        p.set(x, 3, 2, state("minecraft:spruce_shelf", facing="south", powered=False,
                             side_chain="unconnected", waterlogged=False))
    p.set(3, 1, 2, "minecraft:chiseled_bookshelf[facing=south,slot_0_occupied=true,slot_1_occupied=false,"
                   "slot_2_occupied=true,slot_3_occupied=false,slot_4_occupied=false,slot_5_occupied=true]")
    p.set(4, 1, 2, "minecraft:crafting_table")
    p.set(SHOP_X1 - 1, 1, 4, "minecraft:iron_block")              # stock: an iron block, raw ore
    p.set(SHOP_X1 - 1, 2, 4, "useful_armory:colosifiteore")
    # customer side: display shelves on the west wall, a bench, a rug
    for z in (6, 7):
        p.set(2, 2, z, state("minecraft:spruce_shelf", facing="east", powered=False,
                             side_chain="unconnected", waterlogged=False))
        p.set(2, 1, z, "minecraft:barrel[facing=east,open=false]")
    p.stairs(2, 1, 8, "spruce", "west")
    p.set(2, 3, 7, "minecraft:potted_red_tulip")
    for x in (4, 5, 6):
        for z in (7, 8):
            p.carpet(x, 1, z, "red" if (x, z) != (5, 7) else "orange")
    p.set(7, 1, 8, "minecraft:potted_fern")                       # (floor pot by the door)
    # ladder up to the loft against the north wall, west end
    p.ladder_column(2, 2, 1, EAVE - 1, "south")
    # lights
    p.hanging_lantern(7, 3, 7, chain=1)
    p.wall_torch(2, 3, 4, "east")


def _loft(p):
    """Sleeping loft over the west end: board floor on a beam, fence rail, bed, a chest at
    the top of the ladder, candles."""
    y = EAVE - 1
    for x in range(X0 + 1, LOFT_X1 + 1):
        for z in range(Z0 + 1, Z1):
            if (x, z) == (2, 2):
                continue                                         # the ladder hole
            p.set(x, y, z, PLANKS if x < LOFT_X1 else _log("z"))
    for z in range(Z0 + 1, Z1):
        if z != 2:
            p.fence(LOFT_X1, y + 1, z, "spruce")
    p.fence(3, y + 1, 2, "spruce")                               # rail round the ladder hole
    p.bed(2, y + 1, 6, "red", "south")                           # head against the south wall
    p.set(3, y + 1, 8, "minecraft:white_carpet")
    p.chest(2, y + 1, 4, "village_blacksmith", "east")          # the find, up the ladder
    p.candle(3, y + 1, 5, "white", candles=2)
    p.set(3, y + 1, 3, "minecraft:spruce_trapdoor[facing=west,half=bottom,open=false,powered=false,waterlogged=false]")
    # tie beams across the open part of the shop at the plate level
    for x in (7,):
        for z in range(Z0 + 1, Z1):
            p.set(x, y, z, _log("z"))


def _outside(p):
    """Flower pots and a bench by the door, a rain barrel at the corner, a crate of ore."""
    p.set(DOOR_X - 2, 1, Z1 + 1, "minecraft:potted_red_tulip")
    p.set(DOOR_X + 2, 1, Z1 + 1, "minecraft:potted_azure_bluet")
    p.barrel(SHOP_X1, 1, Z1 + 1, facing="up")
    p.set(SHOP_X1, 2, Z1 + 1, "minecraft:spruce_trapdoor[facing=north,half=bottom,open=false,powered=false,waterlogged=false]")


def build():
    p = Piece("village/armory_blacksmith", W, H, D, "blacksmith")
    _site(p)
    _floors(p)
    _shop_walls(p)
    _gables(p)
    _roof(p)
    _chimney(p)
    _openings(p)
    _porch_frame(p)
    _forge(p)
    _shop_interior(p)
    _loft(p)
    _outside(p)
    # where a village street joins on
    p.jigsaw(DOOR_X, 0, D - 1, "south_up", "minecraft:building_entrance", "minecraft:building_entrance",
             "minecraft:empty", final_state="minecraft:cobblestone", joint="aligned")
    return p


VILLAGES = ("plains", "desert", "savanna", "snowy", "taiga")

PLACE = {
    "name": "village/armory_blacksmith",
    "pieces": {"village/armory_blacksmith": build},
    # appended to each vanilla village house pool with horizon:add_to
    "add_to": [f"minecraft:village/{v}/houses" for v in VILLAGES],
    "weight": 2,
}
