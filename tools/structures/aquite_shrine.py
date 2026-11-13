"""Aquite shrine (surface; beaches, rivers, swamps). docs/design/places.md section 3.

A water shrine on a stepped round prismarine podium: three two-high tiers with stair lips
and flights of steps on the south axis, a ring of eight columns (two fallen) joined by
arches, a tall canopy over the altar island in a lit basin, water channels running east and
west across the tiers, and a sunken stair on the north side down to a flooded reliquary
carved into the shrine's own foundation under the altar.

Heights: y=0..3 is the masonry foundation (the reliquary is cut into it), y=4 is ground
level (start_height -5 puts that layer in the surface), the tiers top out at y=6, 8 and 10.
"""
import math

from structkit import AIR, HORIZONTAL, NS, OPPOSITE, VECTOR, Piece, ccw, state

W, H = 33, 25
C = W // 2                                    # the centre column, x = z = 16
GROUND = 4                                    # the layer that replaces the world's surface
TIERS = ((13.4, 6), (10.9, 8), (8.4, 10))     # (radius, top y) from the bottom tier up
TOP = TIERS[-1][1]                            # tier 3 surface, the shrine floor
COLUMN_R = 6
BROKEN = {2, 5}                               # indices of the fallen columns
CHANNELS = ("east", "west")
AQUITE = f"{NS}:aquiteore"
WATER = "minecraft:water[level=0]"
LILY = "minecraft:lily_pad"


def _dist(x, z):
    return math.hypot(x - C, z - C)


def _inside(r):
    return lambda x, z: _dist(x, z) <= r


def _is_rim(inside, x, z):
    return inside(x, z) and any(not inside(x + VECTOR[d][0], z + VECTOR[d][2]) for d in HORIZONTAL)


def _edge_stair(p, x, y, z, inside, material):
    """A stair on the rim of a round tier, back toward the inside, with corner shapes where
    the rim turns: outer where two sides are open, inner where only a diagonal is open."""
    open_sides = [d for d in HORIZONTAL if not inside(x + VECTOR[d][0], z + VECTOR[d][2])]
    if len(open_sides) == 1:
        p.stairs(x, y, z, material, OPPOSITE[open_sides[0]])
        return
    if len(open_sides) == 2 and OPPOSITE[open_sides[0]] != open_sides[1]:
        fz = next(OPPOSITE[d] for d in open_sides if d in ("north", "south"))
        fx = next(OPPOSITE[d] for d in open_sides if d in ("east", "west"))
        p.stairs(x, y, z, material, fz,
                 shape="outer_left" if ccw(fz) == fx else "outer_right")
        return
    p.set(x, y, z, f"minecraft:{material}")


def _line4(a, b):
    """A 4-connected line of cells from a to b (both included): no diagonal gaps."""
    (x, z), (x1, z1) = a, b
    out = [(x, z)]
    while (x, z) != (x1, z1):
        if abs(x1 - x) >= abs(z1 - z):
            x += 1 if x1 > x else -1
        else:
            z += 1 if z1 > z else -1
        out.append((x, z))
    return out


def _noise(p, cell=5):
    """Seeded smooth noise in 0..1 over the piece (bilinear between random grid points), for
    ground patches that clump instead of speckling."""
    n = W // cell + 2
    grid = [[p.rnd.random() for _ in range(n)] for _ in range(n)]

    def at(x, z):
        gx, gz = x / cell, z / cell
        i, j = int(gx), int(gz)
        fx, fz = gx - i, gz - j
        top = grid[i][j] * (1 - fx) + grid[i + 1][j] * fx
        bot = grid[i][j + 1] * (1 - fx) + grid[i + 1][j + 1] * fx
        return top * (1 - fz) + bot * fz
    return at


def _columns():
    """The eight column positions, at 22.5 + 45k degrees so the axes stay open."""
    out = []
    for k in range(8):
        a = math.radians(22.5 + 45 * k)
        out.append((C + round(COLUMN_R * math.cos(a)), C + round(COLUMN_R * math.sin(a))))
    return out


def _outward(x, z):
    """The horizontal direction pointing most away from the centre."""
    return max(HORIZONTAL, key=lambda d: (x - C) * VECTOR[d][0] + (z - C) * VECTOR[d][2])


def _basin_ring(x, z):
    dx, dz = abs(x - C), abs(z - C)
    return max(dx, dz) == 2 and not (dx == 2 and dz == 2)


