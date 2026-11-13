"""Forgotten armory: a buried arsenal (underground, Y -30 to 20, rare). Brief:
docs/design/places.md section 8.

Plan (x east, z south; one piece, 33 x 12 x 25):

    hidden |  library        | |  forge (hearth, anvils, quench)  |
    room   |  (bookshelf wall)| |                                  |
    -------+--door-----------+-+-------door------------------------+
           |  aisle   pillars of the central hall (rib-vaulted nave)  | entrance stair,
           |  trophy  ..........  guardian spawner  ...............   |== rising east, ends
           |  dais    pillars                                         | in a collapse
           +--door-----------+-+-------iron gate + bars-------------+
           |  barracks (beds, |  treasury (bullion of colosifite    |
           |  footlockers)    |  and shadow blocks)                 |

The player digs in. The central hall (x 6..26, z 7..17) has two arcades of pillars, aisles
under a flat ceiling and a stepped, ribbed vault over the nave. Four side rooms open off the
aisles; the hidden room lies behind the library's west wall of bookshelves. The old entrance
stair climbs east from the hall and is choked with rubble where the passage fell in.
Vault guardian spawners: nave centre and barracks. Loot (chests/forgotten_armory): library,
forge, treasury, hidden room.
"""
from structkit import AIR, NS, Piece, ccw, state

W, H, D = 33, 12, 25
HALL = (6, 7, 26, 17)                 # interior x0, z0, x1, z1
PILLAR_X = (8, 12, 16, 20, 24)
PILLAR_Z = (9, 15)
CZ = 12                               # nave centre line
HIDDEN = (1, 1, 4, 5)
LIBRARY = (6, 1, 14, 5)
FORGE = (17, 1, 26, 5)
BARRACKS = (6, 19, 15, 23)
TREASURY = (17, 19, 26, 23)

# masses (x0, z0, x1, z1, top y); every room is carved out of one of these
NORTH = (0, 0, 27, 6, 8)
SOUTH = (5, 18, 27, 24, 8)
NAVE_M = (4, 6, 27, 18, 11)
ENTRY = (27, 10, 32, 14, 11)
MASSES = (NAVE_M, NORTH, SOUTH, ENTRY)

GUARDIAN = f"{NS}:vault_guardian"
COLOS = f"{NS}:colosfiteblock"
SHADOW = f"{NS}:shadowblock"
COLOS_ORE = f"{NS}:colosifiteore"
SHADOW_ORE = f"{NS}:shadowore"
TABLE = "forgotten_armory"


# ------------------------------------------------------------------ helpers
def _corner(facing, side, kind):
    return f"{kind}_left" if ccw(facing) == side else f"{kind}_right"


def _in_mass(x, z):
    return any(x0 <= x <= x1 and z0 <= z <= z1 for x0, z0, x1, z1, _ in MASSES)


def _room(p, box, y0, y1):
    x0, z0, x1, z1 = box
    p.clear((x0, y0, z0, x1, y1, z1))


def _web(p, x, y, z):
    if p.get(x, y, z) == AIR:
        p.set(x, y, z, "minecraft:cobweb")


def _rubble(p):
    return p.rnd.choices(("minecraft:cobblestone", "minecraft:gravel", "minecraft:andesite",
                          "minecraft:cracked_stone_bricks", "minecraft:mossy_cobblestone", "minecraft:stone"),
                         (4, 3, 2, 2, 1, 1))[0]


def _rack(p, x0, x1, z, wall_side):
    """A weapon rack against a wall: a spruce rail, spear and sword shafts (lightning rods and
    end rods) on it, shields (open trapdoors) hung on the wall above."""
    face = {"north": "south", "south": "north", "east": "west", "west": "east"}[wall_side]
    for i, x in enumerate(range(x0, x1 + 1)):
        p.fence(x, 2, z, "spruce")
        p.set(x, 3, z, "minecraft:lightning_rod[facing=up,powered=false,waterlogged=false]" if i % 2 == 0
              else "minecraft:end_rod[facing=up]")
        p.trapdoor(x, 4, z, "spruce" if i % 2 else "dark_oak", face, open=True)


