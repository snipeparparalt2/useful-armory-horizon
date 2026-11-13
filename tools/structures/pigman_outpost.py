"""Pigman outpost: a nether brick keep (Nether wastes, placed by height, enclosed). Brief:
docs/design/places.md section 5.

Plan (x east, z south; one piece, 25 x 16 x 25):

    NW turret ---------- north curtain + walkway ---------- NE turret
       |   west aisle  |   THRONE ROOM (vaulted)   | treasury |
       |   + stair     |   gold dais, brute spawner| (bars)   |
       |   barracks ^  |   balcony over the door   | armory ^ |   (^ = gallery floor above)
       |------------- hall facade, lava channels, fences ---------|
       |   hoglin pen  |   YARD (covered), piglin  | stores,  |
       |               |   spawner on the path     | cookfire |
    SW turret ------ gate (portcullis) between two towers ------ SE turret
                              landing

The keep is one closed mass: foundation, curtain walls two thick, a roof deck at y 10 that is
the battlemented walkway, a red nether brick gable over the hall and hipped caps on the four
turrets. Each turret has a ladder from the ground floor to the walkway; the north-east one is
the back way into the treasury. Every cell inside is set (air or block); outside only the
skirt (plinth, buttresses, cornice) is set, so it reads finished buried in netherrack or
standing free over a lava lake.
"""
from structkit import AIR, NS, Piece, ccw, state  # noqa: F401

W, H, D = 25, 16, 25
GX = 12                       # the north-south axis: gate, path, aisle, throne
DECK = 10                     # roof deck / walkway floor
HALL = (4, 4, 20, 11)         # hall interior x0, z0, x1, z1 (south wall at z 12)
YARD = (4, 13, 20, 20)        # yard interior
NAVE = (8, 16)                # throne room x range (galleries outside it)
TURRETS = ((0, 0), (20, 0), (0, 20), (20, 20))
TOWERS = ((8, 10), (14, 16))  # gate towers x ranges, z 22..24

LAVA = "minecraft:lava[level=0]"
GILDED = "minecraft:gilded_blackstone"
GOLD = "minecraft:gold_block"
PBB = "minecraft:polished_blackstone_bricks"
SHROOM = "minecraft:shroomlight"
NBF = "nether_bricks"         # material name for nether brick fences/stairs


# ------------------------------------------------------------------ footprint
def _in_turret(x, z):
    return any(ox <= x <= ox + 4 and oz <= z <= oz + 4 for ox, oz in TURRETS)


def _in_tower(x, z):
    return 22 <= z <= 24 and any(a <= x <= b for a, b in TOWERS)


def _in_keep(x, z):
    """Curtain square plus the gatehouse block (turrets are counted separately)."""
    return (2 <= x <= 22 and 2 <= z <= 22) or (8 <= x <= 16 and 21 <= z <= 24)


def _in_mass(x, z):
    return 0 <= x < W and 0 <= z < D and (_in_keep(x, z) or _in_turret(x, z))


def _in_gable(x, z):
    return 4 <= x <= 20 and 4 <= z <= 12


def _roof_y(z):
    """Height of the gable's stair course over row z (ridge slab at z 8)."""
    return 11 + min(z - 4, 12 - z)


# ------------------------------------------------------------------ helpers
def _corner(facing, side, kind):
    return f"{kind}_left" if ccw(facing) == side else f"{kind}_right"


def _campfire(p, x, y, z, facing="south", soul=True):
    name = "minecraft:soul_campfire" if soul else "minecraft:campfire"
    p.set(x, y, z, state(name, facing=facing, lit=True, signal_fire=False, waterlogged=False))


def _vines(p, x, top, z, length):
    """Weeping vines hanging from the block above `top`, `length` cells long."""
    for i in range(length):
        y = top - i
        if p.get(x, y, z) != AIR:
            return
        last = i == length - 1 or p.get(x, y - 1, z) != AIR
        p.set(x, y, z, state("minecraft:weeping_vines", age=p.rnd.randint(18, 25)) if last
              else "minecraft:weeping_vines_plant")
        if last:
            return


def build():
    p = Piece("pigman_outpost", W, H, D, "outpost")
    _masses(p)
    _skirt(p)
    _walkway(p)
    _hall_roof(p)
    _turrets(p)
    _gatehouse(p)
    _yard(p)
    _hall(p)
    _galleries(p)
    _treasury(p)
    _age(p)
    return p


