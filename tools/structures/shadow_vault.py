"""Shadow vault: a deepslate vault about 38 blocks under a small blackstone mausoleum, joined
by a square spiral stair in a closed shaft. Brief: docs/design/places.md section 6.

One surface-anchored piece, 41 x 52 x 48 (x east, y up, z south):

  y 37        ground layer (replaces the world's top block): a blighted patch of coarse dirt
              and soul soil with a path to the north door; air is set over the patch.
  y 38..51    the mausoleum over the shaft mouth (x 12..22, z 2..12): blackstone walls with
              corner piers, a hipped roof with a glowing shadow ore finial, an altar on the
              stair core, and the railed stair mouth in the floor's south-west.
  y 0..37     the shaft (same footprint): an 11 x 11 closed shell round a 3 x 3 core; a stair
              3 wide winds down three turns (corner landings, 3 steps per side, 12 a turn)
              from the mausoleum floor to a landing at y 1 against the vault's north wall.
  y 0..13     the vault, z 12..47 (pasted from its own 41 x 14 x 36 build, unchanged apart
              from the new doorway at x 16..18 through its north wall):

    west alcove | ring corridor (3 wide, rib-vaulted) | hidden east alcove
                |   sanctum (15 x 15, coffered)       |  (behind a false wall)
                |   guard hall to the south with the walled-up old entrance

The sanctum is entered through an iron gate in its south wall (iron door between iron bars,
opened by a lever on the lintel). Main chest on the dais under a ceiling of glowing shadow
ore; one cache in each alcove; one small cache on a landing half way down the stair. Vault
guardian spawners: in the corridor in front of the gate, and on the sanctum floor.
"""
from structkit import AIR, NS, OPPOSITE, Piece, ccw, state

VW, VH, VD = 41, 14, 36            # the vault on its own (vault-local coordinates below)
SHADOW = f"{NS}:shadowblock"
SHADOW_ORE = f"{NS}:deepslate_shadow_ore"
SURFACE_ORE = f"{NS}:shadowore"
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

# ---- the whole piece (piece coordinates)
VZ = 12                              # the vault's z offset: its north wall is the shaft's south wall
GROUND = 37                          # the ground layer (vault floor at y 1, so ~38 blocks down)
W, H, D = VW, 52, VZ + VD            # 41 x 52 x 48
SX0, SZ0 = 12, 2                     # shaft / mausoleum outer box x 12..22, z 2..12
SX1, SZ1 = SX0 + 10, SZ0 + 10
IX, IZ = SX0 + 1, SZ0 + 1            # interior origin: (u, v) = (x - IX, z - IZ), 0..8
CX, CZ = SX0 + 5, SZ0 + 5            # centre column (17, 7); the core is u, v 3..5
DOOR_X = CX                          # the north door, the stair mouth and the vault doorway
BOTTOM, TOP = 2, GROUND + 1          # standing heights of the bottom and top landings
EAVE = GROUND + 6                    # wall top and lowest roof course (y 43)

# the stair, walking UP (a turn: east side north, north side west, west side south, south
# side east). Each side: f(step, lane) -> (u, v) and the stairs' facing (= the way up).
# Lane 0 is the outer lane (against the shaft wall), lane 2 the inner (against the core).
SIDE_CELLS = {
    "E": (lambda i, j: (8 - j, 5 - i), "north"),
    "N": (lambda i, j: (5 - i, j), "west"),
    "W": (lambda i, j: (j, 3 + i), "south"),
    "S": (lambda i, j: (3 + i, 8 - j), "east"),
}
CORNER_AFTER = {"E": "NE", "N": "NW", "W": "SW", "S": "SE"}
CORNERS = {"NE": (6, 0), "NW": (0, 0), "SW": (0, 6), "SE": (6, 6)}
CORE_STEP = {"E": (-1, 0), "N": (0, 1), "W": (1, 0), "S": (0, -1)}     # inner lane -> core face
OUTWARD = {"E": "east", "N": "north", "W": "west", "S": "south"}
FIND = ("NW", 20)                    # the landing with the small cache


def build():
    p = Piece("shadow_vault", W, H, D, "vault_entry")
    p.paste(_vault(), 0, 0, VZ)
    _vault_doorway(p)
    _shaft(p)
    _ground(p)
    _mausoleum(p)
    return p