def _rack_x(p, x, z0, z1, wall_side):
    face = {"east": "west", "west": "east"}[wall_side]
    for i, z in enumerate(range(z0, z1 + 1)):
        p.fence(x, 2, z, "spruce")
        p.set(x, 3, z, "minecraft:lightning_rod[facing=up,powered=false,waterlogged=false]" if i % 2 == 0
              else "minecraft:end_rod[facing=up]")
        p.trapdoor(x, 4, z, "spruce" if i % 2 else "dark_oak", face, open=True)


def _beams(p, box, y, axis_z=True, every=3, wood="spruce"):
    x0, z0, x1, z1 = box
    if axis_z:
        for x in range(x0 + 1, x1, every):
            for z in range(z0, z1 + 1):
                p.log(x, y, z, wood, axis="z", stripped=True)
    else:
        for z in range(z0 + 1, z1, every):
            for x in range(x0, x1 + 1):
                p.log(x, y, z, wood, axis="x", stripped=True)


def build():
    p = Piece("forgotten_armory", W, H, D, "armory")
    masonry = p.mix(("minecraft:stone_bricks", 8), ("minecraft:cracked_stone_bricks", 3),
                    ("minecraft:mossy_stone_bricks", 2), ("minecraft:stone", 1), ("minecraft:andesite", 1),
                    ("minecraft:cobblestone", 1), (COLOS_ORE, 0.12), (SHADOW_ORE, 0.08))
    for x0, z0, x1, z1, top in MASSES:
        p.fill(x0, 0, z0, x1, top, z1, masonry)
    _exterior(p)
    _hall(p)
    _library(p)
    _hidden_room(p)
    _forge(p)
    _barracks(p)
    _treasury(p)
    _entrance(p)
    _age(p)
    return p


# ------------------------------------------------------------------ outside
def _exterior(p):
    """Stair plinth at the foot and a cornice at the top of every exposed mass face."""
    for x0, z0, x1, z1, top in MASSES:
        for side, (dx, dz) in (("west", (-1, 0)), ("east", (1, 0)), ("north", (0, -1)), ("south", (0, 1))):
            facing = {"west": "east", "east": "west", "north": "south", "south": "north"}[side]
            if dx:
                cells = [(x0 - 1 if dx < 0 else x1 + 1, z) for z in range(z0, z1 + 1)]
            else:
                cells = [(x, z0 - 1 if dz < 0 else z1 + 1) for x in range(x0, x1 + 1)]
            for x, z in cells:
                if _in_mass(x, z):
                    continue
                for y, half in ((0, "bottom"), (top, "top")):
                    if p.in_bounds(x, y, z) and not p.is_set(x, y, z):
                        p.stairs(x, y, z, "stone_bricks", facing, half=half)


# ------------------------------------------------------------------ central hall
def _hall(p):
    x0, z0, x1, z1 = HALL
    _room(p, HALL, 2, 6)
    _hall_floor(p)
    _vault(p)
    _arcades(p)
    _hall_walls(p)
    _trophy_dais(p)
    p.spawner(16, 2, CZ, GUARDIAN)


def _hall_floor(p):
    x0, z0, x1, z1 = HALL
    aisle = p.mix(("minecraft:stone_bricks", 5), ("minecraft:cracked_stone_bricks", 3),
                  ("minecraft:mossy_stone_bricks", 1), ("minecraft:andesite", 1))
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            if x in (x0, x1) or z in (z0, z1):
                b = "minecraft:polished_andesite"
            elif z in (10, 14):
                b = "minecraft:polished_andesite"
            elif 11 <= z <= 13:
                b = "minecraft:chiseled_stone_bricks" if x in PILLAR_X and z == CZ else \
                    p.rnd.choices(("minecraft:tuff_bricks", "minecraft:stone_bricks", "minecraft:cracked_stone_bricks"),
                                  (4, 2, 1))[0]
            else:
                b = aisle
            p.set(x, 1, z, b)
    # centre motif round the spawner: a shadow block under it, colosifite corners
    for dx in (-1, 0, 1):
        for dz in (-1, 0, 1):
            p.set(16 + dx, 1, CZ + dz, SHADOW if not (dx or dz) else COLOS if dx and dz
                  else "minecraft:chiseled_stone_bricks")
    for dx, dz in ((-2, 0), (2, 0), (0, -2), (0, 2)):
        p.set(16 + dx, 1, CZ + dz, SHADOW_ORE)
    # a worn red runner down the nave, missing in places
    for x in range(8, 26):
        if abs(x - 16) <= 1 or p.rnd.random() < 0.2:
            continue
        p.carpet(x, 2, CZ, "red")


