"""Wanderer's camp: travellers' tents round a fire (surface). Brief: docs/design/places.md section 2.

Layout (x east, z south), all around the fire ring at (17, 16):
  * four sleeping tents of different cloth facing the fire (red north, blue east, green south,
    yellow west) and a larger supply tent to the north-east;
  * a covered wagon to the south-east with a hitching rail, hay and a trough beside it;
  * a cooking spot (pot over a campfire, smoker, food) to the north-west;
  * a lookout platform on log stilts with a ladder, a small roof and a bell (far north-west);
  * a broken log palisade along the west side, lantern posts, a drying rack, trodden paths.
The trodden ground covers the middle; the outer ring keeps the world's own surface, so the
camp sits in forest, taiga, savanna, plains, snow or desert alike.
Loot (chests/wanderers_camp): a barrel in the supply tent and a chest tucked in the wagon.
"""
from structkit import AIR, Piece, state

W, H, D = 35, 13, 33
FX, FZ = 17, 16                       # the fire
SIDES = ("north", "east", "south", "west")


def _pick(p, *weighted):
    names, weights = zip(*weighted)
    return p.rnd.choices(names, weights)[0]


def _trodden(p):
    return _pick(p, ("minecraft:coarse_dirt", 5), ("minecraft:dirt", 2), ("minecraft:dirt_path", 1),
                 ("minecraft:gravel", 1), ("minecraft:rooted_dirt", 1))


# ------------------------------------------------------------------ the site
def _site(p):
    """Air over a rounded site; trodden earth in the middle, the world's surface round it."""
    cx, cz = (W - 1) / 2, (D - 1) / 2
    for x in range(W):
        for z in range(D):
            r = ((x - cx) / (W / 2)) ** 4 + ((z - cz) / (D / 2)) ** 4
            if r > 0.92 + p.rnd.uniform(-0.06, 0.06):
                continue
            for y in range(1, H):
                p.set(x, y, z, AIR)
            inner = ((x - FX) / 11) ** 2 + ((z - FZ) / 10) ** 2
            if inner < 1 + p.rnd.uniform(-0.25, 0.1):
                p.set(x, 0, z, _trodden(p))


def _path(p, a, b):
    """A one-wide trodden path from a to b (x, z), with ragged path blocks."""
    (x0, z0), (x1, z1) = a, b
    n = max(abs(x1 - x0), abs(z1 - z0))
    for i in range(n + 1):
        x = round(x0 + (x1 - x0) * i / n)
        z = round(z0 + (z1 - z0) * i / n)
        p.set(x, 0, z, "minecraft:dirt_path" if p.rnd.random() < 0.75 else "minecraft:coarse_dirt")


def _paths(p):
    _path(p, (FX, 13), (FX, 9))                 # red tent
    _path(p, (19, 13), (26, 10))                # supply tent
    _path(p, (20, FZ), (25, FZ))                # blue tent
    _path(p, (14, FZ), (10, FZ))                # yellow tent
    _path(p, (15, 19), (11, 21))                # green tent
    _path(p, (19, 19), (21, 24))                # wagon
    _path(p, (FX, 19), (FX + 1, D - 1))          # the trail in from the south
    _path(p, (FX + 1, 22), (FX + 2, D - 1))