# ------------------------------------------------------------------ ground and foundation
def _ground(p):
    """Air over everything, then shore ground in clumps: sand, gravel bars, grassy tufts."""
    p.clear((0, GROUND + 1, 0, W - 1, H - 1, W - 1))
    noise = _noise(p)
    sand = p.mix(("minecraft:sand", 8), ("minecraft:gravel", 1), ("minecraft:clay", 1))
    gravel = p.mix(("minecraft:gravel", 6), ("minecraft:sand", 2), ("minecraft:coarse_dirt", 2))
    grass = p.mix(("minecraft:grass_block[snowy=false]", 8), ("minecraft:coarse_dirt", 1),
                  ("minecraft:mud", 1))
    for x in range(W):
        for z in range(W):
            if _dist(x, z) <= TIERS[0][0]:
                continue
            n = noise(x, z) + (_dist(x, z) - 14) * 0.05
            p.set(x, GROUND, z, grass() if n > 0.62 else gravel() if n < 0.3 else sand())
            r = p.rnd.random()
            under = p.get(x, GROUND, z)
            if under == "minecraft:grass_block[snowy=false]":
                if r < 0.25:
                    p.set(x, GROUND + 1, z, "minecraft:short_grass")
                elif r < 0.31:
                    p.set(x, GROUND + 1, z, "minecraft:fern")
                elif r < 0.35:
                    p.set(x, GROUND + 1, z, "minecraft:tall_grass[half=lower]")
                    p.set(x, GROUND + 2, z, "minecraft:tall_grass[half=upper]")
            elif under == "minecraft:sand" and r < 0.025:
                p.set(x, GROUND + 1, z, "minecraft:dead_bush")


def _foundation(p):
    """Solid masonry under the whole podium; the reliquary is carved out of it later."""
    base = p.mix(("minecraft:prismarine_bricks", 5), ("minecraft:prismarine", 3),
                 ("minecraft:dark_prismarine", 1), ("minecraft:stone", 1))
    for x in range(W):
        for z in range(W):
            if _dist(x, z) <= TIERS[0][0]:
                for y in range(0, GROUND + 1):
                    p.set(x, y, z, base())


# ------------------------------------------------------------------ the three tiers
def _tier_surface(p, tier, x, z):
    """The floor block of a tier: worn and sand-drifted low down, inlaid at the top."""
    d = _dist(x, z)
    angle = math.degrees(math.atan2(z - C, x - C)) % 45
    spoke = angle < 5 or angle > 40                   # on a 0/45/90... degree spoke
    if tier == 0:
        if spoke and 11.5 <= d <= 12.4:
            return AQUITE
        return p.mix(("minecraft:prismarine_bricks", 5), ("minecraft:prismarine", 3),
                     ("minecraft:sand", 1), ("minecraft:mossy_cobblestone", 1))()
    if tier == 1:
        if 9.0 <= d <= 9.8:
            return "minecraft:dark_prismarine"
        return p.mix(("minecraft:prismarine_bricks", 6), ("minecraft:prismarine", 3))()
    if abs(x - C) == 0 and z > C:
        return "minecraft:dark_prismarine"                # processional strip to the bridge
    if 5.5 <= d < 6.6:
        return "minecraft:dark_prismarine"                # the column ring band
    if spoke and 3.6 <= d <= 4.4:
        return AQUITE                                     # glowing inlays round the basin
    if d < 3.6:
        return "minecraft:prismarine_bricks"
    return p.mix(("minecraft:prismarine_bricks", 8), ("minecraft:prismarine", 2))()


def _tiers(p):
    """Each tier is a two-high drum: a worn lower course, a dark prismarine trim course and
    a stair lip at the rim, a patterned floor inside."""
    lower = p.mix(("minecraft:prismarine_bricks", 4), ("minecraft:prismarine", 3),
                  ("minecraft:mossy_cobblestone", 1))
    for i, (r, top) in enumerate(TIERS):
        inside = _inside(r)
        upper = _inside(TIERS[i + 1][0]) if i + 1 < len(TIERS) else (lambda x, z: False)
        lip = "dark_prismarine" if i == len(TIERS) - 1 else "prismarine_bricks"
        for x in range(W):
            for z in range(W):
                if not inside(x, z) or upper(x, z):
                    continue
                rim = _is_rim(inside, x, z)
                for y in range(GROUND + 1, top):
                    p.set(x, y, z, "minecraft:dark_prismarine" if rim and y == top - 1 else lower())
                if rim:
                    _edge_stair(p, x, top, z, inside, lip)
                else:
                    p.set(x, top, z, _tier_surface(p, i, x, z))
    # moss creeping over the bottom step
    p.scatter((0, TIERS[0][1] + 1, 0, W - 1, TIERS[0][1] + 1, W - 1), "minecraft:moss_carpet", 0.04,
              only_on={"minecraft:prismarine_bricks", "minecraft:mossy_cobblestone"})