def _vault(p):
    """Nave z 10..14: two courses of upside-down stairs step in from the arcade walls to a
    one-wide ridge two high; ribs of polished andesite over every pillar pair with a keystone
    and a hanging soul lantern; glowing shadow ore set in the ridge between the ribs."""
    x0, _, x1, _ = HALL
    for x in range(x0, x1 + 1):
        rib = x in PILLAR_X
        mat = "polished_andesite" if rib else "stone_bricks"
        p.clear((x, 7, 11, x, 7, 13))
        p.stairs(x, 7, 10, mat, "north", half="top")
        p.stairs(x, 7, 14, mat, "south", half="top")
        p.stairs(x, 8, 11, mat, "north", half="top")
        p.stairs(x, 8, 13, mat, "south", half="top")
        p.set(x, 8, CZ, AIR)
        p.set(x, 9, CZ, AIR)
        if rib:
            p.set(x, 10, CZ, "minecraft:chiseled_stone_bricks")
            p.hanging_lantern(x, 8, CZ, chain=1, soul=True)
        elif x % 4 == 2:
            p.set(x, 10, CZ, SHADOW_ORE)
    # end walls of the vault get a stepped gable trim
    for x, f in ((x0, "west"), (x1, "east")):
        p.stairs(x, 9, CZ, "stone_bricks", f, half="top")


def _arcades(p):
    """Pillars with stair bases and capitals; arches between them at y 6; the aisles have a
    flat ceiling at y 7 with a cornice along the outer wall."""
    x0, z0, x1, z1 = HALL
    for pz in PILLAR_Z:
        for x in range(x0, x1 + 1):
            if x in PILLAR_X:
                p.set(x, 2, pz, "minecraft:chiseled_stone_bricks")
                p.fill(x, 3, pz, x, 5, pz, "minecraft:polished_andesite")
                p.set(x, 6, pz, "minecraft:chiseled_stone_bricks")
                for d, (dx, dz) in (("west", (1, 0)), ("east", (-1, 0)), ("north", (0, 1)), ("south", (0, -1))):
                    p.stairs(x + dx, 2, pz + dz, "stone_bricks", d)
                continue
            west = (x - 1) in PILLAR_X or x - 1 < x0
            east = (x + 1) in PILLAR_X or x + 1 > x1
            if west:
                p.stairs(x, 6, pz, "stone_bricks", "west", half="top")
            elif east:
                p.stairs(x, 6, pz, "stone_bricks", "east", half="top")
            else:
                p.set(x, 6, pz, AIR)
    for x in range(x0, x1 + 1):
        for z, f in ((z0, "north"), (z1, "south")):
            if x in (x0, x1):
                side = "west" if x == x0 else "east"
                p.stairs(x, 6, z, "stone_bricks", f, half="top", shape=_corner(f, side, "inner"))
            else:
                p.stairs(x, 6, z, "stone_bricks", f, half="top")
    for z in range(z0 + 1, z1):
        if z in PILLAR_Z or 10 <= z <= 14:
            continue
        p.stairs(x0, 6, z, "stone_bricks", "west", half="top")
        p.stairs(x1, 6, z, "stone_bricks", "east", half="top")
    # soul torches on the aisle faces of the pillars
    for x in PILLAR_X:
        p.wall_torch(x, 4, 8, "north", soul=True)
        p.wall_torch(x, 4, 16, "south", soul=True)