def _vault():
    """The vault exactly as it was designed, on its own piece (and its own seed)."""
    p = Piece("shadow_vault_vault", VW, VH, VD, "vault")
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


# ================================================================== the way in
def _flight():
    """The stair's treads from the bottom up: (cells [(u, v)], stand, facing, label). `stand`
    is the height a player stands at (the tread block is at stand - 1); facing is the stairs'
    facing (None for a landing); label is the side or corner name."""
    corner = lambda name: [(CORNERS[name][0] + a, CORNERS[name][1] + b)  # noqa: E731
                           for a in range(3) for b in range(3)]
    out = [([(u, v) for u in range(3, 6) for v in range(6, 9)], BOTTOM, None, "S"),
           (corner("SE"), BOTTOM, None, "SE")]
    s, k = BOTTOM, 0
    while s < TOP:
        side = "ENWS"[k % 4]
        cells, facing = SIDE_CELLS[side]
        for i in range(3):
            out.append(([cells(i, j) for j in range(3)], s + i + 1, facing, side))
        s += 3
        out.append((corner(CORNER_AFTER[side]), s, None, CORNER_AFTER[side]))
        k += 1
    assert s == TOP, s
    return out


def _stands():
    """{(u, v): sorted stands} over the walkway."""
    cols = {}
    for cells, stand, _, _ in _flight():
        for c in cells:
            cols.setdefault(c, []).append(stand)
    return {c: sorted(v) for c, v in cols.items()}


def _floor_over(stand_top):
    """How the mausoleum floor (y GROUND) treats a column whose highest tread is stand_top:
    2 = a two-thick floor, 1 = floor at GROUND only, 0 = open (stair mouth)."""
    if stand_top >= TOP:
        return 1                      # the top landing / top step is itself in the floor
    if stand_top + 2 < GROUND - 1:
        return 2
    if stand_top + 2 < GROUND:
        return 1
    return 0


def _vault_doorway(p):
    """A doorway 3 wide and 3 high through the vault's north wall (vault z 0..1) from the
    stair's bottom landing into the north run of the ring corridor, between two ribs (it
    replaces one candle niche). Chiseled jambs and a polished lintel with a glowing keystone."""
    z0, z1 = VZ, VZ + 1
    for z in (z0, z1):
        for x in (DOOR_X - 2, DOOR_X + 2):
            p.set(x, 2, z, "minecraft:chiseled_deepslate")
            p.fill(x, 3, z, x, 4, z, "minecraft:polished_deepslate")
        p.clear((DOOR_X - 1, 2, z, DOOR_X + 1, 4, z))
        for x in range(DOOR_X - 1, DOOR_X + 2):
            p.set(x, 1, z, "minecraft:polished_deepslate")
            p.set(x, 0, z, "minecraft:deepslate_bricks")
            p.set(x, 5, z, "minecraft:polished_deepslate")
        p.set(DOOR_X, 5, z, "minecraft:chiseled_deepslate")
    p.set(DOOR_X, 5, z0, SHADOW_ORE)          # a glowing keystone over the shaft side
    p.set(DOOR_X, 1, z0, "minecraft:chiseled_deepslate")


# ------------------------------------------------------------------ the shaft
def _shaft(p):
    masonry = p.mix(("minecraft:deepslate_bricks", 7), ("minecraft:cracked_deepslate_bricks", 4),
                    ("minecraft:deepslate_tiles", 2), ("minecraft:cracked_deepslate_tiles", 1),
                    ("minecraft:cobbled_deepslate", 2), (SHADOW_ORE, 0.12))
    # the shell: walls from y 0 to the ground layer (the vault's own wall is kept where it is)
    for y in range(0, GROUND + 1):
        for x in range(SX0, SX1 + 1):
            for z in range(SZ0, SZ1 + 1):
                if (x in (SX0, SX1) or z in (SZ0, SZ1)) and not p.is_set(x, y, z):
                    p.set(x, y, z, masonry)
    # a polished band on the inside of the wall once a turn, at the south landing heights
    for y in (13, 25):
        for x in range(SX0, SX1 + 1):
            for z in range(SZ0, SZ1 + 1):
                if x in (SX0, SX1) or z in (SZ0, SZ1):
                    p.set(x, y, z, "minecraft:polished_deepslate")
    # the core: polished corners, brick faces, a chiseled course at every turn
    for y in range(0, GROUND + 1):
        for u in range(3, 6):
            for v in range(3, 6):
                corner = u != 4 and v != 4
                b = "minecraft:polished_deepslate" if corner else masonry()
                if y % 12 == 1 and corner:
                    b = "minecraft:chiseled_deepslate"
                p.set(IX + u, y, IZ + v, b)
    _treads(p)
    _core_niches(p)
    _landing_details(p)
    _shaft_age(p)