def _flights(p):
    """Three-wide flights of steps up each riser on the south axis, the approach."""
    below = GROUND
    for r, top in TIERS:
        rim_z = max(z for z in range(C, W) if _dist(C, z) <= r)
        for x in range(C - 1, C + 2):
            p.stairs(x, below + 1, rim_z, "prismarine_bricks", "north")
            p.set(x, below + 2, rim_z, AIR)
            p.stairs(x, below + 2, rim_z - 1, "prismarine_bricks", "north")
        below = top


# ------------------------------------------------------------------ water
def _channels(p):
    """Sealed runnels from the basin out across each tier floor, edged in dark prismarine
    and lit from below on the top tier. Each stretch stops short of its tier's rim, so the
    water never meets air at its own level."""
    for direction in CHANNELS:
        dx = VECTOR[direction][0]
        for i, (r, top) in enumerate(TIERS):
            inside = _inside(r)
            upper = _inside(TIERS[i + 1][0]) if i + 1 < len(TIERS) else (lambda x, z: _dist(x, z) <= 2)
            cells = [(C + dx * k, C) for k in range(3, 16)
                     if inside(C + dx * k, C) and not upper(C + dx * k, C)
                     and not _is_rim(inside, C + dx * k, C)]
            for n, (x, z) in enumerate(cells):
                p.set(x, top, z, WATER)
                for s in (-1, 1):
                    p.set(x, top, z + s, "minecraft:dark_prismarine")
                if i == len(TIERS) - 1 and n % 2 == 1:
                    p.set(x, top - 1, z, "minecraft:sea_lantern")
            if i == len(TIERS) - 1:
                p.set(cells[2][0], top + 1, C, LILY)


def _basin(p):
    """A two-deep water ring round the altar island, sea lanterns on its bed, and a slab
    bridge on the south side where the approach crosses."""
    for x in range(C - 2, C + 3):
        for z in range(C - 2, C + 3):
            if _basin_ring(x, z):
                p.set(x, TOP, z, WATER)
                p.set(x, TOP - 1, z, WATER)
                p.set(x, TOP - 2, z, "minecraft:sea_lantern")
            elif abs(x - C) <= 1 and abs(z - C) <= 1:
                corner = abs(x - C) == 1 and abs(z - C) == 1
                p.set(x, TOP, z, AQUITE if corner else "minecraft:dark_prismarine")
    p.slab(C, TOP, C + 2, "dark_prismarine", "top")
    for x, z, n in ((C - 2, C - 1, 3), (C + 2, C + 1, 2), (C + 1, C - 2, 4)):   # glowing pickles on the bed
        p.set(x, TOP - 1, z, f"minecraft:sea_pickle[pickles={n},waterlogged=true]")


# ------------------------------------------------------------------ columns and arches
def _flare(p, x, y, z, half, skip):
    """Stairs round a column cell (bases bottom, capitals top), backs to the column."""
    for d in HORIZONTAL:
        cx, cz = x + VECTOR[d][0], z + VECTOR[d][2]
        if (cx, cz) not in skip and p.get(cx, y, cz) in (None, AIR):
            p.stairs(cx, y, cz, "dark_prismarine", OPPOSITE[d], half=half)


def _column(p, k, x, z, skip):
    """A column on the ring: base, shaft with an aquite band, sea lantern capital with a
    flare of upside-down stairs. Fallen ones stop short with a jagged stair top."""
    p.set(x, TOP + 1, z, "minecraft:dark_prismarine")
    _flare(p, x, TOP + 1, z, "bottom", skip)
    if k in BROKEN:
        top = TOP + 2 + k % 2
        for y in range(TOP + 2, top + 1):
            p.set(x, y, z, "minecraft:prismarine_bricks")
        p.stairs(x, top + 1, z, "prismarine_bricks", HORIZONTAL[k % 4])
        return
    for y in range(TOP + 2, TOP + 6):
        p.set(x, y, z, AQUITE if y == TOP + 3 else
              "minecraft:prismarine" if y == TOP + 5 else "minecraft:prismarine_bricks")
    p.set(x, TOP + 6, z, "minecraft:sea_lantern")
    _flare(p, x, TOP + 6, z, "top", set())
    p.set(x, TOP + 7, z, "minecraft:dark_prismarine")