def _banner(p, x, wall_z, colours):
    """A wool hanging from the cornice in front of the wall at wall_z: two cells of cloth
    with a coloured tip, clear of the floor so the aisle stays passable; a chiseled bracket
    in the wall above it."""
    top, mid, tip = colours
    z = wall_z + 1 if wall_z == HALL[1] - 1 else wall_z - 1
    p.set(x, 6, wall_z, "minecraft:chiseled_stone_bricks")
    p.set(x, 5, z, f"minecraft:{top}_wool")
    p.set(x, 4, z, f"minecraft:{mid}_wool")
    p.set(x, 3, z, f"minecraft:{tip}_wool")


def _hall_walls(p):
    """Doors to the side rooms, banners and weapon racks along the aisles, the treasury's
    barred front and iron gate."""
    # doorways
    for x, wz in ((10, 6), (10, 18)):
        p.door(x, 2, wz, "spruce", "north" if wz == 6 else "south", hinge="left")
        p.set(x, 4, wz, "minecraft:chiseled_stone_bricks")
        p.set(x, 1, wz, "minecraft:polished_andesite")
    # forge: an open arch, two wide
    for x in (21, 22):
        p.set(x, 1, 6, "minecraft:polished_andesite")
        p.clear((x, 2, 6, x, 4, 6))
    p.stairs(21, 4, 6, "stone_bricks", "west", half="top")
    p.stairs(22, 4, 6, "stone_bricks", "east", half="top")
    # treasury front: iron bars either side of an iron door opened by a lever
    for x in (18, 19, 20, 24, 25):
        for y in range(2, 6):
            p.bars(x, y, 18)
    p.set(22, 1, 18, "minecraft:polished_andesite")
    p.set(22, 2, 18, "minecraft:iron_door[facing=south,half=lower,hinge=left,open=false,powered=false]")
    p.set(22, 3, 18, "minecraft:iron_door[facing=south,half=upper,hinge=left,open=false,powered=false]")
    p.set(22, 4, 18, "minecraft:chiseled_stone_bricks")
    for x in (21, 23):
        p.fill(x, 2, 18, x, 5, 18, "minecraft:polished_andesite")
    p.set(23, 3, 17, "minecraft:lever[face=wall,facing=north,powered=false]")
    # banners of coloured wool
    for x, wz, c in ((7, 6, ("red", "red", "yellow")), (14, 6, ("blue", "blue", "white")),
                     (18, 6, ("green", "green", "yellow")), (25, 6, ("black", "red", "red")),
                     (7, 18, ("blue", "blue", "white")), (14, 18, ("red", "red", "yellow"))):
        _banner(p, x, wz, c)
    # weapon racks against the aisle walls, anvils between them
    _rack(p, 12, 13, 7, "north")
    _rack(p, 16, 17, 7, "north")
    _rack(p, 12, 13, 17, "south")
    _rack(p, 15, 16, 17, "south")
    p.set(19, 2, 7, "minecraft:anvil[facing=east]")
    p.set(17, 2, 17, "minecraft:chipped_anvil[facing=west]")
    p.set(8, 2, 17, "minecraft:damaged_anvil[facing=east]")
    p.set(26, 2, 7, "minecraft:barrel[facing=up,open=false]")
    p.set(26, 3, 7, "minecraft:barrel[facing=west,open=false]")
    p.set(25, 2, 7, "minecraft:barrel[facing=north,open=false]")
    p.candle(19, 3, 7, "white", candles=2)


def _trophy_dais(p):
    """West end: a step up to a dais under a great tapestry, a blade (lightning rod) driven
    into a colosifite block, two anvils and candles."""
    for z in range(10, 15):
        p.set(6, 2, z, "minecraft:polished_andesite")
        p.stairs(7, 2, z, "stone_bricks", "west")
    p.stairs(7, 2, 10, "stone_bricks", "west", shape="outer_right")
    p.stairs(7, 2, 14, "stone_bricks", "west", shape="outer_left")
    p.set(6, 3, CZ, COLOS)
    p.set(6, 4, CZ, "minecraft:lightning_rod[facing=up,powered=false,waterlogged=false]")
    p.set(6, 3, 11, "minecraft:anvil[facing=north]")
    p.set(6, 3, 13, "minecraft:anvil[facing=south]")
    p.candle(6, 3, 10, "yellow", candles=3)
    p.candle(6, 3, 14, "yellow", candles=3)
    # tapestry in the west wall: yellow border, red field, a colosifite boss
    for y in range(2, 9):
        for z in range(10, 15):
            border = y in (2, 8) or z in (10, 14)
            p.set(5, y, z, "minecraft:yellow_wool" if border else "minecraft:red_wool")
    p.set(5, 5, CZ, COLOS)
    p.set(5, 6, CZ, "minecraft:black_wool")
    p.set(5, 4, CZ, "minecraft:black_wool")
    p.set(5, 9, CZ, "minecraft:chiseled_stone_bricks")