# ------------------------------------------------------------------ the masonry
def _brick(p, y):
    """Wall brick: blackstone and cracks low down, plain nether brick above."""
    if y <= 1:
        return p.rnd.choices((PBB, "minecraft:cracked_polished_blackstone_bricks", "minecraft:blackstone"),
                             (5, 2, 2))[0]
    if y <= 3:
        return p.rnd.choices(("minecraft:nether_bricks", "minecraft:cracked_nether_bricks",
                              "minecraft:blackstone"), (6, 3, 1))[0]
    return p.rnd.choices(("minecraft:nether_bricks", "minecraft:cracked_nether_bricks",
                          "minecraft:red_nether_bricks"), (12, 3, 1))[0]


def _masses(p):
    """Solid keep, gatehouse and turrets up to the deck; every interior is carved later."""
    for x in range(W):
        for z in range(D):
            if _in_turret(x, z):
                for y in range(0, 13):
                    p.set(x, y, z, _brick(p, y))
            elif _in_keep(x, z):
                top = 11 if _in_tower(x, z) else DECK
                for y in range(0, top + 1):
                    p.set(x, y, z, _brick(p, y))
    # a gilded band and a chiseled trim course round the curtain at the deck
    for x in range(W):
        for z in range(D):
            if not _in_keep(x, z) or _in_tower(x, z):
                continue
            if any(not _in_mass(x + dx, z + dz) for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                p.set(x, DECK, z, "minecraft:chiseled_nether_bricks" if (x + z) % 4 == 0 else PBB)
                p.set(x, 1, z, PBB)


def _skirt(p):
    """Outside the curtain: a stair plinth, buttresses and a corbelled cornice under the
    parapet, on every face that is not a turret."""
    dirs = (("west", (-1, 0)), ("east", (1, 0)), ("north", (0, -1)), ("south", (0, 1)))
    for x in range(W):
        for z in range(D):
            if _in_mass(x, z):
                continue
            faces = [d for d, (dx, dz) in dirs if _in_keep(x + dx, z + dz) and not _in_turret(x + dx, z + dz)]
            if not faces:
                continue
            f = faces[0]
            shape = _corner(f, faces[1], "inner") if len(faces) == 2 else "straight"
            p.set(x, 0, z, PBB)
            p.stairs(x, 1, z, "polished_blackstone_bricks", f, shape=shape)
            p.stairs(x, 9, z, NBF, f, half="top", shape=shape)
            along = z if f in ("east", "west") else x
            if len(faces) == 1 and along in (8, 12, 16) and not (f == "north" and 8 <= x <= 16):
                for y in range(1, 8):
                    p.set(x, y, z, _brick(p, y))
                p.stairs(x, 8, z, NBF, f)
                p.set(x, 4, z, "minecraft:chiseled_nether_bricks")


def _walkway(p):
    """The deck is the walkway: crenellated parapet on the outer edge, air above the rest."""
    for x in range(W):
        for z in range(D):
            if not _in_keep(x, z) or _in_turret(x, z) or _in_tower(x, z) or _in_gable(x, z):
                continue
            edge = any(not _in_mass(x + dx, z + dz) for dx in (-1, 0, 1) for dz in (-1, 0, 1))
            if edge:
                p.set(x, 11, z, PBB if (x + z) % 2 else "minecraft:nether_bricks")
                merlon = (x + z) % 2 == 0
                p.set(x, 12, z, _brick(p, 12) if merlon else AIR)
                if merlon:
                    p.slab(x, 13, z, "polished_blackstone_bricks")
                else:
                    p.set(x, 13, z, AIR)
            else:
                p.set(x, DECK, z, p.rnd.choices(("minecraft:nether_bricks", "minecraft:cracked_nether_bricks",
                                                  "minecraft:polished_blackstone"), (6, 2, 1))[0])
                p.clear((x, 11, z, x, 13, z))
    # shroomlight skylights in the yard roof (they light the yard below)
    for x in (8, 12, 16):
        for z in (15, 18):
            p.set(x, DECK, z, SHROOM)
    # a murder grate of iron bars over the yard spawner, looking down from the walkway
    for x in range(11, 14):
        for z in range(16, 19):
            p.bars(x, DECK, z)
    # braziers at the walkway corners
    for x, z in ((5, 21), (19, 21), (5, 13), (19, 13)):
        p.set(x, 11, z, GILDED)
        _campfire(p, x, 12, z)


def _hall_roof(p):
    """Red nether brick gable over the hall (ridge east-west at z 8), two thick, gable ends
    of nether brick with a gilded apex; the attic is solid except the throne-room vault."""
    p.gable_roof(4, 20, 4, 12, 11, "red_nether_bricks", "x", overhang=0,
                 gable_fill="minecraft:nether_bricks", under="minecraft:nether_bricks")
    for x in range(5, 20):
        for z in range(5, 12):
            for y in range(11, _roof_y(z)):
                if p.get(x, y, z) in (None, AIR):
                    p.set(x, y, z, "minecraft:nether_bricks")
    for x in (4, 20):
        p.set(x, 14, 8, GILDED)
        p.set(x, 13, 8, "minecraft:chiseled_nether_bricks")
        p.set(x, 12, 8, "minecraft:red_nether_bricks")
    # ridge cresting: gold at both ends
    p.set(4, 15, 8, GOLD)
    p.set(20, 15, 8, GOLD)


# ------------------------------------------------------------------ turrets
def _turrets(p):
    for ox, oz in TURRETS:
        west, north = ox == 0, oz == 0
        # plinth, gilded band and trim
        for x in range(ox, ox + 5):
            for z in range(oz, oz + 5):
                if x in (ox, ox + 4) or z in (oz, oz + 4):
                    p.set(x, 0, z, "minecraft:blackstone")
                    p.set(x, 1, z, PBB)
                    p.set(x, 7, z, GILDED if (x + z) % 2 else PBB)
                    p.set(x, 12, z, "minecraft:chiseled_nether_bricks" if (x + z) % 2 == 0 else "minecraft:red_nether_bricks")
        # hipped cap with a gold finial; the inside of the cap is solid
        p.fill(ox + 1, 13, oz + 1, ox + 3, 14, oz + 3, "minecraft:nether_bricks")
        p.hip_roof(ox, ox + 4, oz, oz + 4, 13, "red_nether_bricks", overhang=0, ridge_slab=GOLD)
        # inside: ground room y 2..9, upper room y 11..12 on a floor at y 10
        ix0, iz0 = ox + 1, oz + 1
        p.fill(ix0, 1, iz0, ix0 + 2, 1, iz0 + 2, "minecraft:polished_blackstone")
        p.clear((ix0, 2, iz0, ix0 + 2, 9, iz0 + 2))
        p.fill(ix0, 10, iz0, ix0 + 2, 10, iz0 + 2, "minecraft:crimson_planks")
        p.clear((ix0, 11, iz0, ix0 + 2, 12, iz0 + 2))
        lx = ox + 1 if west else ox + 3
        lz = oz + 2
        p.set(lx, 10, lz, AIR)
        p.ladder_column(lx, lz, 2, 11, "east" if west else "west")
        # doors: ground floor toward the yard / hall, upper floor onto the walkway
        dx = 3 if west else 21
        dz = 4 if north else 20
        for y in (2, 3, 11, 12):
            p.set(dx, y, dz, AIR)
        p.set(dx, 4, dz, PBB)
        if not (not west and north):                     # the NE one is a broken-through gap
            p.door(dx, 2, dz, "crimson", "west" if west else "east", hinge="right" if north else "left")
        # arrow slits on the two outer faces, ground and upper rooms
        sx = ox if west else ox + 4
        sz = oz if north else oz + 4
        for y in (5, 6, 11):
            p.bars(sx, y, oz + 2)
            p.bars(ox + 2, y, sz)
        # furniture in the free corners
        fx = ox + 1 if west else ox + 3
        for fz, what in ((oz + 1, "a"), (oz + 3, "b")):
            if what == "a":
                p.barrel(fx, 2, fz, "up")
                p.lantern(fx, 3, fz, soul=True)
            else:
                p.set(fx, 2, fz, "minecraft:crimson_planks")
                p.slab(fx, 3, fz, "crimson")
        p.hanging_lantern(ox + 2, 9, oz + 2, chain=0, soul=True)
        p.lantern(ox + 2, 11, oz + 2 + (1 if north else -1), soul=True)
    # the NW turret's ground room is a little shrine to gold
    p.set(2, 2, 1, "minecraft:lava_cauldron")
    p.set(3, 2, 1, GOLD)
    p.set(3, 3, 1, "minecraft:piglin_head[powered=false,rotation=8]")
    p.set(1, 3, 1, AIR)
    p.set(1, 2, 1, "minecraft:raw_gold_block")


# ------------------------------------------------------------------ gate
def _gatehouse(p):
    """Gate through the south curtain (x 11..13) with a half-raised nether brick fence
    portcullis, a recessed landing between two square towers, and a gilded crest."""
    p.clear((11, 2, 21, 13, 5, 22))
    for z in (21, 22):
        p.set(GX, 1, z, PBB)
        p.set(11, 1, z, "minecraft:polished_blackstone")
        p.set(13, 1, z, "minecraft:polished_blackstone")
    p.stairs(11, 5, 21, "polished_blackstone_bricks", "west", half="top")
    p.stairs(13, 5, 21, "polished_blackstone_bricks", "east", half="top")
    for x in (11, 12, 13):
        p.fence(x, 5, 22, NBF)
        p.fence(x, 4, 22, NBF)
    # the landing, roofed by the gatehouse, open to the south
    p.clear((11, 2, 23, 13, 6, 24))
    for x in (11, 12, 13):
        p.set(x, 1, 23, PBB if x == GX else "minecraft:polished_blackstone")
        p.stairs(x, 1, 24, "polished_blackstone_bricks", "north")
    p.stairs(11, 6, 24, "polished_blackstone_bricks", "west", half="top")
    p.stairs(13, 6, 24, "polished_blackstone_bricks", "east", half="top")
    p.stairs(11, 6, 23, "polished_blackstone_bricks", "west", half="top")
    p.stairs(13, 6, 23, "polished_blackstone_bricks", "east", half="top")
    for x in range(10, 15):
        p.set(x, 7, 24, GILDED if x in (10, 14) else PBB)
    p.set(GX, 8, 24, GOLD)
    p.set(11, 8, 24, GILDED)
    p.set(13, 8, 24, GILDED)
    p.set(GX, 9, 24, "minecraft:chiseled_polished_blackstone")
    p.wall_torch(11, 4, 23, "east", soul=True)
    p.wall_torch(13, 4, 23, "west", soul=True)
    # towers: corner quoins of polished blackstone, crenellated tops with soul braziers
    for a, b in TOWERS:
        for x in (a, b):
            for z in (22, 24):
                for y in range(2, 12):
                    if y % 3 == 0:
                        p.set(x, y, z, PBB)
        for x, z in ((a, 22), (b, 22), (a, 24), (b, 24)):
            p.set(x, 12, z, "minecraft:nether_bricks")
            p.slab(x, 13, z, "polished_blackstone_bricks")
        for x, z in ((a + 1, 22), (a, 23), (b, 23), (a + 1, 24)):
            p.set(x, 12, z, AIR)
            p.set(x, 13, z, AIR)
        p.set(a + 1, 12, 23, GILDED)
        _campfire(p, a + 1, 13, 23)
        p.bars(a + 1, 5, 24)
        p.bars(a + 1, 6, 24)


# ------------------------------------------------------------------ yard
def _yard(p):
    x0, z0, x1, z1 = YARD
    p.clear((x0, 2, z0, x1, 9, z1))
    ground = p.mix(("minecraft:blackstone", 5), ("minecraft:polished_blackstone", 2), ("minecraft:netherrack", 3),
                   ("minecraft:soul_soil", 2), ("minecraft:cracked_polished_blackstone_bricks", 1))
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            if 11 <= x <= 13:
                p.set(x, 1, z, PBB if x == GX else "minecraft:polished_blackstone")
            else:
                p.set(x, 1, z, ground)
    # lava channels in front of the hall, behind nether brick fences
    for x in list(range(5, 10)) + list(range(15, 20)):
        p.set(x, 1, 13, LAVA)
        p.set(x, 0, 13, "minecraft:magma_block")
        p.fence(x, 2, 14, NBF)
        p.set(x, 1, 14, PBB)
    # pilasters flanking the hall door
    for x in (10, 14):
        p.fill(x, 1, 13, x, 8, 13, PBB)
        p.set(x, 2, 13, "minecraft:chiseled_polished_blackstone")
        p.set(x, 8, 13, GILDED)
    # ceiling: cornice, crimson beams, hanging lanterns
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            fz = "north" if z == z0 else "south" if z == z1 else None
            fx = "west" if x == x0 else "east" if x == x1 else None
            if fz and fx:
                p.stairs(x, 9, z, NBF, fz, half="top", shape=_corner(fz, fx, "inner"))
            elif fz or fx:
                p.stairs(x, 9, z, NBF, fz or fx, half="top")
    for x in (6, 10, 14, 18):
        for z in range(z0, z1 + 1):
            p.log(x, 9, z, "crimson", axis="z", stripped=True)
    for x, z in ((10, 16), (14, 16), (10, 19), (14, 19), (6, 17), (18, 17)):
        p.hanging_lantern(x, 8, z, chain=0, soul=True)
    # the spawner on the path, ringed by a gilded inlay
    for dx in (-1, 0, 1):
        for dz in (-1, 0, 1):
            if dx or dz:
                p.set(GX + dx, 1, 17 + dz, GILDED if dx and dz else "minecraft:chiseled_polished_blackstone")
    p.spawner(GX, 2, 17, f"{NS}:lost_pigman")
    # soul braziers either side of the path in front of the channels
    for x in (10, 14):
        p.set(x, 2, 15, GILDED)
        _campfire(p, x, 3, 15)
    _hoglin_pen(p)
    _stores(p)
    _yard_walls(p)


def _hoglin_pen(p):
    """A crimson fence pen in the south-west of the yard: nylium, fungus, gnawed bones."""
    for x in range(5, 10):
        for z in range(16, 20):
            edge = x in (5, 9) or z in (16, 19)
            if edge:
                p.fence(x, 2, z, "crimson")
            else:
                p.set(x, 1, z, "minecraft:crimson_nylium")
    p.fence_gate(9, 2, 18, "crimson", "east")
    p.set(6, 2, 17, "minecraft:crimson_fungus")
    p.set(8, 2, 18, "minecraft:crimson_roots")
    p.set(7, 2, 18, "minecraft:bone_block[axis=x]")
    p.set(8, 2, 17, "minecraft:cauldron")
    p.set(6, 2, 18, "minecraft:nether_wart_block")
    p.set(7, 1, 17, "minecraft:soul_soil")
    p.set(6, 3, 18, "minecraft:crimson_fungus")


def _stores(p):
    """East side of the yard: barrel stacks, a gold pile, a cookfire with a spit."""
    for x, z, h in ((20, 14, 3), (19, 14, 2), (20, 15, 2), (20, 16, 1), (19, 15, 1)):
        for y in range(2, 2 + h):
            p.barrel(x, y, z, p.rnd.choice(("up", "west", "north")))
    p.set(20, 2, 18, GOLD)
    p.set(20, 3, 18, "minecraft:raw_gold_block")
    p.set(20, 2, 17, GILDED)
    p.set(19, 2, 18, "minecraft:raw_gold_block")
    p.slab(19, 2, 17, "blackstone")
    p.slab(20, 3, 17, "polished_blackstone")
    # cookfire: a ring of slabs round a campfire, fence posts and a chain spit
    _campfire(p, 16, 2, 18, facing="west", soul=False)
    for x, z in ((15, 17), (17, 17), (15, 19), (17, 19), (16, 17), (16, 19)):
        p.slab(x, 2, z, "blackstone")
    p.fence(15, 2, 18, NBF)
    p.fence(17, 2, 18, NBF)
    p.fence(15, 3, 18, NBF)
    p.fence(17, 3, 18, NBF)
    p.chain(16, 3, 18, axis="x")
    # a crimson table and stools by the fire
    p.fence(18, 2, 20, "crimson")
    p.set(18, 3, 20, "minecraft:crimson_pressure_plate[powered=false]")
    p.stairs(17, 2, 20, "crimson", "west")
    p.stairs(19, 2, 20, "crimson", "east")


def _yard_walls(p):
    """Arrow slits in the curtain, crimson posts under the beam ends in the south wall."""
    for z in (16, 18):
        p.set(3, 3, z, AIR)
        p.set(3, 4, z, AIR)
        p.bars(2, 3, z)
        p.bars(2, 4, z)
        p.set(21, 3, z, AIR)
        p.set(21, 4, z, AIR)
        p.bars(22, 3, z)
        p.bars(22, 4, z)
    for x in (8, 16):
        p.set(x, 3, 21, AIR)
        p.set(x, 4, 21, AIR)
        p.bars(x, 3, 22)
        p.bars(x, 4, 22)
    for x in (6, 18):
        for y in range(2, 9):
            p.log(x, y, 21, "crimson", stripped=True)
    for z in (14, 19):
        for x in (3, 21):
            for y in range(2, 9):
                p.log(x, y, z, "crimson", stripped=True)
    # red wool hangings on the side walls
    for x, z in ((3, 15), (21, 15), (3, 17), (21, 17)):
        p.fill(x, 5, z, x, 7, z, "minecraft:red_wool")
        p.set(x, 8, z, GOLD if z == 17 else GILDED)


# ------------------------------------------------------------------ hall
def _hall(p):
    x0, z0, x1, z1 = HALL
    n0, n1 = NAVE
    p.clear((x0, 2, z0, x1, 9, z1))
    # the throne-room vault up into the gable
    for x in range(n0, n1 + 1):
        for z in range(z0 + 1, z1 + 1):
            top = 14 if z == 8 else _roof_y(z) - 2
            p.clear((x, 10, z, x, top, z))
            if z != 8 and top >= 10:
                p.stairs(x, top, z, NBF, "north" if z < 8 else "south", half="top")
    # floor: polished blackstone field, brick border, gilded ring round the spawner
    field = p.mix(("minecraft:polished_blackstone", 6), ("minecraft:blackstone", 1),
                  ("minecraft:cracked_polished_blackstone_bricks", 1))
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            if x < n0 or x > n1:
                continue
            border = x in (n0, n1) or z in (z0, z1)
            p.set(x, 1, z, PBB if border else field)
    for dx in (-1, 0, 1):
        for dz in (-1, 0, 1):
            p.set(GX + dx, 1, 8 + dz, GILDED if dx and dz else GOLD if not (dx or dz) else
                  "minecraft:chiseled_polished_blackstone")
    # red carpet aisle with gold-yellow edges from the door to the dais
    for z in range(7, 12):
        for x in (11, 12, 13):
            p.carpet(x, 2, z, "red" if x == GX else "yellow")
    _dais(p)
    p.spawner(GX, 2, 8, "minecraft:piglin_brute")
    # columns of stripped crimson stems under the gallery edges
    for x in (n0 - 1, n1 + 1):
        for z in (6, 10):
            p.set(x, 1, z, PBB)
            p.set(x, 2, z, "minecraft:chiseled_polished_blackstone")
            for y in range(3, 10):
                p.log(x, y, z, "crimson", stripped=True)
            p.set(x, 5, z, GILDED)
            p.wall_torch(x + (1 if x == n0 - 1 else -1), 4, z, "east" if x == n0 - 1 else "west", soul=True)
    # door in the south wall to the yard, with an arch and a crest; a window above
    p.clear((11, 2, 12, 13, 4, 12))
    p.stairs(11, 4, 12, "polished_blackstone_bricks", "west", half="top")
    p.stairs(13, 4, 12, "polished_blackstone_bricks", "east", half="top")
    for x in (11, 12, 13):
        p.set(x, 1, 12, PBB)
        p.set(x, 5, 12, GILDED if x != GX else GOLD)
        p.fence(x, 7, 12, NBF)
        p.fence(x, 8, 12, NBF)
    p.set(GX, 6, 13, "minecraft:piglin_wall_head[facing=south,powered=false]")
    p.set(GX, 6, 12, "minecraft:chiseled_polished_blackstone")
    # barred windows from the yard into the west aisle and the treasury
    for x in (6, 18):
        p.bars(x, 3, 12)
        p.bars(x, 4, 12)
    # light: shroomlights in the ridge, soul lanterns on chains down the nave
    for x in (9, 12, 15):
        p.set(x, 14, 8, SHROOM)
        p.hanging_lantern(x, 11, 8, chain=2, soul=True)
    _west_aisle(p)


def _dais(p):
    """Gold-block dais against the north wall with polished blackstone steps, the throne,
    the hall chest beside it and soul braziers; red hangings and a piglin head above."""
    z0 = HALL[1]
    for x in range(9, 16):
        for z in (z0, z0 + 1):
            p.set(x, 2, z, GOLD if 10 <= x <= 14 else GILDED)
        p.stairs(x, 2, z0 + 2, "polished_blackstone", "north")
    p.stairs(9, 2, z0 + 2, "polished_blackstone", "north", shape="outer_right")
    p.stairs(15, 2, z0 + 2, "polished_blackstone", "north", shape="outer_left")
    p.stairs(8, 2, z0, "polished_blackstone", "east")
    p.stairs(8, 2, z0 + 1, "polished_blackstone", "east")
    p.stairs(16, 2, z0, "polished_blackstone", "west")
    p.stairs(16, 2, z0 + 1, "polished_blackstone", "west")
    # throne
    p.stairs(GX, 3, z0, "polished_blackstone", "north")
    p.set(GX - 1, 3, z0, GILDED)
    p.set(GX + 1, 3, z0, GILDED)
    p.set(GX - 1, 4, z0, "minecraft:polished_blackstone_pressure_plate[powered=false]")
    p.set(GX + 1, 4, z0, "minecraft:polished_blackstone_pressure_plate[powered=false]")
    p.set(GX, 6, z0, "minecraft:piglin_wall_head[facing=south,powered=false]")
    wz = z0 - 1
    for y in range(3, 9):
        p.set(GX, y, wz, GOLD if y in (4, 5, 7) else GILDED)
        for x in (GX - 1, GX + 1):
            p.set(x, y, wz, GILDED if y in (3, 8) else "minecraft:red_wool")
    for x in (9, 15):
        for y in range(4, 9):
            p.set(x, y, wz, "minecraft:red_wool")
        p.set(x, 3, wz, GILDED)
        p.set(x, 9, wz, GOLD)
    # hall chest and a lantern on the dais, braziers off its front corners
    p.chest(14, 3, z0, "pigman_outpost", "south")
    p.lantern(10, 3, z0)
    p.set(10, 3, z0 + 1, "minecraft:raw_gold_block")
    for x in (9, 15):
        p.set(x, 2, z0 + 3, GILDED)
        _campfire(p, x, 3, z0 + 3)


def _west_aisle(p):
    """Under the west gallery: a stair up along the west wall, stores under the gallery."""
    floor = p.mix(("minecraft:crimson_planks", 3), ("minecraft:polished_blackstone", 2), ("minecraft:blackstone", 1))
    for x in range(4, 8):
        for z in range(4, 12):
            p.set(x, 1, z, floor)
    for x in range(17, 21):
        for z in range(4, 12):
            if x == 17:
                p.set(x, 1, z, PBB)
    # stair rising north along x 4, solid under it
    for i, z in enumerate((11, 10, 9, 8)):
        y = 2 + i
        p.stairs(4, y, z, "polished_blackstone_bricks", "north")
        for yy in range(2, y):
            p.set(4, yy, z, PBB)
    # stores
    for x, z, h in ((5, 4, 2), (6, 4, 1), (4, 6, 1), (5, 5, 1)):
        for y in range(2, 2 + h):
            p.barrel(x, y, z, "up" if y == 2 else "north")
    p.set(6, 2, 8, "minecraft:crimson_planks")
    p.slab(6, 3, 8, "crimson")
    p.set(5, 2, 11, "minecraft:raw_gold_block")
    p.slab(6, 2, 11, "blackstone")
    p.hanging_lantern(5, 5, 7, chain=0, soul=True)


def _galleries(p):
    """Upper floor at y 6: west gallery (bunks), east gallery (armory), joined by a balcony
    along the south wall over the hall door; fence railings toward the throne room."""
    planks = p.mix(("minecraft:crimson_planks", 5), ("minecraft:stripped_crimson_hyphae[axis=x]", 1))
    for z in range(4, 12):
        for x in list(range(4, 8)) + list(range(17, 21)):
            p.set(x, 6, z, planks)
    for x in range(8, 17):
        for z in (10, 11):
            p.set(x, 6, z, planks)
        p.stairs(x, 5, 10, NBF, "south", half="top")
    for z in range(8, 12):
        p.set(4, 6, z, AIR)                                # stair well
    p.set(4, 6, 7, "minecraft:crimson_planks")
    # railings
    for z in range(4, 10):
        if z != 6:
            p.fence(7, 7, z, NBF)
            p.fence(17, 7, z, NBF)
    for x in range(8, 17):
        p.fence(x, 7, 9, NBF)
    p.fence(5, 7, 8, NBF)
    # columns carry on up as posts
    for x in (7, 17):
        p.log(x, 6, 6, "crimson", stripped=True)
        p.log(x, 6, 10, "crimson", stripped=True)
    # west: three bunks against the north wall, a barrel at each foot end
    for x in (4, 5, 6):
        p.bed(x, 7, 5, "red", "north")
    p.barrel(5, 7, 6, "up")
    p.barrel(6, 7, 6, "west")
    p.trapdoor(6, 8, 6, "crimson", "south", half="bottom")
    p.hanging_lantern(5, 9, 7, chain=0)
    p.hanging_lantern(6, 9, 10, chain=0, soul=True)
    # east: the armory: weapon racks on the east wall, an anvil, a table and stools
    for z in (5, 6, 7, 8):
        p.fence(20, 7, z, "crimson")
        p.trapdoor(20, 8, z, "crimson", "west", open=True)
    p.set(20, 9, 5, "minecraft:lightning_rod[facing=up,powered=false,waterlogged=false]")
    p.set(20, 7, 4, "minecraft:smithing_table")
    p.set(19, 7, 4, "minecraft:chipped_anvil[facing=east]")
    p.set(18, 7, 4, "minecraft:grindstone[face=floor,facing=north]")
    p.fence(19, 7, 10, "crimson")
    p.set(19, 8, 10, "minecraft:crimson_pressure_plate[powered=false]")
    p.stairs(18, 7, 10, "crimson", "west")
    p.stairs(20, 7, 10, "crimson", "east")
    p.barrel(20, 7, 11, "west")
    p.barrel(20, 8, 11, "up")
    p.set(18, 7, 11, "minecraft:target[power=0]")
    p.set(19, 7, 7, GILDED)
    p.set(19, 8, 7, "minecraft:piglin_head[powered=false,rotation=4]")
    p.hanging_lantern(19, 9, 6, chain=0, soul=True)
    p.hanging_lantern(12, 9, 11, chain=0)


def _treasury(p):
    """Ground floor of the east aisle behind iron bars: bullion stacks, the treasury chest,
    a hole into the NE turret (its back door)."""
    for x in range(18, 21):
        for z in range(4, 12):
            p.set(x, 1, z, GILDED if (x + z) % 3 == 0 else PBB)
    for z in range(4, 12):
        if z not in (6, 10):
            for y in range(2, 6):
                p.bars(17, y, z)
    p.chest(20, 2, 8, "pigman_outpost", "west")
    p.set(20, 2, 7, GILDED)
    p.set(20, 2, 9, GILDED)
    p.lantern(20, 3, 7)
    for x, z, h in ((20, 11, 3), (19, 11, 2), (20, 10, 2), (18, 11, 1), (19, 10, 1), (20, 5, 1)):
        for y in range(2, 2 + h):
            p.set(x, y, z, GOLD if (y + x) % 2 else "minecraft:raw_gold_block")
    p.set(18, 2, 5, GILDED)
    p.set(18, 3, 5, GOLD)
    p.set(18, 2, 9, "minecraft:raw_gold_block")
    p.hanging_lantern(19, 5, 8, chain=0)
    # the hole through to the NE turret: broken bricks, gold spilled into the gap
    p.set(21, 4, 4, "minecraft:cracked_polished_blackstone_bricks")
    p.set(21, 1, 4, "minecraft:blackstone")
    p.slab(19, 2, 4, "blackstone")
    p.set(18, 2, 4, "minecraft:raw_gold_block")


# ------------------------------------------------------------------ age
def _age(p):
    """Weeping vines from the yard roof, broken merlons, a slumped bit of parapet."""
    for x, z, n in ((5, 15, 3), (8, 19, 2), (16, 14, 2), (19, 18, 3), (13, 15, 1), (7, 14, 2), (17, 19, 1)):
        _vines(p, x, 9, z, n)
    for x, z in ((2, 10), (22, 6), (16, 2), (6, 22)):
        if p.get(x, 12, z) not in (None, AIR):
            p.set(x, 12, z, AIR)
            p.set(x, 13, z, AIR)
    # a slumped stretch of the east parapet: rubble on the walkway
    for z in (11, 12, 13):
        p.set(22, 11, z, "minecraft:cracked_nether_bricks")
        p.set(22, 12, z, AIR)
        p.set(22, 13, z, AIR)
    p.slab(21, 11, 12, "nether_bricks")
    p.set(21, 11, 13, "minecraft:blackstone")
    p.slab(21, 11, 14, "blackstone")
    # crimson roots and a fungus in the corners of the yard floor
    for x, z in ((4, 15), (20, 13), (4, 19)):
        if p.get(x, 2, z) == AIR:
            p.set(x, 2, z, "minecraft:crimson_roots")


PLACE = {
    "name": "pigman_outpost",
    "pieces": {"pigman_outpost": build},
    "step": "underground_structures",
    "start_height": (34, 60),
    "surface": False,
    "terrain": "none",
    "biomes": [
        "minecraft:nether_wastes",
    ],
    "spacing": 20,
    "separation": 8,
    "salt": 418200105,
}