def _arches(p, cols):
    """A brick beam between neighbouring standing columns (the capital flares spring it),
    capped with slabs. Beside a fallen column only a one-block stub is left."""
    beam_y = TOP + 7
    beam = p.mix(("minecraft:prismarine_bricks", 5), ("minecraft:dark_prismarine", 1))
    for k in range(8):
        cells = _line4(cols[k], cols[(k + 1) % 8])[1:-1]
        if k in BROKEN:
            cells = cells[-1:]
        elif (k + 1) % 8 in BROKEN:
            cells = cells[:1]
        for x, z in cells:
            p.set(x, beam_y, z, beam())
            p.slab(x, beam_y + 1, z, "prismarine_brick")
    for k, (x, z) in enumerate(cols):
        if k not in BROKEN:
            p.slab(x, beam_y + 1, z, "dark_prismarine")


def _vines(p, cols):
    """Vines hanging off the outer face of three standing columns."""
    for k in (0, 3, 6):
        x, z = cols[k]
        out = _outward(x, z)
        vx, vz = x + VECTOR[out][0], z + VECTOR[out][2]
        for y in range(TOP + 2, TOP + 6):
            if p.get(vx, y, vz) in (None, AIR):
                p.set(vx, y, vz, state("minecraft:vine", up=False,
                                       **{d: d == OPPOSITE[out] for d in HORIZONTAL}))


def _rubble(p, cols):
    """The fallen columns' drums: slabs and stairs strewn on the top floor, and a whole drum
    rolled off the podium onto the shore."""
    for k in BROKEN:
        x, z = cols[k]
        out = _outward(x, z)
        side = HORIZONTAL[(HORIZONTAL.index(out) + 1) % 4]
        for dx, dz, kind in ((VECTOR[side][0] * 2, VECTOR[side][2] * 2, "slab"),
                             (-VECTOR[out][0] * 2, -VECTOR[out][2] * 2, "stairs"),
                             (-VECTOR[side][0] * 2, -VECTOR[side][2] * 2, "slab")):
            cx, cz = x + dx, z + dz
            if p.get(cx, TOP + 1, cz) in (None, AIR) and 3 < _dist(cx, cz) < TIERS[-1][0] - 1:
                if kind == "slab":
                    p.slab(cx, TOP + 1, cz, "prismarine_brick")
                else:
                    p.stairs(cx, TOP + 1, cz, "prismarine_bricks", side)
    y = GROUND + 1
    for x in range(2, 5):
        p.set(x, y, 5, "minecraft:prismarine_bricks")
    p.stairs(5, y, 5, "prismarine_bricks", "west")
    p.set(3, y + 1, 5, "minecraft:moss_carpet")


# ------------------------------------------------------------------ canopy and altar
def _canopy(p):
    """Four tall posts on the basin corners carrying a lantern-studded ceiling and a hipped
    dark prismarine roof with an aquite finial above the column ring."""
    ceil = TOP + 7
    for x in (C - 2, C + 2):
        for z in (C - 2, C + 2):
            p.set(x, TOP, z, "minecraft:dark_prismarine")
            p.set(x, TOP + 1, z, "minecraft:dark_prismarine")
            for y in range(TOP + 2, ceil - 1):
                p.wall(x, y, z, "prismarine")
            p.set(x, ceil - 1, z, "minecraft:prismarine_bricks")
            for d in HORIZONTAL:                          # small capital corbels
                cx, cz = x + VECTOR[d][0], z + VECTOR[d][2]
                if abs(cx - C) <= 2 and abs(cz - C) <= 2:
                    p.stairs(cx, ceil - 1, cz, "prismarine_bricks", OPPOSITE[d], half="top")
    for x in range(C - 2, C + 3):
        for z in range(C - 2, C + 3):
            lamp = abs(x - C) == 1 and abs(z - C) == 1
            p.set(x, ceil, z, "minecraft:sea_lantern" if lamp else "minecraft:dark_prismarine")
    p.hip_roof(C - 2, C + 2, C - 2, C + 2, ceil, "dark_prismarine", overhang=1)
    p.fill(C - 1, ceil + 1, C - 1, C + 1, ceil + 1, C + 1, "minecraft:prismarine_bricks")
    p.set(C, ceil + 2, C, "minecraft:dark_prismarine")
    p.set(C, ceil + 3, C, AQUITE)                         # finial
    p.wall(C, ceil + 4, C, "prismarine")
    p.set(C, ceil + 5, C, "minecraft:end_rod[facing=up]")
    p.hanging_lantern(C, ceil - 3, C, chain=2)            # over the altar