def _treads(p):
    """Stairs and landings, the sloped soffit under each run, air between turns, solid fill
    under the first turn."""
    tread = p.mix(("deepslate_tiles", 5), ("deepslate_bricks", 3), ("cobbled_deepslate", 2),
                  ("polished_deepslate", 2))
    landing = p.mix(("minecraft:deepslate_tiles", 6), ("minecraft:cracked_deepslate_tiles", 3),
                    ("minecraft:polished_deepslate", 2))
    fill = p.mix(("minecraft:deepslate_bricks", 5), ("minecraft:cobbled_deepslate", 3),
                 ("minecraft:deepslate[axis=y]", 2))
    cols = _stands()
    by_cell = {}
    for cells, stand, facing, label in _flight():
        for c in cells:
            by_cell[(c, stand)] = (facing, label)
    for (u, v), stands in sorted(cols.items()):
        x, z = IX + u, IZ + v
        below = 0
        for n, s in enumerate(stands):
            facing, label = by_cell[((u, v), s)]
            if n == 0:
                p.fill(x, 0, z, x, s - 2, z, fill)
            else:
                p.clear((x, below, z, x, s - 3, z))
                if facing:
                    p.stairs(x, s - 2, z, "deepslate_tiles", OPPOSITE[facing], half="top")
                else:
                    p.set(x, s - 2, z, fill)
            if facing:
                p.stairs(x, s - 1, z, tread(), facing)
            else:
                edge = u in (0, 8) or v in (0, 8) or label in ("S",) and v == 8
                p.set(x, s - 1, z, "minecraft:polished_deepslate" if edge and (u + v) % 2 else landing())
            below = s
        mode = _floor_over(stands[-1])
        if stands[-1] < TOP:
            top_air = GROUND - (1 if mode else 0) - (1 if mode == 2 else 0)
            p.clear((x, below, z, x, top_air, z))
    # bottom landing: a chiseled square before the doorway
    for u in range(3, 6):
        p.set(IX + u, 1, IZ + 8, "minecraft:polished_deepslate")
    p.set(DOOR_X, 1, IZ + 7, "minecraft:chiseled_deepslate")


def _core_niches(p):
    """A niche in the core face beside the middle step of every side, at eye height: soul
    lanterns, candles and skulls in turn."""
    k = 0
    for cells, stand, facing, side in _flight():
        if not facing or cells[0] != SIDE_CELLS[side][0](1, 0):
            continue
        u, v = SIDE_CELLS[side][0](1, 2)
        du, dv = CORE_STEP[side]
        x, z, y = IX + u + du, IZ + v + dv, stand + 1
        if y + 1 >= GROUND:
            continue
        p.set(x, y - 1, z, "minecraft:polished_deepslate")
        p.set(x, y + 1, z, "minecraft:chiseled_deepslate")
        kind = k % 3
        if kind == 0:
            p.lantern(x, y, z, soul=True)
        elif kind == 1:
            p.candle(x, y, z, "purple" if k % 2 else "black", candles=3)
        else:
            p.skull(x, y, z, rotation={"S": 0, "W": 4, "N": 8, "E": 12}[side])
        k += 1