# ------------------------------------------------------------------ library
def _library(p):
    x0, z0, x1, z1 = LIBRARY
    _room(p, LIBRARY, 2, 6)
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            if x in (x0, x1) or z in (z0, z1):
                b = "minecraft:polished_andesite"
            else:
                b = "minecraft:dark_oak_planks" if (x + z) % 2 else "minecraft:spruce_planks"
            p.set(x, 1, z, b)
    _beams(p, LIBRARY, 6, axis_z=True, every=4, wood="dark_oak")
    shelf = lambda f: p.rnd.choice(("minecraft:bookshelf", "minecraft:bookshelf", (  # noqa: E731
        f"minecraft:chiseled_bookshelf[facing={f},slot_0_occupied=false,slot_1_occupied=false,"
        f"slot_2_occupied=false,slot_3_occupied=false,slot_4_occupied=false,slot_5_occupied=false]")))
    # north wall: shelves to y 4, candles on top
    for x in range(x0, x1 + 1):
        for y in range(2, 5):
            p.set(x, y, z0, shelf("south"))
        if x in (7, 10, 13):
            p.candle(x, 5, z0, "white", candles=1 + x % 3)
        else:
            p.slab(x, 5, z0, "spruce")
    # east wall: shelves
    for z in range(z0 + 1, z0 + 3):
        for y in range(2, 5):
            p.set(x1, y, z, shelf("west"))
    # west wall is the false wall: plain shelves in front of the hidden room
    for z in range(z0, z1 + 1):
        for y in range(2, 5):
            p.set(5, y, z, "minecraft:bookshelf")
        p.set(5, 5, z, "minecraft:spruce_planks")
    # reading desks with stools, a lectern, a rug
    for x in (7, 8):
        p.fence(x, 2, 3, "spruce")
        p.set(x, 3, 3, "minecraft:spruce_pressure_plate[powered=false]")
        p.stairs(x, 2, 4, "spruce", "south")
    p.set(11, 2, 3, "minecraft:lectern[facing=south,has_book=false,powered=false]")
    for x in range(10, 13):
        for z in (2, 4):
            p.carpet(x, 2, z, "brown")
    p.carpet(10, 2, 3, "red")
    p.carpet(12, 2, 3, "red")
    p.chest(x1, 2, z1, TABLE, "west")
    p.barrel(x1, 2, z1 - 1, "west")
    p.candle(x1, 3, z1 - 1, "white", candles=2)
    p.hanging_lantern(7, 5, 3, chain=0)
    p.hanging_lantern(11, 5, 3, chain=0)
    # scattered books: a cobweb or two, a fallen shelf
    p.set(6, 2, 5, "minecraft:bookshelf")
    p.slab(6, 3, 5, "spruce")
    p.candle(6, 2, 3, None, candles=1, lit=False)       # the draught: a candle by the false wall


# ------------------------------------------------------------------ hidden room
def _hidden_room(p):
    """Behind the library's west shelves: dark, webbed, a skeleton slumped by the last cache."""
    x0, z0, x1, z1 = HIDDEN
    _room(p, HIDDEN, 2, 5)
    floor = p.mix(("minecraft:cobblestone", 3), ("minecraft:mossy_cobblestone", 2), ("minecraft:gravel", 1),
                  ("minecraft:stone_bricks", 2))
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            p.set(x, 1, z, floor)
    p.set(x0, 2, 3, "minecraft:chiseled_stone_bricks")
    p.chest(x0 + 1, 2, 3, TABLE, "east")
    p.set(x0, 2, 2, COLOS)
    p.set(x0, 2, 4, SHADOW)
    p.set(x0, 3, 2, COLOS_ORE)
    p.set(0, 4, 4, COLOS_ORE)
    p.set(2, 6, 1, SHADOW_ORE)
    p.set(3, 2, 5, "minecraft:bone_block[axis=x]")
    p.set(4, 2, 5, "minecraft:skeleton_skull[powered=false,rotation=6]")
    p.set(3, 2, 1, "minecraft:candle[candles=3,lit=false,waterlogged=false]")
    p.set(4, 2, 1, "minecraft:decorated_pot[cracked=true,facing=south,waterlogged=false]")
    for x, y, z in ((1, 5, 1), (4, 5, 1), (1, 5, 5), (4, 5, 5), (2, 5, 3), (1, 4, 1)):
        _web(p, x, y, z)