# ------------------------------------------------------------------ fire and seats
def _fire(p):
    """Campfire in a pit of ash and gravel, ringed by low stones; logs, benches and stumps."""
    for dx in range(-2, 3):
        for dz in range(-2, 3):
            x, z = FX + dx, FZ + dz
            if abs(dx) == 2 and abs(dz) == 2:
                continue
            if max(abs(dx), abs(dz)) == 2:
                p.set(x, 0, z, "minecraft:cobblestone")
                roll = p.rnd.random()
                if roll < 0.45:
                    p.slab(x, 1, z, p.rnd.choice(("cobblestone", "mossy_cobblestone", "stone")))
                elif roll < 0.75:
                    out = "south" if dz == 2 else "north" if dz == -2 else "east" if dx == 2 else "west"
                    p.stairs(x, 1, z, p.rnd.choice(("cobblestone", "stone", "mossy_cobblestone")), out)
                else:
                    p.set(x, 1, z, p.rnd.choice(("minecraft:cobblestone", "minecraft:andesite",
                                                 "minecraft:mossy_cobblestone")))
            else:
                p.set(x, 0, z, _pick(p, ("minecraft:gravel", 2), ("minecraft:coarse_dirt", 1),
                                     ("minecraft:cobblestone", 1)))
    p.set(FX, 0, FZ, "minecraft:cobblestone")
    p.set(FX, 1, FZ, state("minecraft:campfire", facing="north", lit=True, signal_fire=False,
                           waterlogged=False))
    # seats on the diagonals, leaving the paths free: logs to the west, plank benches east
    for x in (14, 15):
        p.set(x, 1, 12, "minecraft:spruce_log[axis=x]")
        p.set(x, 1, 20, "minecraft:oak_log[axis=x]")
    for x in (19, 20):
        p.stairs(x, 1, 12, "spruce", "north")
        p.stairs(x, 1, 20, "spruce", "south")
    for x, z in ((13, 13), (13, 19), (21, 13), (21, 19)):
        p.set(x, 1, z, "minecraft:stripped_spruce_log[axis=y]")             # stumps
    p.set(13, 2, 19, "minecraft:lantern[hanging=false,waterlogged=false]")
    # a stack of firewood by the ring
    for z in (FZ - 1, FZ, FZ + 1):
        p.set(FX + 4, 1, z, "minecraft:oak_log[axis=z]" if z != FZ else "minecraft:birch_log[axis=z]")
    p.set(FX + 4, 2, FZ, "minecraft:spruce_log[axis=z]")


# ------------------------------------------------------------------ tents
def _tent(name, hw, length, cloth, trim, patch, carpet, kind):
    """One tent as its own piece, entrance to the south (+z), its pole at z = 0 and a porch
    awning on two poles at z = length + 1. hw is the half width; the cloth rises in two
    upright courses then steps in to a ridge."""
    t = Piece(name, 2 * hw + 1, hw + 3, length + 2, name)
    ridge = hw + 2

    def off(y):
        return hw if y <= 2 else hw - (y - 2)

    for z in range(1, length + 1):
        for y in range(1, ridge + 1):
            for x in (hw - off(y), hw + off(y)):
                b = trim if y in (1, ridge) else cloth
                if b == cloth and t.rnd.random() < 0.06:
                    b = patch                                  # a mended patch
                t.set(x, y, z, b)
            if z == 1:                                         # closed back
                for x in range(hw - off(y) + 1, hw + off(y)):
                    t.set(x, y, z, cloth)
    for y in range(1, ridge + 1):                             # tent pole behind the back
        t.fence(hw, y, 0, "spruce")
    for y in range(3, ridge + 1):                             # porch awning on two poles
        for x in {hw - off(y), hw + off(y)}:
            t.set(x, y, length + 1, trim if y == ridge else cloth)
    for x in (hw - off(3), hw + off(3)):
        for y in (1, 2):
            t.fence(x, y, length + 1, "spruce")
    t.set(hw - 1, 1, length, cloth)                           # a flap pinned across the door
    t.set(hw - 1, 2, length, cloth)
    if kind == "supply":
        _supply_inside(t, hw, length)
    else:
        _sleeping_inside(t, hw, length, kind)
    for z in range(2, length + 1):                            # carpet over whatever floor is free
        for x in range(hw - off(1) + 1, hw + off(1)):
            if not t.is_set(x, 1, z):
                t.carpet(x, 1, z, carpet)
    return t


def _sleeping_inside(t, hw, length, kind):
    """A bed against one side, a pack barrel with a lantern, and the owner's trade."""
    bed, owner = kind
    t.bed(hw + 1, 1, 3, bed, "north")                         # head against the back
    t.barrel(hw - 1, 1, 2, facing="up")
    t.lantern(hw - 1, 2, 2)
    t.set(hw - 1, 1, length - 1, owner)