def _altar(p):
    """The altar on the island: the chest between stair arms, a back stone carrying a
    conduit, candles at the corners."""
    y = TOP + 1
    p.chest(C, y, C, "aquite_shrine", "south")
    p.stairs(C - 1, y, C, "dark_prismarine", "east")
    p.stairs(C + 1, y, C, "dark_prismarine", "west")
    p.set(C, y, C - 1, "minecraft:dark_prismarine")
    p.set(C, y + 1, C - 1, "minecraft:conduit[waterlogged=false]")
    p.candle(C - 1, y, C - 1, "cyan", 3)
    p.candle(C + 1, y, C - 1, "cyan", 2)
    p.candle(C - 1, y, C + 1, "light_blue", 1)
    p.candle(C + 1, y, C + 1, "light_blue", 2)


# ------------------------------------------------------------------ sunken stair and reliquary
STAIR_TOP_Z = C - 7                                   # first step, on the north of tier 3


def _sunken_stair(p):
    """Steps down southward from the north side of the top tier, under the basin, into the
    reliquary. The open mouth is railed with prismarine walls."""
    for i, y in enumerate(range(TOP - 1, 1, -1)):         # y 9..2 at z C-7..C
        z = STAIR_TOP_Z + i
        p.stairs(C, y, z, "prismarine_bricks", "north")
        for yy in range(y + 1, y + 3):
            p.set(C, yy, z, AIR)
    for z in range(STAIR_TOP_Z, STAIR_TOP_Z + 3):
        p.set(C, TOP, z, AIR)
        for x in (C - 1, C + 1):
            if p.get(x, TOP + 1, z) in (None, AIR):
                p.wall(x, TOP + 1, z, "prismarine")
    for x in (C - 1, C, C + 1):
        p.wall(x, TOP + 1, STAIR_TOP_Z + 3, "prismarine")
    p.wall_torch(C, TOP - 1, STAIR_TOP_Z + 3, "north", soul=True)   # under the lip, lights the steps


def _reliquary(p):
    """A low flooded room under the altar: sea lanterns under the water, kelp and pickles,
    glowing ore set in the walls, the reliquary chest on a candle-lit plinth at the far end."""
    x0, x1, z0, z1 = C - 3, C + 3, C + 1, C + 6
    wall = p.mix(("minecraft:prismarine_bricks", 3), ("minecraft:prismarine", 2))
    for x in range(x0 - 1, x1 + 2):
        for z in range(z0 - 1, z1 + 2):
            edge = x in (x0 - 1, x1 + 1) or z in (z0 - 1, z1 + 1)
            corner = x in (x0 - 1, x1 + 1) and z in (z0 - 1, z1 + 1)
            for y in range(1, 5):
                if edge:
                    p.set(x, y, z, "minecraft:dark_prismarine" if corner else
                          AQUITE if y == 3 and (x + z) % 3 == 0 else wall())
            p.set(x, 0, z, "minecraft:sea_lantern" if (x - x0) % 2 == 0 and (z - z0) % 2 == 0
                  else "minecraft:dark_prismarine")
            p.set(x, 5, z, "minecraft:dark_prismarine")
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            p.set(x, 1, z, WATER)
            for y in (2, 3, 4):
                p.set(x, y, z, AIR)
    p.stairs(C, 1, z0, "prismarine_bricks", "north", waterlogged=True)   # last step, under water
    for x in (C - 1, C, C + 1):                           # plinth at the far (south) end
        p.set(x, 1, z1, "minecraft:dark_prismarine")
    p.chest(C, 2, z1, "aquite_shrine", "north")
    p.candle(C - 1, 2, z1, "cyan", 4)
    p.candle(C + 1, 2, z1, "cyan", 3)
    for x in (C - 2, C + 2):                              # two piers carrying the ceiling
        for y in range(1, 5):
            p.set(x, y, C + 3, "minecraft:dark_prismarine" if y in (1, 4) else "minecraft:prismarine_bricks")
        p.set(x, 3, C + 3, AQUITE)
    p.set(C, 5, C + 3, "minecraft:sea_lantern")
    for x, z, age in ((x0, z0 + 1, 3), (x1, z0 + 2, 9), (x0, z1 - 1, 5)):
        p.set(x, 1, z, f"minecraft:kelp[age={age}]")
    for x, z, n in ((x1, z0, 2), (x1, z1 - 1, 3), (x0 + 1, z0 + 3, 1)):
        p.set(x, 1, z, f"minecraft:sea_pickle[pickles={n},waterlogged=true]")
    for x, z in ((x0, z0), (x1, z1 - 1), (x0 + 3, z0 + 2)):   # lichen on the ceiling
        p.set(x, 4, z, state("minecraft:glow_lichen", up=True, down=False, waterlogged=False,
                             **{d: False for d in HORIZONTAL}))