# ------------------------------------------------------------------ forge
def _forge(p):
    x0, z0, x1, z1 = FORGE
    _room(p, FORGE, 2, 6)
    floor = p.mix(("minecraft:cobblestone", 3), ("minecraft:stone", 2), ("minecraft:andesite", 2),
                  ("minecraft:tuff", 2), ("minecraft:cobbled_deepslate", 1))
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            p.set(x, 1, z, floor)
    _beams(p, FORGE, 6, axis_z=True, every=3, wood="dark_oak")
    # hearth on the north wall: blast furnaces either side of a magma bed and fire, a hood
    for x in range(21, 24):
        p.set(x, 1, z0, "minecraft:magma_block")
    p.set(22, 2, z0, "minecraft:campfire[facing=south,lit=true,signal_fire=false,waterlogged=false]")
    p.set(21, 2, z0, "minecraft:coal_block")
    p.set(23, 2, z0, "minecraft:coal_block")
    for x in (20, 24):
        p.set(x, 2, z0, f"minecraft:blast_furnace[facing=south,lit={'true' if x == 20 else 'false'}]")
        p.set(x, 3, z0, "minecraft:polished_andesite")
    for x in range(20, 25):
        p.stairs(x, 4, z0 + 1, "stone_bricks", "north", half="top")
        p.fill(x, 5, z0, x, 6, z0 + 1, "minecraft:bricks")
    p.stairs(19, 5, z0 + 1, "brick", "east", half="top")
    p.stairs(25, 5, z0 + 1, "brick", "west", half="top")
    # bellows: a barrel and a trapdoor flap
    p.barrel(19, 2, z0, "east")
    p.trapdoor(19, 3, z0, "spruce", "east", half="bottom")
    # quench trough, anvils, grindstone and smithing table
    p.set(17, 2, z0, "minecraft:water_cauldron[level=3]")
    p.set(18, 2, z0, "minecraft:water_cauldron[level=2]")
    p.set(17, 2, z0 + 1, "minecraft:cauldron")
    p.set(21, 2, 3, "minecraft:anvil[facing=east]")
    p.set(23, 2, 3, "minecraft:chipped_anvil[facing=east]")
    p.set(x1, 2, z0, "minecraft:smithing_table")
    p.set(x1, 2, z0 + 1, "minecraft:grindstone[face=floor,facing=west]")
    p.set(x1 - 1, 2, z0, "minecraft:stonecutter[facing=south]")
    # tool wall on the east wall: hooks and hung trapdoors
    for z in (3, 4):
        p.set(x1, 4, z, "minecraft:tripwire_hook[attached=false,facing=west,powered=false]")
        p.trapdoor(x1, 3, z, "spruce", "west", open=True)
    # coal heap and ingot stacks, colosifite half sunk in the floor
    p.set(17, 2, z1, "minecraft:coal_block")
    p.set(18, 2, z1, "minecraft:coal_block")
    p.set(17, 3, z1, "minecraft:coal_block")
    p.slab(17, 2, z1 - 1, "cobblestone")
    p.set(x1, 1, z1, COLOS)
    p.set(x1 - 1, 1, z1, COLOS_ORE)
    p.set(x1, 2, z1, "minecraft:iron_block")
    p.set(x1 - 1, 2, z1, COLOS_ORE)
    p.chest(19, 2, z1, TABLE, "north")
    p.hanging_lantern(18, 5, 3, chain=0)
    p.hanging_lantern(24, 5, 3, chain=0)


