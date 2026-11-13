"""Shadow vault: a sealed deepslate vault (underground, Y -52 to -12). Brief: docs/design/places.md
section 6.

Plan (x east, z south; one piece, 41 x 14 x 36):

    west alcove | ring corridor (3 wide, rib-vaulted) | hidden east alcove
                |   sanctum (15 x 15, coffered)       |  (behind a false wall)
                |   guard hall to the south with the walled-up old entrance

The player digs in from anywhere. The sanctum is entered through an iron gate in its south
wall (iron door between iron bars, opened by a lever on the lintel). Main chest on the
dais under a ceiling of glowing shadow ore; one cache in each alcove. Vault guardian
spawners: in the corridor in front of the gate, and on the sanctum floor.
"""
from structkit import AIR, NS, Piece, ccw

W, H, D = 41, 14, 36
SHADOW = f"{NS}:shadowblock"
SHADOW_ORE = f"{NS}:deepslate_shadow_ore"
GUARDIAN = f"{NS}:vault_guardian"

# masses as (x0, z0, x1, z1, top y): every room is carved out of one of these
RING = (6, 0, 34, 28, 8)
SANCTUM = (11, 5, 29, 23, 13)
WEST_ALCOVE = (0, 10, 6, 18, 7)
EAST_ALCOVE = (34, 10, 40, 18, 7)
GUARD_HALL = (14, 27, 26, 35, 8)
MASSES = (RING, SANCTUM, WEST_ALCOVE, EAST_ALCOVE, GUARD_HALL)

# room interiors (x0, z0, x1, z1)
CORRIDOR_OUT = (8, 2, 32, 26)
CORRIDOR_IN = (11, 5, 29, 23)        # the sanctum mass the corridor runs round
ROOM = (13, 7, 27, 21)               # the sanctum
GATE_X = 20


def build():
    p = Piece("shadow_vault", W, H, D, "vault")
    masonry = p.mix(("minecraft:deepslate_bricks", 8), ("minecraft:cracked_deepslate_bricks", 3),
                    ("minecraft:deepslate_tiles", 3), ("minecraft:cracked_deepslate_tiles", 1),
                    ("minecraft:cobbled_deepslate", 2), (SHADOW_ORE, 0.3))
    for x0, z0, x1, z1, top in MASSES:
        p.fill(x0, 0, z0, x1, top, z1, masonry)
    _exterior(p)
    _corridor(p)
    _sanctum(p)
    _gate(p)
    _west_alcove(p)
    _east_alcove(p)
    _guard_hall(p)
    _collapse(p)
    _sculk_and_cobwebs(p)
    return p


# ------------------------------------------------------------------ helpers
def _corner(facing, side, kind):
    """Stair shape for a corner cell: kind 'inner' or 'outer', `side` the second direction."""
    return f"{kind}_left" if ccw(facing) == side else f"{kind}_right"


def _solid(p, x, y, z):
    b = p.get(x, y, z)
    return b is not None and b != AIR