def _supply_inside(t, hw, length):
    """Barrels down one side (one holds the loot), crates, hay and cloth down the other."""
    left, right = hw - 2, hw + 2
    for z in range(2, length - 1):
        if z == 4:
            t.chest(left, 1, z, "wanderers_camp", "east", block="minecraft:barrel")
        else:
            t.barrel(left, 1, z, facing="up" if z % 2 else "east")
        if z in (2, 3, 5):
            t.barrel(left, 2, z, facing="east")
    for z, b in ((2, "crate"), (3, "crate"), (4, "minecraft:hay_block[axis=y]"),
                 (5, "minecraft:white_wool"), (6, "minecraft:brown_wool")):
        if b == "crate":
            t.set(right, 1, z, "minecraft:spruce_planks")
            t.trapdoor(right, 2, z, "spruce", "west")
        else:
            t.set(right, 1, z, b)
    t.set(right, 2, 4, "minecraft:hay_block[axis=z]")
    t.set(hw, 1, 2, "minecraft:loom[facing=south]")
    t.hanging_lantern(hw, hw + 1, length // 2, chain=0)


def _tents(p):
    """Paste the tents round the fire, each turned so its door faces the fire."""
    # (name, half width, length, cloth, trim, patch, carpet, kind, corner x, z, quarter turns)
    tents = (
        ("red", 2, 6, "red", "white", "brown", "orange", ("red", "minecraft:fletching_table"), 15, 2, 0),
        ("blue", 2, 6, "blue", "light_blue", "cyan", "light_blue", ("blue", "minecraft:cartography_table"), 25, 14, 1),
        ("green", 2, 6, "green", "lime", "brown", "lime", ("green", "minecraft:composter[level=4]"), 9, 21, 2),
        ("yellow", 2, 6, "yellow", "orange", "white", "yellow", ("yellow", "minecraft:brewing_stand[has_bottle_0=false,has_bottle_1=false,has_bottle_2=false]"), 2, 14, 3),
        ("supply", 3, 8, "white", "brown", "light_gray", "brown", "supply", 23, 1, 0),
    )
    for name, hw, length, cloth, trim, patch, carpet, kind, x, z, turns in tents:
        t = _tent(f"wanderers_camp/{name}", hw, length, f"minecraft:{cloth}_wool", f"minecraft:{trim}_wool",
                  f"minecraft:{patch}_wool", carpet, kind)
        p.paste(t, x, 0, z, turns=turns)


# ------------------------------------------------------------------ wagon and horses' corner
def _wagon(p):
    """A covered wagon pointing west: slab bed on trapdoor wheels, trapdoor sides, wool hoops,
    a driver's bench, cargo, and the loot chest tucked at the back behind the barrels."""
    x0, x1, z0, z1 = 22, 27, 24, 26
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            p.slab(x, 1, z, "spruce", type="top")
        p.trapdoor(x, 2, z0, "spruce", "south", open=True)    # boarded sides
        p.trapdoor(x, 2, z1, "spruce", "north", open=True)
    for x in (x0 + 1, x1 - 1):                                # wheels
        p.trapdoor(x, 1, z0 - 1, "spruce", "north", open=True)
        p.trapdoor(x, 1, z1 + 1, "spruce", "south", open=True)
    for x in range(x0 + 1, x1 + 1):                           # canvas over hoops
        cover = "minecraft:light_gray_wool" if p.rnd.random() < 0.15 else "minecraft:white_wool"
        p.set(x, 3, z0, cover)
        p.set(x, 3, z1, cover)
        p.set(x, 4, (z0 + z1) // 2, "minecraft:white_wool")
    zm = (z0 + z1) // 2
    p.stairs(x0, 2, zm, "spruce", "east")                     # driver's bench
    p.fence(x0 - 1, 1, zm, "spruce")                          # the shaft
    p.fence(x0 - 2, 1, zm, "spruce")
    p.barrel(x0 + 1, 2, zm, facing="up")
    p.barrel(x0 + 2, 2, zm, facing="west")
    p.set(x0 + 2, 3, zm, "minecraft:hay_block[axis=x]")
    p.chest(x0 + 3, 2, zm, "wanderers_camp", "east")
    p.hanging_lantern(x0 + 1, 3, zm, chain=0)
    p.set(x1 + 1, 1, zm, "minecraft:spruce_trapdoor[facing=east,half=bottom,open=false,powered=false,waterlogged=false]")


def _hitching(p):
    """Hitching rail of log posts and fence, with hay and a water trough for the animals."""
    x = 31
    for z in (19, 23):
        p.log(x, 1, z, "spruce", stripped=True)
        p.log(x, 2, z, "spruce", stripped=True)
    for z in range(20, 23):
        p.fence(x, 2, z, "spruce")
    p.set(x + 1, 1, 20, "minecraft:water_cauldron[level=3]")
    p.set(x + 1, 1, 21, "minecraft:water_cauldron[level=2]")
    p.set(x + 1, 1, 22, "minecraft:hay_block[axis=z]")
    p.set(x - 1, 1, 22, "minecraft:hay_block[axis=y]")
    p.set(x - 1, 1, 21, "minecraft:leaf_litter[facing=east,segment_amount=2]")


def _drying_rack(p):
    """Two posts and a rail with hides and cloth hung to dry."""
    z = 21
    for x in (24, 28):
        for y in (1, 2, 3):
            p.fence(x, y, z, "spruce")
    for x in (25, 26, 27):
        p.fence(x, 3, z, "spruce")
    for x, colour in ((25, "brown"), (26, "white"), (27, "brown")):
        p.set(x, 2, z, f"minecraft:{colour}_wall_banner[facing=south]")


# ------------------------------------------------------------------ cooking spot
def _cooking(p):
    """North-west: a pot on a crossbar over a campfire, a smoker, food and a prep table."""
    for x in range(6, 12):
        for z in range(7, 11):
            p.set(x, 0, z, _pick(p, ("minecraft:cobblestone", 2), ("minecraft:gravel", 1), ("minecraft:coarse_dirt", 1)))
    for x in (7, 9):
        for y in (1, 2, 3):
            p.fence(x, y, 8, "spruce")
    p.fence(8, 3, 8, "spruce")
    p.set(8, 1, 8, state("minecraft:campfire", facing="south", lit=True, signal_fire=False, waterlogged=False))
    p.set(8, 2, 8, "minecraft:water_cauldron[level=2]")
    p.set(10, 1, 8, "minecraft:smoker[facing=south,lit=true]")
    p.set(10, 2, 8, "minecraft:cobblestone_slab[type=bottom,waterlogged=false]")
    p.set(11, 1, 8, "minecraft:barrel[facing=up,open=true]")
    p.set(11, 1, 7, "minecraft:pumpkin")
    p.set(10, 1, 7, "minecraft:melon")
    p.set(6, 1, 7, "minecraft:decorated_pot[cracked=false,facing=south,waterlogged=false]")
    p.fence(6, 1, 10, "spruce")                               # prep table
    p.set(6, 2, 10, "minecraft:spruce_pressure_plate[powered=false]")
    p.stairs(7, 1, 10, "spruce", "west")
    for x in (11, 12):                                        # firewood
        p.set(x, 1, 10, "minecraft:spruce_log[axis=z]")
    p.set(11, 2, 10, "minecraft:birch_log[axis=z]")


# ------------------------------------------------------------------ lookout and palisade
def _lookout(p):
    """A platform on log stilts with a ladder, railing, a little hipped roof and a bell."""
    x0, x1, z0, z1, top = 3, 6, 3, 6, 6
    for x, z in ((x0, z0), (x1, z0), (x0, z1), (x1, z1), (5, z1)):
        for y in range(0, top):
            p.log(x, y, z, "spruce")
    for x, z in ((x0, z0), (x1, z1)):                         # cross braces
        p.stairs(x + (1 if x == x0 else -1), top - 1, z, "spruce", "west" if x == x0 else "east", half="top")
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            p.set(x, top, z, "minecraft:spruce_planks" if (x + z) % 3 else "minecraft:stripped_spruce_log[axis=x]")
    for y in range(1, top + 1):
        p.ladder(5, y, z1 + 1, "south")
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            if (x in (x0, x1) or z in (z0, z1)) and (x, z) != (5, z1):
                p.fence(x, top + 1, z, "spruce")
    for x, z in ((x0, z0), (x1, z0), (x0, z1), (x1, z1)):
        p.fence(x, top + 2, z, "spruce")
    p.hip_roof(x0, x1, z0, z1, top + 3, "spruce", overhang=1)
    p.set(4, top + 1, 4, "minecraft:bell[attachment=floor,facing=south,powered=false]")
    p.barrel(4, top + 1, 5, facing="up")
    p.hanging_lantern(5, top + 2, 4, chain=1)


def _palisade(p):
    """A run of sharpened logs along the west side, rotten through in places, braced inside."""
    for z in range(7, 27):
        x = 1 if 9 <= z <= 23 else 2
        if z in (12, 21):                                     # rotted away
            continue
        if z == 20:                                           # a stump
            p.log(x, 0, z, "spruce")
            p.log(x, 1, z, "spruce")
            continue
        h = p.rnd.choice((3, 3, 4))
        for y in range(0, h + 1):
            p.log(x, y, z, "spruce")
        p.fence(x, h + 1, z, "spruce")
        if z % 4 == 0:
            p.stairs(x + 1, 1, z, "spruce", "west")
    for z in range(9, 24):                                    # moss and vines on the inner face
        if p.get(1, 1, z) and p.get(1, 1, z) != AIR and p.rnd.random() < 0.35:
            for y in range(p.rnd.randint(2, 3), 0, -1):
                if p.get(2, y, z) == AIR:
                    p.set(2, y, z, state("minecraft:vine", up=False, **{d: d == "west" for d in SIDES}))
    for x in range(3, 6):                                     # a fallen log
        p.set(x, 1, 21, "minecraft:spruce_log[axis=x]")
    p.set(2, 1, 22, "minecraft:moss_carpet")


def _lantern_posts(p):
    """Fence posts with an arm and a hanging lantern at the corners of the fire circle."""
    for x, z, arm in ((13, 10, 1), (22, 11, -1), (13, 22, 1), (22, 22, -1)):
        for y in (1, 2, 3):
            p.fence(x, y, z, "spruce")
        p.fence(x + arm, 3, z, "spruce")
        p.lantern(x + arm, 2, z, hanging=True)


def _scatter(p):
    """Odd bits of camp life and a few hardy plants on the trodden ground."""
    for x, colour in ((10, "white"), (11, "brown"), (12, "brown")):      # a bedroll by the fire
        p.carpet(x, 1, 19, colour)
    p.set(6, 8, 6, "minecraft:cobweb")                        # under the lookout roof
    p.set(3, 8, 3, "minecraft:cobweb")
    for x, z in ((20, 9), (14, 24), (8, 12), (29, 12)):
        if p.get(x, 1, z) == AIR:
            p.set(x, 1, z, f"minecraft:leaf_litter[facing={p.rnd.choice(SIDES)},segment_amount={p.rnd.randint(1, 4)}]")
    p.scatter((0, 1, 0, W - 1, 1, D - 1), p.mix(("minecraft:short_grass", 3), ("minecraft:dead_bush", 1),
                                                ("minecraft:fern", 1)), 0.04, only_on="minecraft:coarse_dirt")


def build():
    p = Piece("wanderers_camp", W, H, D, "camp")
    _site(p)
    _paths(p)
    _fire(p)
    _tents(p)
    _wagon(p)
    _hitching(p)
    _drying_rack(p)
    _cooking(p)
    _lookout(p)
    _palisade(p)
    _lantern_posts(p)
    _scatter(p)
    return p


PLACE = {
    "name": "wanderers_camp",
    "pieces": {"wanderers_camp": build},
    "step": "surface_structures",
    "start_height": 0,  # piece bottom lands at surface top block + start_height, so layer 0 replaces the top block
    "surface": True,
    "terrain": "beard_thin",
    "biomes": [
        "#minecraft:is_forest",
        "#minecraft:is_taiga",
        "#minecraft:is_savanna",
        "minecraft:plains",
        "minecraft:snowy_plains",
        "minecraft:desert",
        "minecraft:meadow",
    ],
    "spacing": 24,
    "separation": 8,
    "salt": 418200102,
}