# ------------------------------------------------------------------ barracks
def _barracks(p):
    """Beds along the south wall, a footlocker at each foot, a rack and a table, guardians."""
    x0, z0, x1, z1 = BARRACKS
    _room(p, BARRACKS, 2, 6)
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            edge = x in (x0, x1) or z in (z0, z1)
            p.set(x, 1, z, "minecraft:stone_bricks" if edge else
                  p.rnd.choice(("minecraft:spruce_planks", "minecraft:spruce_planks", "minecraft:stripped_spruce_wood[axis=x]")))
    _beams(p, BARRACKS, 6, axis_z=True, every=3)
    for x, colour in ((6, "blue"), (8, "blue"), (12, "red"), (14, "blue")):
        p.bed(x, 2, z1 - 1, colour, "south")
        p.set(x, 2, z1 - 2, "minecraft:chest[facing=north,type=single,waterlogged=false]")
    # rack and table between the bed pairs
    _rack(p, 9, 11, z1, "south")
    p.fence(10, 2, 21, "spruce")
    p.set(10, 3, 21, "minecraft:spruce_pressure_plate[powered=false]")
    p.stairs(9, 2, 21, "spruce", "west")
    p.stairs(11, 2, 21, "spruce", "east")
    p.set(x1, 2, z0, "minecraft:barrel[facing=up,open=false]")
    p.set(x1, 3, z0, "minecraft:barrel[facing=west,open=false]")
    p.set(x0, 2, z0, "minecraft:barrel[facing=up,open=false]")
    p.spawner(12, 2, 20, GUARDIAN)
    p.hanging_lantern(7, 5, 20, chain=0, soul=True)
    p.hanging_lantern(13, 5, 21, chain=0, soul=True)
    p.carpet(7, 2, 22, "gray")
    p.carpet(13, 2, 22, "gray")


# ------------------------------------------------------------------ treasury
def _treasury(p):
    """Behind the bars: bullion of colosifite and shadow blocks stacked in pyramids, ore
    sacks, the treasure chest on a step at the back between candles."""
    x0, z0, x1, z1 = TREASURY
    _room(p, TREASURY, 2, 6)
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            edge = x in (x0, x1) or z in (z0, z1)
            p.set(x, 1, z, "minecraft:polished_andesite" if edge else
                  "minecraft:chiseled_stone_bricks" if (x + z) % 4 == 0 else "minecraft:stone_bricks")
    # bullion pyramids in the four corners
    for cx, cz in ((x0, z1), (x1, z1), (x0, z0 + 1), (x1, z0 + 1)):
        sx = 1 if cx == x0 else -1
        sz = -1 if cz == z1 else 1
        stack = ((0, 0, 3), (sx, 0, 2), (0, sz, 2), (sx, sz, 1), (2 * sx, 0, 1))
        for dx, dz, h in stack:
            for y in range(2, 2 + h):
                p.set(cx + dx, y, cz + dz, COLOS if (y + dx + dz) % 2 == 0 else SHADOW)
    p.set(20, 2, 22, COLOS_ORE)
    p.set(24, 2, 22, SHADOW_ORE)
    # the chest on a step at the back
    p.set(22, 2, z1, "minecraft:chiseled_stone_bricks")
    p.stairs(22, 2, z1 - 1, "polished_andesite", "south")
    p.chest(22, 3, z1, TABLE, "north")
    p.set(21, 2, z1, "minecraft:polished_andesite")
    p.set(23, 2, z1, "minecraft:polished_andesite")
    p.candle(21, 3, z1, "yellow", candles=4)
    p.candle(23, 3, z1, "yellow", candles=4)
    p.hanging_lantern(22, 5, 21, chain=1, soul=True)
    p.set(22, 7, 21, SHADOW_ORE)