def _trim(p, x0, z0, x1, z1, y, block):
    """Re-face the rectangle's perimeter cells at height y that are solid and face air."""
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            if x not in (x0, x1) and z not in (z0, z1):
                continue
            if not _solid(p, x, y, z):
                continue
            if any(p.get(x + dx, y, z + dz) == AIR for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                p.set(x, y, z, block() if callable(block) else block)


def _in_corridor(x, z):
    ox0, oz0, ox1, oz1 = CORRIDOR_OUT
    ix0, iz0, ix1, iz1 = CORRIDOR_IN
    return ox0 <= x <= ox1 and oz0 <= z <= oz1 and not (ix0 <= x <= ix1 and iz0 <= z <= iz1)


def _coffer(p, x0, z0, x1, z1, y, lid):
    """A ceiling coffer over x0..x1, z0..z1: a ring of upside-down stairs at y stepping up
    from the beams, the middle open to a lid of `lid` at y + 1."""
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            fz = "north" if z == z0 else "south" if z == z1 else None
            fx = "west" if x == x0 else "east" if x == x1 else None
            if fz and fx:
                p.stairs(x, y, z, "polished_deepslate", fz, half="top", shape=_corner(fz, fx, "inner"))
                p.set(x, y + 1, z, "minecraft:deepslate_tiles")
            elif fz or fx:
                p.stairs(x, y, z, "polished_deepslate", fz or fx, half="top")
                p.set(x, y + 1, z, "minecraft:deepslate_tiles")
            else:
                p.set(x, y, z, AIR)
                p.set(x, y + 1, z, lid)


# ------------------------------------------------------------------ outside
def _exterior(p):
    """A plinth of stairs at the foot and a corbelled cornice at the top of every mass face
    that is not against another mass, so the vault reads as built when a cave exposes it."""
    for x0, z0, x1, z1, top in MASSES:
        for side, (dx, dz) in (("west", (-1, 0)), ("east", (1, 0)), ("north", (0, -1)), ("south", (0, 1))):
            facing = {"west": "east", "east": "west", "north": "south", "south": "north"}[side]
            if dx:
                cells = [(x0 - 1 if dx < 0 else x1 + 1, z) for z in range(z0, z1 + 1)]
            else:
                cells = [(x, z0 - 1 if dz < 0 else z1 + 1) for x in range(x0, x1 + 1)]
            for x, z in cells:
                for y, half in ((0, "bottom"), (top, "top")):
                    if p.in_bounds(x, y, z) and not p.is_set(x, y, z):
                        p.stairs(x, y, z, "deepslate_tiles", facing, half=half)


# ------------------------------------------------------------------ ring corridor
def _corridor(p):
    """3 wide, 4 high with a pointed vault: corbel stairs at y5, a centre slot to y6.
    Transverse ribs of polished deepslate with a keystone and a hanging soul lantern."""
    ox0, oz0, ox1, oz1 = CORRIDOR_OUT
    centre = lambda x, z: x in (ox0 + 1, ox1 - 1) or z in (oz0 + 1, oz1 - 1)  # noqa: E731
    ribs = {(x, z) for x in range(ox0, ox1 + 1) for z in range(oz0, oz1 + 1) if _in_corridor(x, z)
            and ((x <= 10 or x >= 30) and z in (8, 14, 20) or z <= 4 and x in (14, 20, 26)
                 or z >= 24 and x in (14, 26))}
    floor = p.mix(("minecraft:deepslate_tiles", 6), ("minecraft:cracked_deepslate_tiles", 3),
                  ("minecraft:cobbled_deepslate", 1))
    for x in range(ox0, ox1 + 1):
        for z in range(oz0, oz1 + 1):
            if not _in_corridor(x, z):
                continue
            p.clear((x, 2, z, x, 5, z))
            if centre(x, z):
                p.set(x, 6, z, AIR)
                p.set(x, 1, z, "minecraft:chiseled_deepslate" if (x, z) in ribs else "minecraft:polished_deepslate")
            else:
                p.set(x, 1, z, floor)
    # vault corbels: each non-centre cell gets an upside-down stair toward its wall(s)
    for x in range(ox0, ox1 + 1):
        for z in range(oz0, oz1 + 1):
            if not _in_corridor(x, z) or centre(x, z):
                continue
            walls = [d for d, (dx, dz) in (("north", (0, -1)), ("south", (0, 1)), ("west", (-1, 0)), ("east", (1, 0)))
                     if not _in_corridor(x + dx, z + dz)]
            mat = "polished_deepslate" if (x, z) in ribs else "deepslate_tiles"
            if len(walls) == 2:
                fz, fx = sorted(walls, key=lambda d: d not in ("north", "south"))
                p.stairs(x, 5, z, mat, fz, half="top", shape=_corner(fz, fx, "inner"))
            elif len(walls) == 1:
                p.stairs(x, 5, z, mat, walls[0], half="top")
            else:                                   # the four inner corners of the ring
                fx = "east" if x < GATE_X else "west"
                fz = "south" if z < 14 else "north"
                p.stairs(x, 5, z, mat, fx, half="top", shape=_corner(fx, fz, "outer"))
    # plinth course and rib pilasters on both corridor walls
    for rect in ((ox0 - 1, oz0 - 1, ox1 + 1, oz1 + 1), CORRIDOR_IN):
        _trim(p, *rect, 2, "minecraft:polished_deepslate")
    for x, z in ribs:
        for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if not _in_corridor(x + dx, z + dz):
                p.fill(x + dx, 2, z + dz, x + dx, 4, z + dz, "minecraft:polished_deepslate")
        if centre(x, z):
            p.set(x, 6, z, "minecraft:chiseled_deepslate")
            p.hanging_lantern(x, 5, z, chain=0, soul=True)
    _corridor_niches(p)


# ------------------------------------------------------------------ sanctum
def _sanctum(p):
    rx0, rz0, rx1, rz1 = ROOM
    p.clear((rx0, 2, rz0, rx1, 9, rz1))
    _sanctum_floor(p)
    _sanctum_ceiling(p)
    _sanctum_walls(p)
    _sanctum_pillars(p)
    _dais(p)
    _braziers_and_sentinels(p)
    p.spawner(GATE_X, 2, 14, GUARDIAN)


def _sanctum_floor(p):
    """Polished border, cracked tile field, a polished aisle from the gate and a ring of
    crying obsidian and shadow block round the spawner."""
    rx0, rz0, rx1, rz1 = ROOM
    field = p.mix(("minecraft:deepslate_tiles", 7), ("minecraft:cracked_deepslate_tiles", 2),
                  ("minecraft:deepslate_bricks", 2))
    for x in range(rx0, rx1 + 1):
        for z in range(rz0, rz1 + 1):
            ring = max(abs(x - GATE_X), abs(z - 14))
            if x in (rx0, rx1) or z in (rz0, rz1):
                block = "minecraft:polished_deepslate"
            elif ring == 0:
                block = SHADOW_ORE
            elif ring == 1:
                block = SHADOW
            elif ring == 2:
                block = "minecraft:crying_obsidian" if abs(x - GATE_X) == abs(z - 14) else "minecraft:chiseled_deepslate"
            elif abs(x - GATE_X) <= 1 and z > 14:
                block = "minecraft:polished_deepslate"
            elif abs(x - GATE_X) == 2 and z > 14:
                block = "minecraft:deepslate_bricks"
            else:
                block = field
            p.set(x, 1, z, block)


def _sanctum_ceiling(p):
    """Beams at y10 on a grid that lands on the pillars and pilasters; coffers between them
    step up to lids of glowing deepslate shadow ore."""
    rx0, rz0, rx1, rz1 = ROOM
    xs, zs = (rx0, 18, 22, rx1), (rz0, 12, 16, rz1)
    for x in range(rx0, rx1 + 1):
        for z in range(rz0, rz1 + 1):
            if x in xs or z in zs:
                p.set(x, 10, z, "minecraft:polished_deepslate")
    for a, b in zip(xs, xs[1:]):
        for c, d in zip(zs, zs[1:]):
            _coffer(p, a + 1, c + 1, b - 1, d - 1, 10, SHADOW_ORE)
    # a cornice of upside-down stairs under the perimeter beams
    for x in range(rx0, rx1 + 1):
        for z in range(rz0, rz1 + 1):
            fz = "north" if z == rz0 else "south" if z == rz1 else None
            fx = "west" if x == rx0 else "east" if x == rx1 else None
            if fz and fx:
                p.stairs(x, 9, z, "deepslate_tiles", fz, half="top", shape=_corner(fz, fx, "inner"))
            elif fz or fx:
                p.stairs(x, 9, z, "deepslate_tiles", fz or fx, half="top")
    # soul lanterns hanging off the inner beams
    for x, z in ((GATE_X, 12), (GATE_X, 16), (18, 14), (22, 14), (15, 12), (25, 12), (15, 16), (25, 16)):
        p.hanging_lantern(x, 8, z, chain=1, soul=True)


def _sanctum_walls(p):
    """Pilasters under every beam end, candle niches, tinted-glass slits into the corridor."""
    rx0, rz0, rx1, rz1 = ROOM
    _trim(p, rx0 - 1, rz0 - 1, rx1 + 1, rz1 + 1, 2, "minecraft:polished_deepslate")
    pilasters = [(x, z) for x in (18, 22) for z in (rz0, rz1)] + \
                [(x, z) for x in (rx0, rx1) for z in (12, 16)] + \
                [(x, z) for x in (rx0, rx1) for z in (rz0, rz1)]
    for x, z in pilasters:
        p.set(x, 2, z, "minecraft:chiseled_deepslate")
        p.fill(x, 3, z, x, 8, z, "minecraft:polished_deepslate")
        p.set(x, 9, z, "minecraft:chiseled_deepslate")
    # east and west walls: niches in the side bays, a glass slit in the middle bay
    for wx, out in ((rx0 - 1, "east"), (rx1 + 1, "west")):
        for z0 in (9, 18):
            p.clear((wx, 3, z0, wx, 4, z0 + 1))
            p.slab(wx, 5, z0, "polished_deepslate", type="top")
            p.slab(wx, 5, z0 + 1, "polished_deepslate", type="top")
            p.candle(wx, 3, z0, "purple", candles=3)
            p.skull(wx, 3, z0 + 1, rotation=12 if out == "east" else 4)
        p.fill(wx - 1 if out == "east" else wx, 4, 13, wx if out == "east" else wx + 1, 6, 15, "minecraft:tinted_glass")
        p.set(wx, 3, 14, SHADOW)
        p.set(wx, 7, 14, SHADOW)
    # south wall: tinted windows either side of the gate
    for x0 in (15, 24):
        p.fill(x0, 4, rz1 + 1, x0 + 1, 5, rz1 + 2, "minecraft:tinted_glass")
    # north wall: candle niches in the outer bays
    for x0 in (15, 24):
        p.clear((x0, 3, rz0 - 1, x0 + 1, 4, rz0 - 1))
        p.candle(x0, 3, rz0 - 1, "black", candles=2)
        p.candle(x0 + 1, 3, rz0 - 1, "purple", candles=4)
        p.set(x0, 2, rz0 - 1, SHADOW)
        p.set(x0 + 1, 2, rz0 - 1, SHADOW)


def _sanctum_pillars(p):
    """Four shadow block pillars carrying the beam crossings, with stepped bases and capitals."""
    for x in (18, 22):
        for z in (12, 16):
            p.set(x, 2, z, "minecraft:chiseled_deepslate")
            p.fill(x, 3, z, x, 9, z, SHADOW)
            for d, (dx, dz) in (("west", (1, 0)), ("east", (-1, 0)), ("north", (0, 1)), ("south", (0, -1))):
                p.stairs(x + dx, 2, z + dz, "polished_deepslate", d)
                p.stairs(x + dx, 9, z + dz, "polished_deepslate", d, half="top")


def _dais(p):
    """Two-step dais against the north wall, the main chest on top between shadow plinths,
    a reredos of crying obsidian and tinted glass behind."""
    rz0 = ROOM[1]
    p.fill(17, 2, rz0, 23, 2, rz0 + 3, "minecraft:polished_deepslate")
    for x in range(17, 24):
        p.stairs(x, 2, rz0 + 4, "polished_deepslate", "north")
    for z in range(rz0, rz0 + 4):
        p.stairs(16, 2, z, "polished_deepslate", "east")
        p.stairs(24, 2, z, "polished_deepslate", "west")
    p.stairs(16, 2, rz0 + 4, "polished_deepslate", "north", shape="outer_right")
    p.stairs(24, 2, rz0 + 4, "polished_deepslate", "north", shape="outer_left")
    p.set(17, 2, rz0 + 3, "minecraft:crying_obsidian")
    p.set(23, 2, rz0 + 3, "minecraft:crying_obsidian")
    # upper step
    p.fill(19, 3, rz0, 21, 3, rz0 + 2, "minecraft:deepslate_tiles")
    for x in range(19, 22):
        p.stairs(x, 3, rz0 + 3, "deepslate_tiles", "north")
    for z in range(rz0 + 1, rz0 + 3):
        p.stairs(18, 3, z, "deepslate_tiles", "east")
        p.stairs(22, 3, z, "deepslate_tiles", "west")
    p.chest(GATE_X, 4, rz0 + 1, "shadow_vault", "south")
    for x in (19, 21):
        p.set(x, 4, rz0, SHADOW)
        p.candle(x, 5, rz0, "purple", candles=3)
        p.candle(x, 4, rz0 + 2, "black", candles=1)
    for x in (17, 23):
        p.lantern(x, 3, rz0 + 3, soul=True)
    # reredos in the north wall
    wz = rz0 - 1
    for y in range(3, 9):
        p.set(19, y, wz, "minecraft:crying_obsidian")
        p.set(21, y, wz, "minecraft:crying_obsidian")
        p.set(GATE_X, y, wz, "minecraft:tinted_glass" if 5 <= y <= 7 else SHADOW)
    p.set(GATE_X, 8, wz, SHADOW_ORE)
    p.set(GATE_X, 4, wz, "minecraft:chiseled_deepslate")


def _braziers_and_sentinels(p):
    """Soul-fire braziers in the four floor corners; two skull-topped sentinel posts inside
    the gate; relic shelves flanking the candle niches in the side walls."""
    rx0, rz0, rx1, rz1 = ROOM
    for x, z in ((rx0 + 1, rz0 + 1), (rx1 - 1, rz0 + 1), (rx0 + 1, rz1 - 1), (rx1 - 1, rz1 - 1)):
        p.set(x, 2, z, "minecraft:chiseled_deepslate")
        p.set(x, 3, z, "minecraft:soul_campfire[facing=south,lit=true,signal_fire=false,waterlogged=false]")
    for x in (GATE_X - 2, GATE_X + 2):
        p.wall(x, 2, rz1 - 1, "polished_deepslate")
        p.wall(x, 3, rz1 - 1, "polished_deepslate")
        p.set(x, 4, rz1 - 1, "minecraft:wither_skeleton_skull[powered=false,rotation=0]")
    for x, facing in ((rx0, "east"), (rx1, "west")):
        for z in (8, 11, 17, 20):
            p.slab(x, 3, z, "polished_deepslate", type="top")
        p.set(x, 4, 17, "minecraft:amethyst_cluster[facing=up,waterlogged=false]")
        p.candle(x, 4, 20, "purple", candles=2)
        p.set(x, 4, 11, f"minecraft:decorated_pot[cracked=false,facing={facing},waterlogged=false]")
        p.candle(x, 4, 8, "black", candles=1)


def _corridor_niches(p):
    """Shallow niches in the corridor's outer wall between the ribs: candles and skulls."""
    spots = [(7, z, "east") for z in (5, 11, 17, 23)] + [(33, z, "west") for z in (5, 11, 17, 23)] + \
            [(x, 1, "south") for x in (11, 17, 23, 29)] + [(x, 27, "north") for x in (11, 29)]
    rot = {"east": 12, "west": 4, "south": 0, "north": 8}
    for i, (x, z, facing) in enumerate(spots):
        p.set(x, 3, z, AIR)
        p.set(x, 2, z, "minecraft:polished_deepslate")
        p.slab(x, 4, z, "polished_deepslate", type="top")
        if i % 2:
            p.skull(x, 3, z, rotation=rot[facing])
        else:
            p.candle(x, 3, z, "purple" if i % 4 else "white", candles=1 + i % 3)


# ------------------------------------------------------------------ the gate
def _gate(p):
    """South wall of the sanctum: an arch on the inside, iron bars either side of an iron door
    on the corridor face, a lintel with a lever that opens it. The corridor guardian waits
    in front of it."""
    wz_in, wz_out = ROOM[3] + 1, ROOM[3] + 2
    p.clear((GATE_X - 1, 2, wz_in, GATE_X + 1, 3, wz_in))
    p.set(GATE_X, 4, wz_in, AIR)
    p.stairs(GATE_X - 1, 4, wz_in, "polished_deepslate", "west", half="top")
    p.stairs(GATE_X + 1, 4, wz_in, "polished_deepslate", "east", half="top")
    for x in (GATE_X - 1, GATE_X + 1):
        for y in (2, 3, 4):
            p.bars(x, y, wz_out)
    p.set(GATE_X, 2, wz_out, "minecraft:iron_door[facing=north,half=lower,hinge=left,open=false,powered=false]")
    p.set(GATE_X, 3, wz_out, "minecraft:iron_door[facing=north,half=upper,hinge=left,open=false,powered=false]")
    p.set(GATE_X, 4, wz_out, "minecraft:chiseled_deepslate")
    p.set(GATE_X, 4, wz_out + 1, "minecraft:lever[face=wall,facing=south,powered=false]")
    for x in (GATE_X - 2, GATE_X + 2):
        p.fill(x, 2, wz_out, x, 4, wz_out, "minecraft:polished_deepslate")
        p.set(x, 5, wz_out, "minecraft:chiseled_deepslate")
    p.spawner(GATE_X, 2, wz_out + 2, GUARDIAN)


# ------------------------------------------------------------------ alcoves
def _alcove_room(p, x0, x1, opening):
    """Carve a 5 x 5 alcove (z 12..16) with a vaulted top and a patterned floor."""
    p.clear((x0, 2, 12, x1, 4, 16))
    p.clear((x0, 5, 13, x1, 5, 15))
    for x in range(x0, x1 + 1):
        p.stairs(x, 5, 12, "deepslate_tiles", "north", half="top")
        p.stairs(x, 5, 16, "deepslate_tiles", "south", half="top")
        for z in range(12, 17):
            edge = x in (x0, x1) or z in (12, 16)
            p.set(x, 1, z, "minecraft:deepslate_tiles" if edge else "minecraft:polished_deepslate")
    p.set((x0 + x1) // 2, 1, 14, SHADOW)
    if opening is not None:
        ox, step = opening
        for x in (ox, ox + step):
            p.clear((x, 2, 13, x, 3, 15))
            p.set(x, 4, 14, AIR)
            p.stairs(x, 4, 13, "polished_deepslate", "north", half="top")
            p.stairs(x, 4, 15, "polished_deepslate", "south", half="top")
            p.set(x, 1, 14, "minecraft:polished_deepslate")
            p.set(x, 1, 13, "minecraft:deepslate_tiles")
            p.set(x, 1, 15, "minecraft:deepslate_tiles")


def _west_alcove(p):
    """Open alcove off the west corridor: a cache between two candle plinths, a bent grille."""
    _alcove_room(p, 1, 5, (6, 1))
    p.chest(1, 2, 14, "shadow_vault", "east")
    for z in (13, 15):
        p.set(1, 2, z, SHADOW)
        p.candle(1, 3, z, "purple", candles=2)
    p.set(2, 2, 12, "minecraft:decorated_pot[cracked=true,facing=east,waterlogged=false]")
    p.skull(4, 2, 16, rotation=6)
    p.lantern(5, 2, 12, soul=True)
    p.bars(6, 3, 13)
    p.bars(6, 3, 15)
    p.set(1, 4, 12, "minecraft:cobweb")
    p.set(5, 4, 16, "minecraft:cobweb")


def _east_alcove(p):
    """Hidden alcove behind a false wall in the east corridor: the corridor face is all
    cracked bricks over a rubble fill, with a candle and a vein trail in front. Inside, dark,
    the remains of whoever sealed it and the last cache."""
    _alcove_room(p, 35, 39, None)
    p.fill(33, 2, 13, 33, 4, 15, "minecraft:cracked_deepslate_bricks")
    p.fill(34, 2, 13, 34, 4, 15, "minecraft:cobbled_deepslate")
    p.candle(32, 2, 14, "white", candles=1)
    p.chest(39, 2, 14, "shadow_vault", "west")
    p.set(36, 2, 15, "minecraft:bone_block[axis=x]")
    p.skull(37, 2, 15, rotation=3)
    p.set(36, 2, 13, "minecraft:sculk")
    p.candle(38, 2, 12, "black", candles=3, lit=False)
    p.set(40, 3, 14, SHADOW_ORE)
    for x, y, z in ((35, 4, 12), (39, 4, 16), (39, 4, 12), (35, 4, 16), (37, 5, 13)):
        p.set(x, y, z, "minecraft:cobweb")


# ------------------------------------------------------------------ guard hall
def _guard_hall(p):
    """South of the ring: the guards' hall, barrel-vaulted, its old entrance walled up with
    rubble that has slumped inward."""
    x0, z0, x1, z1 = 16, 29, 24, 33
    worn = p.mix(("minecraft:deepslate_bricks", 3), ("minecraft:cracked_deepslate_bricks", 1))
    p.clear((x0, 2, z0, x1, 4, z1))
    p.clear((x0, 5, z0 + 1, x1, 5, z1 - 1))
    p.clear((x0, 6, z0 + 2, x1, 7, z1 - 2))
    for x in range(x0, x1 + 1):
        p.stairs(x, 5, z0, "deepslate_tiles", "north", half="top")
        p.stairs(x, 5, z1, "deepslate_tiles", "south", half="top")
        p.stairs(x, 6, z0 + 1, "deepslate_tiles", "north", half="top")
        p.stairs(x, 6, z1 - 1, "deepslate_tiles", "south", half="top")
        for z in range(z0, z1 + 1):
            edge = x in (x0, x1) or z in (z0, z1)
            p.set(x, 1, z, "minecraft:polished_deepslate" if edge else worn)
    for x in range(18, 23):
        p.set(x, 1, 31, "minecraft:deepslate_tiles")
    p.set(GATE_X, 1, 31, "minecraft:chiseled_deepslate")
    _trim(p, x0 - 1, z0 - 1, x1 + 1, z1 + 1, 2, "minecraft:polished_deepslate")
    # arch to the corridor through the ring wall
    for z in (27, 28):
        p.clear((18, 2, z, 22, 4, z))
        p.clear((19, 5, z, 21, 5, z))
        p.stairs(18, 5, z, "polished_deepslate", "west", half="top")
        p.stairs(22, 5, z, "polished_deepslate", "east", half="top")
        for x in range(18, 23):
            p.set(x, 1, z, "minecraft:polished_deepslate")
    # benches along the west wall, a table and stool on the east
    for z in range(30, 33):
        p.stairs(x0, 2, z, "deepslate_tiles", "west")
    p.fence(23, 2, 31, "dark_oak")
    p.set(23, 3, 31, "minecraft:dark_oak_pressure_plate[powered=false]")
    p.stairs(x1, 2, 31, "dark_oak", "east")
    p.stairs(23, 2, 30, "dark_oak", "north")
    p.skull(x0 + 1, 2, 33, rotation=9)
    p.set(x1, 2, 33, "minecraft:bone_block[axis=y]")
    p.set(x1, 2, z0, "minecraft:barrel[facing=up,open=false]")
    p.set(x1, 3, z0, "minecraft:barrel[facing=west,open=false]")
    for x in (17, 23):
        p.wall_torch(x, 4, z0, "south", soul=True)
    p.hanging_lantern(GATE_X, 6, 31, chain=1, soul=True)
    # the old entrance, walled up and slumped
    rubble = p.mix(("minecraft:cobbled_deepslate", 4), ("minecraft:gravel", 2), ("minecraft:tuff", 2),
                   ("minecraft:cracked_deepslate_bricks", 1))
    for x in (GATE_X - 2, GATE_X + 2):
        p.fill(x, 2, z1 + 1, x, 4, z1 + 1, "minecraft:chiseled_deepslate")
    p.fill(GATE_X - 2, 5, z1 + 1, GATE_X + 2, 5, z1 + 1, "minecraft:polished_deepslate")
    p.fill(GATE_X - 1, 2, z1 + 1, GATE_X + 1, 4, z1 + 2, rubble)
    p.stairs(GATE_X - 1, 2, z1, "cobbled_deepslate", "south")
    p.set(GATE_X, 2, z1, "minecraft:gravel")
    p.slab(GATE_X + 1, 2, z1, "cobbled_deepslate")
    p.slab(GATE_X, 3, z1, "cobbled_deepslate")


# ------------------------------------------------------------------ age
def _collapse(p):
    """The south-east corner of the corridor has fallen in: a rubble slope, broken vault."""
    rubble = p.mix(("minecraft:cobbled_deepslate", 4), ("minecraft:gravel", 2), ("minecraft:tuff", 2),
                   ("minecraft:cracked_deepslate_tiles", 1))
    for x in range(30, 33):
        for z in range(24, 27):
            h = max(0, (x - 30) + (z - 24) - 1)
            if h:
                p.fill(x, 2, z, x, 1 + h, z, rubble)
                p.slab(x, 2 + h, z, "cobbled_deepslate")
    p.set(32, 5, 26, rubble)
    p.set(31, 6, 25, rubble)
    p.set(32, 5, 25, "minecraft:cobbled_deepslate")
    p.slab(30, 2, 24, "tuff")


def _sculk_and_cobwebs(p):
    """Sculk creeping along the north and east corridor, cobwebs in the vaults."""
    rnd = p.rnd
    for cx, cz, r in ((14, 3, 2), (31, 9, 2), (26, 3, 1), (31, 18, 1)):
        for x in range(cx - r, cx + r + 1):
            for z in range(cz - r, cz + r + 1):
                if not _in_corridor(x, z) or rnd.random() > 0.7:
                    continue
                if rnd.random() < 0.55:
                    p.set(x, 1, z, "minecraft:sculk")
                elif p.get(x, 2, z) == AIR:
                    p.set(x, 2, z, "minecraft:sculk_vein[down=true,east=false,north=false,south=false,up=false,"
                                   "waterlogged=false,west=false]")
    p.set(31, 1, 9, "minecraft:sculk_catalyst[bloom=false]")
    # a vein trail toward the false wall
    for z in (11, 12, 13):
        p.set(32, 2, z, "minecraft:sculk_vein[down=true,east=false,north=false,south=false,up=false,"
                        "waterlogged=false,west=false]")
    ox0, oz0, ox1, oz1 = CORRIDOR_OUT
    for x in range(ox0, ox1 + 1):
        for z in range(oz0, oz1 + 1):
            if _in_corridor(x, z) and p.get(x, 6, z) == AIR and rnd.random() < 0.08:
                p.set(x, 6, z, "minecraft:cobweb")
    for x, y, z in ((8, 4, 2), (32, 4, 2), (8, 4, 26), (10, 4, 24), (14, 9, 8), (26, 9, 20), (26, 11, 8)):
        if p.get(x, y, z) == AIR:
            p.set(x, y, z, "minecraft:cobweb")


PLACE = {
    "name": "shadow_vault",
    "pieces": {"shadow_vault": build},
    "step": "underground_structures",
    "start_height": (-52, -12),
    "surface": False,
    "terrain": "none",
    "biomes": [
        "#minecraft:is_overworld",
    ],
    "spacing": 22,
    "separation": 8,
    "salt": 418200106,
}