# ------------------------------------------------------------------ surroundings
def _approach(p):
    """A gravel and slab path from the south edge to the first flight, flanked by lamp
    posts, with offering pots set on the bottom tier."""
    rim_z = max(z for z in range(C, W) if _dist(C, z) <= TIERS[0][0])
    path = p.mix(("minecraft:gravel", 3), ("minecraft:dirt_path", 1), ("minecraft:prismarine_bricks", 2))
    for z in range(rim_z + 1, W):
        for x in range(C - 1, C + 2):
            p.set(x, GROUND, z, path())
            p.set(x, GROUND + 1, z, AIR)
            p.set(x, GROUND + 2, z, AIR)
    for x in (C - 3, C + 3):
        z = rim_z + 2
        p.set(x, GROUND, z, "minecraft:dark_prismarine")
        p.set(x, GROUND + 1, z, "minecraft:prismarine_bricks")
        p.wall(x, GROUND + 2, z, "prismarine")
        p.set(x, GROUND + 3, z, "minecraft:sea_lantern")
        p.slab(x, GROUND + 4, z, "dark_prismarine")
    pot = "minecraft:decorated_pot[cracked={},facing={},waterlogged=false]"
    for x, z, cracked in ((C - 3, C + 11, "false"), (C + 3, C + 11, "true"),
                          (C - 11, C + 3, "false"), (C + 11, C - 4, "true")):
        p.set(x, TIERS[0][1] + 1, z, pot.format(cracked, _outward(x, z)))


def _pool(p):
    """A small reed-fringed pool in the north-east corner, sealed in clay."""
    cells = [(x, z) for x in range(W - 5, W - 2) for z in range(2, 5) if (x, z) != (W - 3, 2)]
    for x, z in cells:
        p.set(x, GROUND - 1, z, "minecraft:clay")
        p.set(x, GROUND, z, WATER)
        for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if (x + dx, z + dz) not in cells and p.get(x + dx, GROUND, z + dz) in (None, "minecraft:grass_block[snowy=false]"):
                p.set(x + dx, GROUND, z + dz, "minecraft:sand")
    for x, z in ((W - 5, 3), (W - 3, 4)):
        p.set(x, GROUND + 1, z, LILY)
    for x, z in ((W - 6, 3), (W - 6, 4), (W - 3, 1)):
        p.set(x, GROUND, z, "minecraft:sand")
        for y in range(GROUND + 1, GROUND + 3):
            p.set(x, y, z, "minecraft:sugar_cane[age=0]")


def build():
    p = Piece("aquite_shrine", W, H, W, "shrine")
    _ground(p)
    _foundation(p)
    _tiers(p)
    _flights(p)
    _basin(p)
    _channels(p)
    cols = _columns()
    stair_cells = {(C + dx, z) for dx in (-1, 0, 1) for z in range(STAIR_TOP_Z, STAIR_TOP_Z + 4)}
    rim = {(x, z) for x in range(W) for z in range(W) if _is_rim(_inside(TIERS[-1][0]), x, z)}
    for k, (x, z) in enumerate(cols):
        _column(p, k, x, z, rim | stair_cells)
    _arches(p, cols)
    _vines(p, cols)
    _rubble(p, cols)
    _canopy(p)
    _altar(p)
    _reliquary(p)
    _sunken_stair(p)                                      # after the room: it cuts the doorway
    _approach(p)
    _pool(p)
    return p


PLACE = {
    "name": "aquite_shrine",
    "pieces": {"aquite_shrine": build},
    "step": "surface_structures",
    "start_height": -5,
    "surface": True,
    "terrain": "beard_thin",
    "biomes": [
        "#minecraft:is_beach",
        "#minecraft:is_river",
        "minecraft:swamp",
        "minecraft:mangrove_swamp",
    ],
    "spacing": 30,
    "separation": 10,
    "salt": 418200103,
}