# ------------------------------------------------------------------ entrance
def _entrance(p):
    """An arch in the hall's east wall, then a stair climbing east that is choked with the
    rubble of the fallen passage before it reaches daylight."""
    # arch
    p.clear((27, 2, 11, 27, 4, 13))
    p.set(27, 5, CZ, AIR)
    p.stairs(27, 5, 11, "stone_bricks", "north", half="top")
    p.stairs(27, 5, 13, "stone_bricks", "south", half="top")
    for z in (11, 12, 13):
        p.set(27, 1, z, "minecraft:polished_andesite")
    p.set(27, 6, CZ, "minecraft:chiseled_stone_bricks")
    # stair, stepped ceiling
    for i, x in enumerate(range(28, 33)):
        y = 2 + i
        for z in (11, 12, 13):
            p.fill(x, 1, z, x, y - 1, z, "minecraft:stone_bricks")
            p.stairs(x, y, z, "stone_bricks" if z == CZ else "cobblestone", "east")
            p.clear((x, y + 1, z, x, y + 3, z))
            p.stairs(x, y + 4, z, "stone_bricks", "west", half="top")
    p.wall_torch(28, 5, 11, "south")
    p.wall_torch(28, 5, 13, "north")
    # the collapse: rubble fills the top of the stair and slumps down it
    for z in (11, 12, 13):
        p.fill(32, 6, z, 32, 10, z, lambda: _rubble(p))
        top31 = 8 + (z == CZ)
        p.fill(31, 6, z, 31, top31, z, lambda: _rubble(p))
        if z != 13:
            p.set(30, 5, z, _rubble(p))
        p.slab(30, 6 if z != 13 else 5, z, "cobblestone")
    p.slab(29, 4, 11, "cobblestone")
    p.set(29, 4, 12, "minecraft:gravel")
    p.stairs(28, 3, 13, "cobblestone", "east")
    p.set(30, 7, 11, "minecraft:hanging_roots[waterlogged=false]")


# ------------------------------------------------------------------ age
def _age(p):
    """Cobwebs high in the vault and the room corners, moss creeping over the aisle floors,
    a heap of fallen vault stones in the south-east aisle."""
    rnd = p.rnd
    x0, z0, x1, z1 = HALL
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            for y in (5, 6, 7, 8, 9):
                if p.get(x, y, z) == AIR and rnd.random() < (0.015 if y < 7 else 0.035):
                    p.set(x, y, z, "minecraft:cobweb")
            if p.get(x, 2, z) == AIR and p.get(x, 1, z) not in (None, AIR) and rnd.random() < 0.06 \
                    and not (14 <= x <= 18 and 10 <= z <= 14):
                p.set(x, 2, z, "minecraft:moss_carpet")
    for box in (LIBRARY, FORGE, BARRACKS, TREASURY):
        bx0, bz0, bx1, bz1 = box
        for x, z in ((bx0, bz0), (bx1, bz0), (bx0, bz1), (bx1, bz1)):
            _web(p, x, 6, z)
    _web(p, 6, 6, 7)
    _web(p, 26, 6, 17)
    _web(p, 9, 5, 7)
    # a fallen patch of vault: one rib course missing, rubble on the floor below
    for x in (25, 26):
        p.set(x, 8, 13, AIR)
        p.set(x, 7, 14, AIR)
    for x, z, h in ((25, 16, 2), (26, 16, 1), (26, 15, 1), (24, 16, 1), (25, 17, 1)):
        for y in range(2, 2 + h):
            p.set(x, y, z, _rubble(p))
        p.slab(x, 2 + h, z, "cobblestone")
    p.set(25, 2, 14, "minecraft:cobblestone")
    p.slab(26, 2, 13, "stone_brick")
    # glow lichen in the damp corner by the collapse and on the corridor
    for x, y, z, side in ((26, 3, 17, "east"), (26, 4, 16, "east"), (29, 6, 13, "south")):
        if p.get(x, y, z) == AIR:
            p.set(x, y, z, state("minecraft:glow_lichen", down=False, up=False, waterlogged=False,
                                 **{d: d == side for d in ("north", "east", "south", "west")}))


PLACE = {
    "name": "forgotten_armory",
    "pieces": {"forgotten_armory": build},
    "step": "underground_structures",
    "start_height": (-30, 20),
    "surface": False,
    "terrain": "none",
    "biomes": [
        "#minecraft:is_overworld",
    ],
    "spacing": 40,
    "separation": 14,
    "salt": 418200108,
}