def _landing_details(p):
    """On each corner landing's outer corner: candles or a soul lantern; the small cache on
    one landing half way down; bones and a skull on the bottom landing."""
    for cells, stand, facing, label in _flight():
        if facing or label not in CORNERS or stand in (BOTTOM, TOP):
            continue
        cu, cv = CORNERS[label]
        u, v = cu + (0 if cu == 0 else 2), cv + (0 if cv == 0 else 2)
        x, y, z = IX + u, stand, IZ + v
        if (label, stand) == FIND:
            p.chest(x, y, z, "shadow_vault", "south" if cv == 0 else "north")
            p.set(x + (1 if cu == 0 else -1), y, z, "minecraft:cobweb")
            continue
        if (stand // 3) % 2:
            p.lantern(x, y, z, soul=True)
        else:
            p.candle(x, y, z, "purple", candles=1 + stand % 4)
    # the bottom landing: bones in the corner, a lantern niche in the core facing the door
    p.set(IX + 8, BOTTOM, IZ + 8, "minecraft:bone_block[axis=x]")
    p.skull(IX + 8, BOTTOM + 1, IZ + 8, rotation=6)
    x, z = CX, IZ + 5
    p.set(x, BOTTOM + 2, z, "minecraft:chiseled_deepslate")
    p.lantern(x, BOTTOM + 1, z, soul=True)
    p.set(x, BOTTOM, z, "minecraft:polished_deepslate")


def _shaft_age(p):
    """Cobwebs high in the open space over the stair (never in its headroom), glow lichen
    and sculk veins on the walls."""
    rnd = p.rnd
    cols = _stands()
    for (u, v), stands in sorted(cols.items()):
        x, z = IX + u, IZ + v
        outer = [d for d, (du, dv) in (("west", (-1, 0)), ("east", (1, 0)), ("north", (0, -1)), ("south", (0, 1)))
                 if not (0 <= u + du <= 8 and 0 <= v + dv <= 8)]
        for y in range(2, GROUND):
            if p.get(x, y, z) != AIR:
                continue
            under = max((s for s in stands if s <= y), default=None)
            if under is None:
                continue
            high = y - under >= 3
            if outer and high and rnd.random() < 0.05:
                p.set(x, y, z, "minecraft:cobweb")
            elif outer and rnd.random() < 0.025:
                side = outer[0]
                if y < 9:
                    p.set(x, y, z, state("minecraft:sculk_vein", down=False, up=False, waterlogged=False,
                                         **{d: d == side for d in ("north", "east", "south", "west")}))
                else:
                    p.set(x, y, z, state("minecraft:glow_lichen", down=False, up=False, waterlogged=False,
                                         **{d: d == side for d in ("north", "east", "south", "west")}))
    # webs in the bottom landing's corners and over the doorway
    for x, y, z in ((IX + 3, 6, IZ + 8), (IX + 5, 7, IZ + 6), (IX + 8, 5, IZ + 8)):
        if p.get(x, y, z) == AIR:
            p.set(x, y, z, "minecraft:cobweb")


# ------------------------------------------------------------------ the surface
def _ground(p):
    """An irregular patch of blighted ground (the layer that replaces the world's top block)
    with air over it, a path to the north door and a little debris."""
    rnd = p.rnd
    cx, cz = CX, CZ + 1
    for x in range(W):
        for z in range(D):
            if SX0 <= x <= SX1 and SZ0 <= z <= SZ1:
                continue
            r = ((x - cx) / 10.5) ** 2 + ((z - cz) / 9.5) ** 2
            if r > 1 + rnd.uniform(-0.18, 0.08):
                continue
            near = max(abs(x - CX), abs(z - CZ)) <= 7
            if near:
                b = _pick(p, ("minecraft:coarse_dirt", 4), ("minecraft:soul_soil", 3), ("minecraft:gravel", 2),
                          ("minecraft:cobbled_deepslate", 2), ("minecraft:blackstone", 1), ("minecraft:tuff", 1))
            else:
                b = _pick(p, ("minecraft:coarse_dirt", 6), ("minecraft:soul_soil", 2), ("minecraft:gravel", 1),
                          ("minecraft:dirt", 2), ("minecraft:rooted_dirt", 1))
            p.set(x, GROUND, z, b)
            for y in range(GROUND + 1, H):
                p.set(x, y, z, AIR)
            if b == "minecraft:coarse_dirt" and not near and rnd.random() < 0.08:
                p.set(x, GROUND + 1, z, "minecraft:dead_bush")
    for x in range(SX0, SX1 + 1):
        for z in range(SZ0, SZ1 + 1):
            for y in range(GROUND + 1, H):
                p.set(x, y, z, AIR)
    # the path north from the door, edged with rubble
    for z in range(0, SZ0):
        for x in range(DOOR_X - 1, DOOR_X + 2):
            p.set(x, GROUND, z, _pick(p, ("minecraft:polished_blackstone_bricks", 3),
                                      ("minecraft:cracked_polished_blackstone_bricks", 3),
                                      ("minecraft:cobbled_deepslate", 2), ("minecraft:gravel", 1)))
    # lantern posts either side of the path
    for x in (DOOR_X - 3, DOOR_X + 3):
        p.set(x, GROUND, 0, "minecraft:polished_blackstone")
        p.wall(x, GROUND + 1, 0, "polished_blackstone")
        p.wall(x, GROUND + 2, 0, "polished_blackstone")
        p.lantern(x, GROUND + 3, 0, soul=True)
    # debris fallen from the roof and walls
    for x, z, kind in ((9, 6, "slab"), (10, 10, "block"), (25, 9, "stairs"), (24, 13, "slab"),
                       (14, 15, "block"), (21, 15, "stairs"), (26, 4, "block"), (8, 12, "slab")):
        if p.get(x, GROUND, z) in (None, AIR):
            continue
        if kind == "slab":
            p.slab(x, GROUND + 1, z, p.rnd.choice(("polished_blackstone_bricks", "cobbled_deepslate")))
        elif kind == "stairs":
            p.stairs(x, GROUND + 1, z, "polished_blackstone_bricks", p.rnd.choice(("north", "east", "south", "west")))
        else:
            p.set(x, GROUND + 1, z, p.rnd.choice(("minecraft:cracked_polished_blackstone_bricks",
                                                 "minecraft:cobbled_deepslate", "minecraft:blackstone")))
    p.skull(10, GROUND + 1, 3, rotation=10)
    p.set(24, GROUND + 1, 6, "minecraft:bone_block[axis=z]")


def _pick(p, *weighted):
    names, weights = zip(*weighted)
    return p.rnd.choices(names, weights)[0]


def _mausoleum(p):
    _mausoleum_floor(p)
    _mausoleum_walls(p)
    _mausoleum_roof(p)
    _altar(p)
    _mausoleum_details(p)


def _mausoleum_floor(p):
    """The floor over the shaft (y GROUND): blackstone over the covered turns of the stair,
    the stair mouth open in the south-west, the top landing marked with glowing ore."""
    cols = _stands()
    for (u, v), stands in cols.items():
        x, z = IX + u, IZ + v
        mode = _floor_over(stands[-1])
        if stands[-1] >= TOP:
            if "_stairs" not in p.get(x, GROUND, z):
                p.set(x, GROUND, z, "minecraft:polished_blackstone" if (u + v) % 2 else
                      "minecraft:polished_blackstone_bricks")
            continue
        if mode == 0:
            p.set(x, GROUND, z, AIR)
            continue
        outer = u in (0, 8) or v in (0, 8)
        p.set(x, GROUND, z, _pick(p, ("minecraft:polished_blackstone_bricks", 4),
                                  ("minecraft:cracked_polished_blackstone_bricks", 3))
              if outer else "minecraft:polished_blackstone")
        if mode == 2:
            p.set(x, GROUND - 1, z, "minecraft:deepslate_tiles")
    p.set(IX + 7, GROUND, IZ + 7, SURFACE_ORE)              # the top landing's mark
    # the threshold
    for x in range(DOOR_X - 1, DOOR_X + 2):
        p.set(x, GROUND, SZ0, "minecraft:polished_blackstone")
    # a railing along the stair mouth's north edge
    for u in range(0, 3):
        p.wall(IX + u, GROUND + 1, IZ + 4, "polished_blackstone")


def _wall_block(p, y):
    if y <= GROUND + 2:
        return _pick(p, ("minecraft:polished_blackstone_bricks", 4), ("minecraft:cracked_polished_blackstone_bricks", 4),
                     ("minecraft:blackstone", 2), ("minecraft:cobbled_deepslate", 1), (SURFACE_ORE, 0.25))
    return _pick(p, ("minecraft:polished_blackstone_bricks", 7), ("minecraft:cracked_polished_blackstone_bricks", 2),
                 ("minecraft:blackstone", 1), ("minecraft:deepslate_tiles", 1), (SURFACE_ORE, 0.25))


def _mausoleum_walls(p):
    """Walls y 38..43 with a plinth course, corner piers, pilasters, slit windows and the
    pointed north door."""
    g = GROUND
    for y in range(g + 1, EAVE + 1):
        for x in range(SX0, SX1 + 1):
            for z in range(SZ0, SZ1 + 1):
                if x in (SX0, SX1) or z in (SZ0, SZ1):
                    p.set(x, y, z, _wall_block(p, y) if y < EAVE else "minecraft:polished_blackstone")
    # corner columns and L-shaped piers outside them
    for cx, dx in ((SX0, -1), (SX1, 1)):
        for cz, dz in ((SZ0, -1), (SZ1, 1)):
            for y in range(g + 1, EAVE + 1):
                p.set(cx, y, cz, "minecraft:chiseled_polished_blackstone" if y in (g + 1, EAVE)
                      else "minecraft:polished_blackstone")
            for x, z in ((cx + dx, cz), (cx, cz + dz), (cx + dx, cz + dz)):
                for y in range(g, EAVE - 1):
                    p.set(x, y, z, "minecraft:polished_blackstone_bricks" if y > g else "minecraft:cobbled_deepslate")
                p.set(x, EAVE - 1, z, "minecraft:chiseled_polished_blackstone")
    # pilasters at mid-wall on the east, west and south sides, with a glowing ore inset
    for x, z in ((SX0 - 1, CZ), (SX1 + 1, CZ), (CX, SZ1 + 1)):
        for y in range(g, EAVE - 1):
            p.set(x, y, z, "minecraft:polished_blackstone")
        p.set(x, g + 3, z, SURFACE_ORE)
        p.set(x, EAVE - 1, z, "minecraft:chiseled_polished_blackstone")
    # plinth course: stairs against the wall foot all round, except at piers, pilasters, door
    sides = (("north", [(x, SZ0 - 1) for x in range(SX0 + 1, SX1)], "south"),
             ("south", [(x, SZ1 + 1) for x in range(SX0 + 1, SX1)], "north"),
             ("west", [(SX0 - 1, z) for z in range(SZ0 + 1, SZ1)], "east"),
             ("east", [(SX1 + 1, z) for z in range(SZ0 + 1, SZ1)], "west"))
    for _, cells, facing in sides:
        for x, z in cells:
            if p.is_set(x, g + 1, z) and p.get(x, g + 1, z) != AIR:
                continue
            if facing == "south" and abs(x - DOOR_X) <= 1:
                continue
            p.stairs(x, g + 1, z, "polished_blackstone_bricks", facing)
            p.set(x, g, z, "minecraft:cobbled_deepslate")
    # slit windows with iron bars
    for x, z in ((SX0, IZ + 2), (SX0, IZ + 6), (SX1, IZ + 2), (SX1, IZ + 6), (IX + 2, SZ1), (IX + 6, SZ1)):
        for y in range(g + 2, g + 5):
            p.bars(x, y, z)
        p.set(x, g + 1, z, "minecraft:polished_blackstone")
        p.set(x, g + 5, z, "minecraft:chiseled_polished_blackstone")
    # the north door: a pointed opening 3 wide, chiseled jambs, a glowing keystone
    z = SZ0
    for x in (DOOR_X - 2, DOOR_X + 2):
        for y in range(g + 1, g + 5):
            p.set(x, y, z, "minecraft:chiseled_polished_blackstone" if y == g + 4 else "minecraft:polished_blackstone")
    p.clear((DOOR_X - 1, g + 1, z, DOOR_X + 1, g + 3, z))
    for x in (DOOR_X - 1, DOOR_X + 1):
        p.set(x, g + 4, z, "minecraft:polished_blackstone_bricks")
    p.set(DOOR_X, g + 4, z, SURFACE_ORE)
    for x in range(DOOR_X - 1, DOOR_X + 2):
        p.set(x, g + 5, z, "minecraft:chiseled_polished_blackstone")
    # a hood over the door
    for x in range(DOOR_X - 2, DOOR_X + 3):
        p.stairs(x, g + 5, z - 1, "polished_blackstone_bricks", "south", half="top")
    p.stairs(DOOR_X - 2, g + 5, z - 1, "polished_blackstone_bricks", "south", half="top", shape="outer_left")
    p.stairs(DOOR_X + 2, g + 5, z - 1, "polished_blackstone_bricks", "south", half="top", shape="outer_right")


def _mausoleum_roof(p):
    """A hipped roof of blackstone and deepslate tiles, weathered, with a glowing finial."""
    rnd = p.rnd
    top = p.hip_roof(SX0, SX1, SZ0, SZ1, EAVE, "polished_blackstone_bricks", overhang=1, ridge_slab=False)
    for (x, y, z), (b, _) in list(p.cells.items()):
        if y < EAVE or "polished_blackstone_brick_stairs" not in b:
            continue
        roll = rnd.random()
        if roll < 0.25:
            p.set(x, y, z, b.replace("polished_blackstone_brick_stairs", "deepslate_tile_stairs"))
        elif roll < 0.35:
            p.set(x, y, z, b.replace("polished_blackstone_brick_stairs", "blackstone_stairs"))
    # an under-course inside the eave line so the roof reads two thick from below
    for x in range(SX0 + 1, SX1):
        for z in range(SZ0 + 1, SZ1):
            if x in (SX0 + 1, SX1 - 1) or z in (SZ0 + 1, SZ1 - 1):
                p.set(x, EAVE, z, "minecraft:polished_blackstone_bricks")
    # finial over the apex
    p.set(CX, top - 1, CZ, SURFACE_ORE)
    p.wall(CX, top, CZ, "polished_blackstone")
    p.lantern(CX, top + 1, CZ, soul=True)


def _altar(p):
    """On the core, facing the door: a block altar with a shadow block, a wither skull and
    candles."""
    y = GROUND + 1
    for u in range(3, 6):
        for v in range(3, 6):
            corner = u != 4 and v != 4
            p.set(IX + u, y, IZ + v, "minecraft:chiseled_polished_blackstone" if corner
                  else "minecraft:polished_blackstone_bricks")
    p.set(CX, y + 1, CZ, SHADOW)
    p.set(CX, y + 2, CZ, "minecraft:wither_skeleton_skull[powered=false,rotation=8]")
    for u, v in ((3, 3), (5, 3), (3, 5), (5, 5)):
        p.candle(IX + u, y + 1, IZ + v, "black" if u == v else "purple", candles=2 + (u + v) % 3)
    for (u, v), f in (((4, 3), "south"), ((3, 4), "east"), ((5, 4), "west"), ((4, 5), "north")):
        p.stairs(IX + u, y + 1, IZ + v, "polished_blackstone_bricks", f)


def _mausoleum_details(p):
    """Soul lanterns hanging over the altar and the stair mouth, lanterns in the corners,
    cobwebs high up, a skull and candles by the walls."""
    g = GROUND
    p.hanging_lantern(CX, EAVE, CZ, chain=4, soul=True)          # from the finial
    p.hanging_lantern(IX + 2, EAVE - 2, IZ + 8, chain=1, soul=True)  # from the inner cornice
    for u, v in ((0, 0), (8, 0)):
        p.lantern(IX + u, g + 1, IZ + v, soul=True)
    p.candle(IX + 8, g + 1, IZ + 8, "purple", candles=3)
    p.candle(IX + 0, g + 1, IZ + 3, "black", candles=2)
    p.skull(IX + 8, g + 1, IZ + 3, rotation=4)
    for x, y, z in ((IX, EAVE - 1, IZ), (IX + 8, EAVE - 1, IZ), (IX + 8, EAVE - 1, IZ + 8),
                    (IX, EAVE - 1, IZ + 8), (IX + 1, EAVE + 1, IZ + 1), (IX + 7, EAVE + 1, IZ + 6),
                    (DOOR_X - 1, g + 2, SZ0 - 0)):
        if p.get(x, y, z) == AIR:
            p.set(x, y, z, "minecraft:cobweb")


PLACE = {
    "name": "shadow_vault",
    "pieces": {"shadow_vault": build},
    "step": "surface_structures",
    # The ground layer is y = GROUND = 37, the 38th layer of the piece. The surface height
    # (WORLD_SURFACE_WG) is the first air above the top block, so -(37 + 1) puts layer 37 on
    # the top block, as start_height -1 does for a ground layer at y 0 (ruined_forge).
    "start_height": -GROUND,  # -37: Horizon puts the piece bottom at (top block y + start_height); see jigsaw.rs place_start
    "surface": True,
    "terrain": "none",
    "biomes": [
        "#minecraft:is_forest", "#minecraft:is_taiga", "#minecraft:is_savanna", "#minecraft:is_badlands", "#minecraft:is_hill", "#minecraft:is_mountain", "#minecraft:is_jungle", "minecraft:plains", "minecraft:sunflower_plains", "minecraft:meadow", "minecraft:desert", "minecraft:snowy_plains", "minecraft:cherry_grove",
    ],
    "spacing": 22,
    "separation": 8,
    "salt": 418200106,
}
