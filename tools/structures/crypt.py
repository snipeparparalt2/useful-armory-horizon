"""Crypt dungeon: a mausoleum on the surface, a stair 26 blocks down to the dungeon level, and
below it a crypt built from jigsaw pieces, different every time.
Brief: docs/design/places.md section 12.

Pieces (outer size w x h x d; every one but the start's surface part is a solid closed shell
that carves its own air):
  crypt/start        11 x 38 x 19  vestibule (3 doors) at the bottom, a switchback stair in a
                                   closed shaft above it, the mausoleum and its yard on top
  crypt/corridor      7 x  6 x 11  straight; arched, ribbed, burial shelves and niches
  crypt/corner        9 x  7 x  9  domed junction, doors S and E, two wall shrines
  crypt/t_junction    9 x  7 x  9  domed junction, doors W, E and S, one wall shrine
  crypt/crossing      9 x  7 x  9  domed junction, four doors
  crypt/tomb_hall    15 x  8 x 15  stone coffins, burial niches; skeleton spawner
  crypt/ossuary      13 x  7 x 13  bone-lined walls of skulls, bone pillar; skeleton spawner
  crypt/chapel       13 x  9 x 15  pews, altar on a dais, chest behind the altar
  crypt/flooded      13 x  9 x 13  pit flooded two deep, causeway, sunken chest
  crypt/collapsed    13 x  9 x 13  vault fallen in, rubble heap, buried chest; zombie spawner
  crypt/guard_room   15 x  7 x 15  racks, bunks, table, cell; vault guardian spawner
  crypt/treasure     13 x  8 x 13  one door; dais, sarcophagus, three treasure chests,
                                   vault guardian spawner. Exactly one per crypt.
  crypt/cap           3 x  4 x  1  bricked-up doorway: the dead end (pools' fallback)

Doorways are all the same: 3 wide, 3 high, the connector in the middle of the bottom row
on the outer face of the shell, front pointing out, one block above the walking floor
(y = 1 everywhere except the flooded chamber, whose floor is raised to y = 2 over its pit
and whose connectors are at y = 3). Walls are two thick (the cap is one), so a joined
doorway is a 3 x 3 passage four blocks long with a polished frame, threshold and lintel.

Pools (what each connector draws its child from):
  start doors           -> crypt/corridors  (corridor shapes only)
  corridor/junction ends -> crypt/branches  (rooms, more corridors; treasure guaranteed once)
  room doors            -> crypt/corridors
  treasure door, cap    -> minecraft:empty  (they only ever attach as children)
  crypt/corridors and crypt/branches fall back to crypt/caps, so at the deepest level
  (and wherever nothing else fits) an open doorway is closed by a cap.

Jigsaw connector conventions (checked against Horizon fdc87ae,
crates/horizon-world/src/worldgen/structure/jigsaw.rs and template.rs):

* A connector is a `minecraft:jigsaw` block with block-entity data; place it with
  `Piece.jigsaw(x, y, z, orientation, name, target, pool, final_state, joint)`.
* orientation "<front>_<top>" (template_jigsaws): front is the direction the connector
  points, OUT of the piece toward where the neighbour goes. Horizontal connectors are
  north_up / east_up / south_up / west_up; vertical ones up_<dir> / down_<dir>.
  Put horizontal connectors in the piece's outer wall layer, front pointing outward.
* Attaching (can_attach): a parent connector P takes a child connector C when
  C.front == opposite(P.front), C.name == P.target, and (P is rollable or the tops match).
  For horizontal connectors the top is always "up", so joint does not matter there; for
  vertical ones joint "aligned" also needs the tops to match after rotation ("rollable" lets
  the child spin). A connector with no `joint` in its NBT counts as aligned when horizontal
  and rollable when vertical (JigsawInfo in template.rs); Piece.jigsaw always writes one.
* P.pool names the pool the child is drawn from (Pools::get, `<ns>:<path>` under
  worldgen/template_pool). The child's own `pool` field is not used for this attachment.
  All four rotations of each candidate are tried (JigsawBuilder::children).
* Placement (children): the child is moved so that C sits in the cell directly in front of
  P (P.pos + P.front). The two connector blocks end up face to face, one in each piece.
  For rigid pieces the child's height is set so that C is level with P
  (delta_y = P.local_y - C.local_y), so floors line up whenever every connector sits the
  same height above its own piece's walking floor (one block here).
* The child's bounding box must not overlap any placed piece (the start's whole box counts,
  so nothing can be placed in the shaft or the mausoleum) and must stay inside the reach box:
  max_distance_from_center (80 here) round the centre of the start's box horizontally and
  round the start's bottom + 1 vertically (lay_out_children); otherwise the next candidate is
  tried.
* Depth: the start is depth 0 and `size` (5 here) is the deepest level. At the last level
  only the pool's `fallback` is drawn from, so every pool a connector can reach has the
  dead-end pool `crypt/caps` as fallback; it seals openings that nothing else filled.
* `lithostitched:guaranteed` (count, min_depth) in a pool is tried before the pool's other
  entries until `count` have been placed in the start; `lithostitched:limited` (limit,
  min_depth) caps how many of an element one start holds. min_depth is the PARENT piece's
  least depth. Both count by the element's JSON, wherever it is listed. Neither forces a
  piece in when there is no room.
* After placement every jigsaw block is replaced by its `final_state` (default air): use
  air for doorways, the wall block where the connector sits in a wall that stays closed.
* selection_priority: within one piece, higher goes first. placement_priority: children
  from connectors with higher values are expanded first.

Every doorway connector has name = target = "useful_armory:crypt/door", so any door fits
any door; the pools decide what grows where.
"""
from structkit import AIR, HORIZONTAL, NS, OPPOSITE, VECTOR, Piece, ccw, cw, is_full_solid, state

DOOR = f"{NS}:crypt/door"
CORRIDORS = f"{NS}:crypt/corridors"
BRANCHES = f"{NS}:crypt/branches"
EMPTY = "minecraft:empty"
GUARDIAN = f"{NS}:vault_guardian"
SHADOW = f"{NS}:shadowblock"
SHADOW_ORE = f"{NS}:deepslate_shadow_ore"
ROT = {"south": 0, "west": 4, "north": 8, "east": 12}     # floor skull rotation facing a way


# ------------------------------------------------------------------ palettes
def _pal(p, kind):
    """Block palette of one family member; wall/floor are seeded mixers."""
    m = p.mix
    if kind == "deepslate":
        return dict(
            wall=m(("minecraft:deepslate_bricks", 8), ("minecraft:cracked_deepslate_bricks", 3),
                   ("minecraft:deepslate_tiles", 2), ("minecraft:cobbled_deepslate", 1)),
            floor=m(("minecraft:deepslate_tiles", 6), ("minecraft:cracked_deepslate_tiles", 3),
                    ("minecraft:cobbled_deepslate", 1)),
            trim="minecraft:polished_deepslate", accent="minecraft:chiseled_deepslate",
            stair="deepslate_tiles", trim_stair="polished_deepslate", wall_post="polished_deepslate")
    if kind == "stone":
        return dict(
            wall=m(("minecraft:stone_bricks", 7), ("minecraft:cracked_stone_bricks", 3),
                   ("minecraft:mossy_stone_bricks", 2), ("minecraft:andesite", 1)),
            floor=m(("minecraft:stone_bricks", 5), ("minecraft:cracked_stone_bricks", 2),
                    ("minecraft:andesite", 1)),
            trim="minecraft:polished_andesite", accent="minecraft:chiseled_stone_bricks",
            stair="stone_bricks", trim_stair="polished_andesite", wall_post="stone_bricks")
    if kind == "tuff":
        return dict(
            wall=m(("minecraft:tuff_bricks", 7), ("minecraft:tuff", 3), ("minecraft:polished_tuff", 1)),
            floor=m(("minecraft:polished_tuff", 4), ("minecraft:tuff_bricks", 2), ("minecraft:tuff", 1)),
            trim="minecraft:polished_tuff", accent="minecraft:chiseled_tuff_bricks",
            stair="tuff_bricks", trim_stair="polished_tuff", wall_post="tuff_bricks")
    if kind == "mossy":
        return dict(
            wall=m(("minecraft:mossy_stone_bricks", 5), ("minecraft:stone_bricks", 3),
                   ("minecraft:cracked_stone_bricks", 2), ("minecraft:mossy_cobblestone", 2)),
            floor=m(("minecraft:mossy_cobblestone", 3), ("minecraft:mossy_stone_bricks", 3),
                    ("minecraft:cobblestone", 1)),
            trim="minecraft:stone_bricks", accent="minecraft:chiseled_stone_bricks",
            stair="mossy_stone_bricks", trim_stair="stone_bricks", wall_post="mossy_stone_bricks")
    if kind == "ruin":
        return dict(
            wall=m(("minecraft:cracked_deepslate_bricks", 4), ("minecraft:deepslate_bricks", 3),
                   ("minecraft:cobbled_deepslate", 3), ("minecraft:tuff", 2)),
            floor=m(("minecraft:cracked_deepslate_tiles", 3), ("minecraft:cobbled_deepslate", 3),
                    ("minecraft:tuff", 1), ("minecraft:gravel", 1)),
            trim="minecraft:polished_deepslate", accent="minecraft:chiseled_deepslate",
            stair="cobbled_deepslate", trim_stair="polished_deepslate", wall_post="cobbled_deepslate")
    raise KeyError(kind)


def _rubble(p):
    return p.mix(("minecraft:cobbled_deepslate", 4), ("minecraft:tuff", 3),
                 ("minecraft:cracked_deepslate_bricks", 2), ("minecraft:cobblestone", 1))


# ------------------------------------------------------------------ shared helpers
def _corner(facing, side, kind):
    """Stair shape for a corner cell: kind 'inner' or 'outer', `side` the second direction."""
    return f"{kind}_left" if ccw(facing) == side else f"{kind}_right"


def _step(x, z, d, n=1):
    dx, _, dz = VECTOR[d]
    return x + dx * n, z + dz * n


def _vault(p, cells, y, mat, open_=()):
    """Corbel course at height y over a set of (x, z) cells: each cell with walls beside it
    gets an upside-down stair backed onto them (inner corner shapes in corners); cells with
    no wall beside them are left as they are (air: the crown). `open_` cells count as open."""
    cells, open_ = set(cells), set(open_)
    for x, z in sorted(cells):
        walls = [d for d in HORIZONTAL if _step(x, z, d) not in cells and _step(x, z, d) not in open_]
        if not walls:
            continue
        if len(walls) == 1:
            p.stairs(x, y, z, mat, walls[0], half="top")
        elif len(walls) == 2 and walls[0] != OPPOSITE[walls[1]]:
            fz = next(d for d in walls if d in ("north", "south"))
            fx = next(d for d in walls if d in ("east", "west"))
            p.stairs(x, y, z, mat, fz, half="top", shape=_corner(fz, fx, "inner"))
        else:
            p.slab(x, y, z, mat, type="top")


def _rect(x0, z0, x1, z1):
    return [(x, z) for x in range(x0, x1 + 1) for z in range(z0, z1 + 1)]


def _door(p, x, z, facing, pool, pal, y=1, depth=2, arch=False):
    """A standard 3 x 3 doorway whose connector sits at (x, y, z) on the outer face, front
    `facing`. The opening runs `depth` cells inward with a polished threshold, jambs and
    lintel (keystone on the face). arch=True adds corbels on the innermost cell's top row
    on the room side only (the joint face stays a full 3 x 3)."""
    lat = cw(facing)
    for k in range(depth):
        cx, cz = _step(x, z, facing, -k)
        for l in (-1, 0, 1):
            ax, az = _step(cx, cz, lat, l)
            for yy in range(y, y + 3):
                p.set(ax, yy, az, AIR)
            p.set(ax, y - 1, az, pal["trim"])
            p.set(ax, y + 3, az, pal["accent"] if (l == 0 and k == 0) else pal["trim"])
        for l in (-2, 2):
            ax, az = _step(cx, cz, lat, l)
            for yy in range(y, y + 3):
                p.set(ax, yy, az, pal["trim"])
    if arch and depth > 1:
        cx, cz = _step(x, z, facing, -(depth - 1))
        for l, d in ((-1, ccw(facing)), (1, cw(facing))):
            ax, az = _step(cx, cz, lat, l)
            p.stairs(ax, y + 2, az, pal["trim_stair"], d, half="top")
    p.jigsaw(x, y, z, facing, DOOR, DOOR, pool)


def _niche(p, x, y, z, into, what, colour=None):
    """A one-cell niche in a wall cell (x, y, z) opening toward `into`, with a polished sill
    under it and a slab lintel over it. what: 'skull', 'candles', 'bones', 'empty'."""
    p.set(x, y, z, AIR)
    if what == "skull":
        p.skull(x, y, z, rotation=(ROT[into] + p.rnd.choice((-1, 0, 0, 1))) % 16)
    elif what == "candles":
        p.candle(x, y, z, colour, candles=p.rnd.randint(1, 4))
    elif what == "bones":
        p.set(x, y, z, f"minecraft:bone_block[axis={'x' if into in ('north', 'south') else 'z'}]")


def _cobwebs(p, box, chance):
    """Cobwebs in air cells of box that are under a solid block or tucked into a corner."""
    x0, y0, z0, x1, y1, z1 = box
    for x, y, z in Piece.box_cells(box):
        if p.get(x, y, z) != AIR:
            continue
        above = p.get(x, y + 1, z)
        if above in (None, AIR) or "chain" in above or "lantern" in above:
            continue
        if p.rnd.random() < chance:
            p.set(x, y, z, "minecraft:cobweb")


def _lichen(p, x, y, z, side):
    """Glow lichen on the face of the block at `side` of the cell (only into air)."""
    if p.get(x, y, z) == AIR:
        p.set(x, y, z, state("minecraft:glow_lichen", down=False, up=False, waterlogged=False,
                             **{d: d == side for d in HORIZONTAL}))


def _room_shell(p, pal, x0, z0, x1, z1, top, floor_y=0, box=None):
    """Solid box (the whole piece, or `box`), interior x0..x1 / z0..z1 carved from
    floor_y + 1 to top, a perimeter cornice at `top`, the interior floor patterned
    (polished border, mixed field)."""
    w, h, d = p.size
    p.fill(*(box or (0, 0, 0, w - 1, h - 1, d - 1)), pal["wall"])
    p.clear((x0, floor_y + 1, z0, x1, top, z1))
    _vault(p, _rect(x0, z0, x1, z1), top, pal["stair"])
    for x, z in _rect(x0, z0, x1, z1):
        edge = x in (x0, x1) or z in (z0, z1)
        p.set(x, floor_y, z, pal["trim"] if edge else pal["floor"])
    # plinth course: the wall faces at the floor are polished
    for x, z in _rect(x0 - 1, z0 - 1, x1 + 1, z1 + 1):
        if x in (x0 - 1, x1 + 1) or z in (z0 - 1, z1 + 1):
            p.set(x, floor_y + 1, z, pal["trim"])


# ------------------------------------------------------------------ the entrance
# The start piece is 11 x 38 x 19, the old start's footprint, so its bounding box blocks the
# same ground at the dungeon level as before and Horizon centres the reach box on the same
# point (see PLACE). Three parts are stacked in it:
#   * the vestibule at the bottom, as before: floor y 0, interior x 2..8, z 10..16, doors on
#     the piece's west (x 0), east (x 10) and south (z 18) faces;
#   * a switchback stair in a closed shaft (the whole box below the ground layer is masonry,
#     walls two thick): from the vestibule's north-west corner a short flight climbs north to a
#     landing (z 2..4), then long flights run back and forth over the vestibule on two 3-wide
#     lanes (west x 2..4, east x 6..8) either side of a one-block spine at x 5, turning on
#     3-deep landings (x 2..8) at the north (z 2..4) and south (z 14..16) ends;
#   * the mausoleum on top, its floor in the ground layer GROUND (y 26), which replaces the top
#     block of terrain (PLACE start_height = -GROUND). The stair comes up into an open, railed
#     stairwell in the north half of its floor.
# Climbing from the vestibule floor (y 0): 5 + 9 + 9 + 3 steps to the mausoleum floor (y 26).
GROUND = 26
LANES = {"west": (2, 3, 4), "east": (6, 7, 8)}
# (lane, the direction it climbs, z of its bottom step, floor it starts from, steps)
FLIGHTS = (("west", "north", 9, 0, 5), ("east", "south", 5, 5, 9),
           ("west", "north", 13, 14, 9), ("east", "south", 5, 23, 3))
LANDINGS = ((2, 4, 5), (14, 16, 14), (2, 4, 23))                  # (z0, z1, floor y), x 2..8
MX0, MX1, MZ0, MZ1 = 1, 9, 1, 11                # the mausoleum's outer wall line
WALL_TOP = GROUND + 5                           # top wall course; the roof's eaves are one higher
# the stairwell in its floor: the top landing, both lanes' last two rows, the top step
HOLE = ({(x, z) for x in range(2, 9) for z in (2, 3, 4)}
        | {(x, z) for x in (2, 3, 4, 6, 7, 8) for z in (5, 6)}
        | {(x, 7) for x in (6, 7, 8)})
GRASS = "minecraft:grass_block[snowy=false]"


def _flight_cells(lane, climb, z0, floor, n):
    """[(z, step height)] of a flight, bottom step first."""
    dz = -1 if climb == "north" else 1
    return [(z0 + dz * i, floor + 1 + i) for i in range(n)]


def _weathered(p, dy):
    """Mausoleum wall stone, dy above the ground layer: worn and mossy low down."""
    if dy <= 1:
        return p.rnd.choices(("minecraft:mossy_stone_bricks", "minecraft:cracked_stone_bricks",
                              "minecraft:stone_bricks", "minecraft:mossy_cobblestone",
                              "minecraft:cobblestone"), (4, 3, 3, 2, 1))[0]
    return p.rnd.choices(("minecraft:stone_bricks", "minecraft:cracked_stone_bricks",
                          "minecraft:mossy_stone_bricks", "minecraft:andesite"), (7, 2, 2, 1))[0]


def _vine(p, x, y, z, wall_side):
    """A vine on the face of the block at `wall_side` of the cell (only into air)."""
    if p.get(x, y, z) in (None, AIR):
        p.set(x, y, z, state("minecraft:vine", up=False, **{d: d == wall_side for d in HORIZONTAL}))


def _entrance_site(p):
    """The ground layer: turf over the whole footprint but a few ragged cells at the yard's
    far corners (left to the world), with air over it to the top of the box."""
    w, h, d = p.size
    cx, cz = (w - 1) / 2, (d - 1) / 2
    ground = p.mix((GRASS, 12), ("minecraft:coarse_dirt", 3), ("minecraft:podzol[snowy=false]", 2),
                   ("minecraft:moss_block", 1), ("minecraft:dirt", 1))
    for x in range(w):
        for z in range(d):
            r = abs((x - cx) / (w / 2 + 0.5)) ** 4 + abs((z - cz) / (d / 2 + 0.5)) ** 4
            building = MZ0 - 1 <= z <= MZ1 + 1
            if not building and r > 0.62 + p.rnd.uniform(-0.15, 0.15):
                continue
            p.set(x, GROUND, z, ground)
            for y in range(GROUND + 1, h):
                p.set(x, y, z, AIR)


def _shaft(p, pal):
    """Everything under the ground layer is masonry: deepslate low down, stone higher up,
    stone and cobble footings under the mausoleum and packed earth under the yard."""
    stone = p.mix(("minecraft:stone", 4), ("minecraft:stone_bricks", 3), ("minecraft:cobblestone", 2),
                  ("minecraft:andesite", 2))
    footing = p.mix(("minecraft:cobblestone", 4), ("minecraft:stone_bricks", 3),
                    ("minecraft:mossy_cobblestone", 2), ("minecraft:andesite", 1))
    earth = p.mix(("minecraft:dirt", 5), ("minecraft:coarse_dirt", 2), ("minecraft:stone", 1))
    for x, y, z in Piece.box_cells((0, 0, 0, 10, GROUND - 1, 18)):
        if y >= GROUND - 3:
            block = footing if z <= MZ1 + 1 else earth
        else:
            block = stone if y >= GROUND - 9 else pal["wall"]
        p.set(x, y, z, block)


def _vestibule(p, pal):
    """The old start's vestibule, unchanged but for its north wall, which now opens in the
    north-west corner on the first flight up."""
    _room_shell(p, pal, 2, 10, 8, 16, 5, box=(0, 0, 8, 10, 7, 18))
    p.clear((3, 5, 11, 7, 5, 15))                     # a flat crown inside the cornice
    _vault(p, _rect(2, 10, 8, 16), 5, pal["stair"])
    p.set(5, 6, 13, pal["accent"])
    p.hanging_lantern(5, 5, 13, chain=0, soul=True)
    # floor: a compass of polished rings round a chiseled centre, an aisle to the stair
    for x, z in _rect(3, 11, 7, 15):
        r = max(abs(x - 5), abs(z - 13))
        p.set(x, 0, z, {0: pal["accent"], 1: pal["trim"], 2: "minecraft:deepslate_tiles"}[r])
    for x in (2, 3, 4):
        p.set(x, 0, 10, pal["trim"])
    p.set(5, 0, 16, pal["trim"])
    _door(p, 0, 13, "west", CORRIDORS, pal, arch=True)
    _door(p, 10, 13, "east", CORRIDORS, pal, arch=True)
    _door(p, 5, 18, "south", CORRIDORS, pal, arch=True)
    # the way up (x 2..4): a lintel over it, a polished jamb on the spine side
    for x in (2, 3, 4):
        p.stairs(x, 5, 10, pal["trim_stair"], "north", half="top")
    for y in range(1, 6):
        p.set(5, y, 9, pal["trim"])
    p.set(5, 6, 9, pal["accent"])
    # fittings: a guardian statue beside the way up, a candle stand, niches, candles
    p.wall(5, 1, 10, pal["wall_post"])
    p.wall(5, 2, 10, pal["wall_post"])
    p.skull(5, 3, 10, rotation=0)
    p.wall(8, 1, 10, pal["wall_post"])
    p.candle(8, 2, 10, "white", candles=3)
    for x, z, into in ((1, 10, "east"), (1, 16, "east"), (9, 10, "west"), (9, 16, "west")):
        _niche(p, x, 2, z, into, "skull" if z == 10 else "candles", "white")
    for x, z in ((2, 16), (8, 16), (2, 11), (8, 11)):
        p.candle(x, 1, z, p.rnd.choice(("white", "light_gray")), candles=p.rnd.randint(2, 4))
    p.set(2, 1, 15, "minecraft:bone_block[axis=y]")
    p.skull(2, 2, 15, rotation=13)
    _cobwebs(p, (2, 4, 10, 8, 5, 16), 0.12)


def _stair(p, pal):
    """Landings and flights: four of headroom, a stepped ceiling of upside-down stairs over
    the flights, a polished dado, niches with skulls and candles, soul lights, cobwebs."""
    for z0, z1, f in LANDINGS:
        top = f + 5 >= GROUND                           # the top landing opens into the mausoleum
        p.clear((2, f + 1, z0, 8, min(f + 4, GROUND), z1))
        for x, z in _rect(2, z0, 8, z1):
            edge = x in (2, 8) or z in (z0, z1)
            p.set(x, f, z, pal["trim"] if edge else pal["floor"])
        mid = (z0 + z1) // 2
        p.set(5, f, mid, pal["accent"])
        if not top:
            p.set(5, f + 5, mid, pal["accent"])
            p.hanging_lantern(5, f + 4, mid, chain=0, soul=True)
            _cobwebs(p, (2, f + 4, z0, 8, f + 4, z1), 0.14)
        # niches in the end wall (skull between candles) and both side walls
        end, into = (z0 - 1, "south") if z0 == 2 else (z1 + 1, "north")
        for x, what in ((3, "candles"), (5, "skull"), (7, "candles")):
            _niche(p, x, f + 2, end, into, what, "white")
            p.set(x, f + 3, end, pal["trim"])
        for x, side in ((1, "east"), (9, "west")):
            _niche(p, x, f + 2, mid, side, "skull" if f == 14 else "candles", "white")
            p.set(x, f + 1, mid, pal["trim"])
    for lane, climb, z0, f, n in FLIGHTS:
        back = OPPOSITE[climb]
        outer, into = (1, "east") if lane == "west" else (9, "west")
        cells = _flight_cells(lane, climb, z0, f, n)
        for z, s in cells:
            for x in LANES[lane]:
                p.stairs(x, s, z, "polished_deepslate" if x in (3, 7) else "deepslate_tiles", climb)
                for y in range(s + 1, min(s + 5, GROUND + 1)):
                    p.set(x, y, z, AIR)
                if s + 5 < GROUND:
                    p.stairs(x, s + 5, z, pal["stair"], back, half="top")
            if s + 1 < GROUND:
                p.set(outer, s + 1, z, pal["trim"])
                p.set(5, s + 1, z, pal["trim"])
        # niches in the outer wall, a soul torch on the spine, a few webs up in the ceiling
        for i, what in ((2, "skull"), (n - 3, "candles")):
            z, s = cells[i]
            if n >= 5 and s + 3 < GROUND and (i == 2 or n - 3 != 2):
                _niche(p, outer, s + 2, z, into, what, "white")
        zt, st = cells[n // 2]
        if n >= 5 and st + 5 < GROUND:
            side, face = (4, "west") if lane == "west" else (6, "east")
            p.wall_torch(side, st + 3, zt, face, soul=True)
        for z, s in cells:
            if s + 4 < GROUND:
                for x in (LANES[lane][0], LANES[lane][2]):
                    if p.get(x, s + 4, z) == AIR and p.rnd.random() < 0.18:
                        p.set(x, s + 4, z, "minecraft:cobweb")


def _mausoleum(p):
    """The way in: a small stone mausoleum (9 x 11 inside its buttresses) with a gabled roof,
    a doorway with one door leaf left (the other lies in the grass), the stairwell railed off
    in the north half, a sarcophagus, an altar and a skull shelf in the south half."""
    g = GROUND
    plinth = p.mix(("minecraft:mossy_cobblestone", 3), ("minecraft:cobblestone", 3),
                   ("minecraft:mossy_stone_bricks", 2), ("minecraft:stone", 1))
    for x, z in _rect(MX0, MZ0, MX1, MZ1):
        if x in (MX0, MX1) or z in (MZ0, MZ1):
            p.set(x, g, z, plinth)
            for y in range(g + 1, WALL_TOP):
                p.set(x, y, z, _weathered(p, y - g))
            p.set(x, WALL_TOP, z, "minecraft:polished_andesite" if p.rnd.random() < 0.8
                  else _weathered(p, 5))                # trim course under the eaves
    p.clear((MX0 + 1, g + 1, MZ0 + 1, MX1 - 1, g + 10, MZ1 - 1))
    # floor: polished border, worn field, an aisle from the door; the stairwell left open
    field = p.mix(("minecraft:stone_bricks", 5), ("minecraft:cracked_stone_bricks", 3),
                  ("minecraft:mossy_stone_bricks", 2), ("minecraft:cobblestone", 1))
    for x, z in _rect(MX0 + 1, MZ0 + 1, MX1 - 1, MZ1 - 1):
        if (x, z) in HOLE:
            continue
        edge = x in (MX0 + 1, MX1 - 1) or z in (MZ0 + 1, MZ1 - 1) or (x, z + 1) in HOLE
        p.set(x, g, z, "minecraft:polished_andesite" if edge else field)
    for z in range(8, MZ1):
        p.set(5, g, z, "minecraft:polished_andesite")
    p.set(5, g, 9, "minecraft:chiseled_stone_bricks")
    # corner buttresses (L-shaped, sloped caps) and two pilasters with soul lanterns at the door
    for cx, cz, sx, sz in ((MX0, MZ0, -1, -1), (MX1, MZ0, 1, -1), (MX0, MZ1, -1, 1), (MX1, MZ1, 1, 1)):
        for bx, bz, face in ((cx + sx, cz, "east" if sx < 0 else "west"),
                             (cx, cz + sz, "south" if sz < 0 else "north")):
            for y in range(g, g + 4):
                p.set(bx, y, bz, plinth if y == g else _weathered(p, y - g))
            p.stairs(bx, g + 4, bz, "stone_bricks", face)
    for x in (3, 7):
        p.set(x, g + 1, MZ1 + 1, "minecraft:polished_andesite")
        p.set(x, g + 2, MZ1 + 1, "minecraft:chiseled_stone_bricks")
        p.lantern(x, g + 3, MZ1 + 1, soul=True)
    # the doorway: 3 wide, a corbelled head and keystone, one door leaf standing open
    for x in (4, 5, 6):
        p.set(x, g, MZ1, "minecraft:polished_andesite")
        p.set(x, g + 1, MZ1, AIR)
        p.set(x, g + 2, MZ1, AIR)
    p.set(5, g + 3, MZ1, AIR)
    p.stairs(4, g + 3, MZ1, "stone_bricks", "west", half="top")
    p.stairs(6, g + 3, MZ1, "stone_bricks", "east", half="top")
    p.set(5, g + 4, MZ1, "minecraft:chiseled_stone_bricks")
    p.door(4, g + 1, MZ1, "dark_oak", "north", hinge="left", open=True)
    p.trapdoor(6, g + 1, MZ1 + 3, "dark_oak", "south")          # the fallen leaf, in the grass
    # windows: barred slits in the side walls, one over the stairwell
    for z in (3, 8):
        for x in (MX0, MX1):
            p.bars(x, g + 2, z)
            p.bars(x, g + 3, z)
    # roof: gabled, ridge north-south, two thick, mossy in places; roundels in the gables
    p.gable_roof(MX0, MX1, MZ0, MZ1, WALL_TOP + 1, "stone_bricks", "z", overhang=1,
                 gable_fill=lambda: _weathered(p, 9), under=lambda: _weathered(p, 9))
    for (x, y, z), (b, nbt) in list(p.cells.items()):
        if y > WALL_TOP and b.startswith("minecraft:stone_brick_") and p.rnd.random() < 0.3:
            p.set(x, y, z, b.replace("minecraft:stone_brick_", "minecraft:mossy_stone_brick_"))
    for z in (MZ0, MZ1):
        p.set(5, WALL_TOP + 3, z, "minecraft:chiseled_stone_bricks")
        p.bars(5, WALL_TOP + 4, z)
    # the stairwell: railed along its south edge and along the spine between the lanes
    for x in (2, 3, 4):
        p.wall(x, g + 1, 7, "stone_brick")
    for z in (5, 6, 7):
        p.wall(5, g + 1, z, "stone_brick")
    p.lantern(5, g + 2, 7, soul=True)
    p.candle(2, g + 2, 7, "white", candles=2)
    p.hanging_lantern(5, WALL_TOP + 1, 3, chain=4, soul=True)
    # a sarcophagus against the west wall (lid slid half off), an altar against the east wall,
    # a skull shelf by the door
    for z in (8, 9):
        p.set(2, g + 1, z, "minecraft:polished_andesite")
    p.slab(2, g + 2, 8, "smooth_stone")
    p.skull(2, g + 2, 9, rotation=12)
    p.slab(3, g + 1, 9, "smooth_stone")
    p.candle(3, g + 1, 8, "white", candles=1, lit=False)
    p.set(8, g + 1, 9, "minecraft:chiseled_stone_bricks")
    p.skull(8, g + 2, 9, rotation=4)
    p.candle(8, g + 1, 8, "white", candles=3)
    p.candle(8, g + 1, 10, "white", candles=2)
    for x in (2, 3):
        p.slab(x, g + 3, 10, "stone_brick", type="top")
    p.skull(2, g + 4, 10, rotation=p.rnd.choice((0, 15, 1)))
    p.candle(3, g + 4, 10, "white", candles=4)
    p.slab(7, g + 1, 10, "mossy_cobblestone")                     # a little fallen masonry
    p.scatter((MX0 + 1, g + 1, MZ0 + 1, MX1 - 1, g + 1, MZ1 - 1), "minecraft:moss_carpet", 0.07,
              only_on=lambda b: b is not None and "stone" in b and is_full_solid(b))
    _cobwebs(p, (MX0 + 1, WALL_TOP - 1, MZ0 + 1, MX1 - 1, WALL_TOP + 4, MZ1 - 1), 0.07)


def _churchyard(p):
    """Outside: a worn path to the door, four graves, a broken low wall with gate posts,
    vines from the eaves, grass and a few flowers."""
    g = GROUND
    w, _, d = p.size

    def ground(x, z):
        return p.get(x, g, z) not in (None, AIR) and p.get(x, g + 1, z) == AIR

    path = p.mix(("minecraft:dirt_path", 5), ("minecraft:gravel", 2), ("minecraft:cobblestone", 1),
                 ("minecraft:coarse_dirt", 1))
    for z in range(MZ1 + 1, d):
        xs = (4, 5, 6) if z <= MZ1 + 2 else ((5, 6) if (z - MZ1) % 4 == 3 else (4, 5))
        for x in xs:
            if p.is_set(x, g, z):
                p.set(x, g, z, path)
    # graves: (headstone x, z, the side it stands on); plots run in toward the path
    graves = ((1, 14, "west"), (1, 16, "west"), (9, 13, "east"), (9, 15, "east"))
    kinds = ["stair", "post", "block", "fallen"]
    p.rnd.shuffle(kinds)
    for (hx, z, side), kind in zip(graves, kinds):
        plot = (2, 3) if side == "west" else (8, 7)
        if not all(ground(x, z) for x in (hx,) + plot):
            continue
        for x in plot:
            p.set(x, g, z, p.rnd.choice(("minecraft:podzol[snowy=false]", "minecraft:coarse_dirt",
                                         "minecraft:rooted_dirt")))
        if kind == "stair":
            p.stairs(hx, g + 1, z, "mossy_cobblestone", side)
        elif kind == "post":
            p.wall(hx, g + 1, z, "mossy_stone_brick")
            p.slab(hx, g + 2, z, "stone_brick")
        elif kind == "block":
            p.set(hx, g + 1, z, "minecraft:chiseled_stone_bricks")
            p.candle(hx, g + 2, z, "white", candles=p.rnd.randint(1, 3))
        else:
            p.slab(hx, g + 1, z, "cobblestone")
            p.slab(plot[0], g + 1, z, "mossy_stone_brick")
        if kind != "fallen":
            p.set(plot[0], g + 1, z, "minecraft:moss_carpet")
        if p.rnd.random() < 0.6:
            p.candle(plot[1], g + 1, z, "white", candles=p.rnd.randint(1, 2), lit=p.rnd.random() < 0.5)
    # a broken low wall along the south edge, gate posts with soul lanterns
    for x in (0, 1, 2, 8, 9, 10):
        if ground(x, d - 1) and p.rnd.random() < 0.7:
            p.wall(x, g + 1, d - 1, "mossy_cobblestone")
    for x in (3, 7):
        if ground(x, d - 1):
            p.wall(x, g + 1, d - 1, "mossy_cobblestone")
            p.wall(x, g + 2, d - 1, "mossy_cobblestone")
            p.lantern(x, g + 3, d - 1, soul=True)
    # vines down the walls from under the eaves, moss low on the walls
    for z in range(MZ0, MZ1 + 1):
        for x, side in ((MX0 - 1, "east"), (MX1 + 1, "west")):
            if p.rnd.random() < 0.4:
                for y in range(WALL_TOP, WALL_TOP - p.rnd.randint(2, 5), -1):
                    _vine(p, x, y, z, side)
    for x in range(MX0, MX1 + 1):
        if p.rnd.random() < 0.5:
            for y in range(WALL_TOP, WALL_TOP - p.rnd.randint(1, 4), -1):
                _vine(p, x, y, MZ0 - 1, "south")
    for x in (2, 8):
        for y in range(WALL_TOP, WALL_TOP - p.rnd.randint(2, 4), -1):
            _vine(p, x, y, MZ1 + 1, "north")
    p.replace((MX0, g + 1, MZ0, MX1, g + 2, MZ1), "minecraft:stone_bricks",
              "minecraft:mossy_stone_bricks", 0.3)
    plants = p.mix(("minecraft:short_grass", 10), ("minecraft:fern", 4), ("minecraft:poppy", 1),
                   ("minecraft:azure_bluet", 1))
    p.scatter((0, g + 1, 0, w - 1, g + 1, d - 1), plants, 0.2, only_on=GRASS)


def start():
    """The crypt's way in: a mausoleum on the surface, a switchback stair down a closed shaft
    and the vestibule with its three doors (see the notes above)."""
    p = Piece("crypt/start", 11, GROUND + 12, 19, "crypt/start")
    pal = _pal(p, "deepslate")
    _entrance_site(p)
    _shaft(p, pal)
    _vestibule(p, pal)
    _stair(p, pal)
    _mausoleum(p)
    _churchyard(p)
    return p


# ------------------------------------------------------------------ corridors
def corridor():
    """Straight corridor, 7 wide (walls two thick), 3 wide inside, open at both ends.
    Arched (corbels at y 4, crown to y 4 in the middle), ribs at z 3 and 7 with polished
    pilasters and keystones, burial shelves in the end bays and niches in the middle bay."""
    p = Piece("crypt/corridor", 7, 6, 11, "crypt/corridor")
    pal = _pal(p, "deepslate")
    p.fill(0, 0, 0, 6, 5, 10, pal["wall"])
    p.clear((2, 1, 0, 4, 4, 10))
    _vault(p, _rect(2, 0, 4, 10), 4, pal["stair"], open_=[(x, z) for x in (2, 3, 4) for z in (-1, 11)])
    for z in range(11):
        p.set(3, 0, z, pal["trim"])
        p.set(2, 0, z, pal["floor"])
        p.set(4, 0, z, pal["floor"])
        p.set(1, 1, z, pal["trim"])
        p.set(5, 1, z, pal["trim"])
    for z in (3, 7):                                   # ribs: tuff against the deepslate
        for x in (1, 5):
            p.set(x, 1, z, "minecraft:chiseled_tuff")
            p.pillar(x, z, 2, 3, "minecraft:polished_tuff")
        p.stairs(2, 4, z, "polished_tuff", "west", half="top")
        p.stairs(4, 4, z, "polished_tuff", "east", half="top")
        p.set(3, 5, z, "minecraft:chiseled_tuff_bricks")
        p.set(3, 0, z, pal["accent"])
    # burial shelves (two long, low) in the end bays; niches in the middle bay
    sides = ((1, "east"), (5, "west"))
    for (wx, into), zs in ((sides[0], (1, 2)), (sides[1], (8, 9))):
        for z in zs:
            p.set(wx, 2, z, AIR)
            p.set(wx, 3, z, pal["trim"])
        p.set(wx, 2, zs[0], f"minecraft:bone_block[axis=z]")
        p.skull(wx, 2, zs[1], rotation=ROT[into] + 1)
    for (wx, into), zs in ((sides[1], (1, 2)), (sides[0], (8, 9))):
        _niche(p, wx, 2, zs[0], into, "candles", "white")
        p.set(wx, 3, zs[0], pal["trim"])
    _niche(p, 1, 2, 5, "east", "skull")
    _niche(p, 5, 2, 5, "west", "candles", "white")
    p.set(1, 3, 5, pal["accent"])
    p.set(5, 3, 5, pal["accent"])
    p.hanging_lantern(3, 4, 5, chain=0, soul=True)
    # age: a fallen slab, cobwebs in the vault
    p.slab(4, 1, 9, "cobbled_deepslate")
    p.set(2, 0, 6, "minecraft:cobbled_deepslate")
    _cobwebs(p, (2, 3, 1, 4, 4, 9), 0.07)
    _door(p, 3, 0, "north", BRANCHES, pal, depth=1)
    _door(p, 3, 10, "south", BRANCHES, pal, depth=1)
    return p


def _shrine(p, pal, cx, cz, into, kind):
    """A 3-wide, 3-high recess in the inner wall layer at (cx, cz) (its middle), opening
    toward `into`: 'altar' (skull on a chiseled block between candles) or 'bones' (bones
    stacked with skulls)."""
    lat = cw(into)
    for l in (-1, 0, 1):
        x, z = _step(cx, cz, lat, l)
        for y in (1, 2, 3):
            p.set(x, y, z, AIR)
    for l, d in ((-1, ccw(into)), (1, cw(into))):     # arch head
        x, z = _step(cx, cz, lat, l)
        p.stairs(x, 3, z, pal["trim_stair"], d, half="top")
    if kind == "altar":
        p.set(cx, 1, cz, pal["accent"])
        p.skull(cx, 2, cz, rotation=ROT[into])
        for l in (-1, 1):
            x, z = _step(cx, cz, lat, l)
            p.slab(x, 1, z, pal["trim_stair"], type="top")
            p.candle(x, 2, z, "white", candles=p.rnd.randint(2, 4))
    else:
        for l in (-1, 0, 1):
            x, z = _step(cx, cz, lat, l)
            p.set(x, 1, z, "minecraft:bone_block[axis=y]")
            if l:
                p.skull(x, 2, z, rotation=(ROT[into] + p.rnd.choice((-1, 0, 1))) % 16)
            else:
                p.set(x, 2, z, f"minecraft:bone_block[axis={'x' if into in ('north', 'south') else 'z'}]")
        p.set(cx, 3, cz, "minecraft:cobweb")


def _junction(name, doors):
    """9 x 7 x 9 junction: a 5 x 5 chamber (x, z 2..6) under a stepped dome, doors from
    `doors` (subset of north/east/south/west) through the two-thick walls; shrines in the
    other walls; candle posts in the chamber corners."""
    p = Piece(name, 9, 7, 9, name)
    pal = _pal(p, "deepslate")
    p.fill(0, 0, 0, 8, 6, 8, pal["wall"])
    p.clear((2, 1, 2, 6, 4, 6))
    p.clear((3, 5, 3, 5, 5, 5))
    _vault(p, _rect(2, 2, 6, 6), 4, pal["stair"])
    _vault(p, _rect(3, 3, 5, 5), 5, pal["trim_stair"])
    p.set(4, 6, 4, pal["accent"])
    p.hanging_lantern(4, 5, 4, chain=0, soul=True)
    for x, z in _rect(2, 2, 6, 6):
        r = max(abs(x - 4), abs(z - 4))
        p.set(x, 0, z, {0: pal["accent"], 1: pal["trim"], 2: pal["floor"]}[r])
    for x, z in _rect(1, 1, 7, 7):                     # plinth course
        if x in (1, 7) or z in (1, 7):
            p.set(x, 1, z, pal["trim"])
    centres = {"north": (4, 0), "south": (4, 8), "west": (0, 4), "east": (8, 4)}
    inner = {"north": (4, 1), "south": (4, 7), "west": (1, 4), "east": (7, 4)}
    kinds = ["altar", "bones"]
    for d in HORIZONTAL:
        if d in doors:
            continue
        _shrine(p, pal, *inner[d], OPPOSITE[d], kinds[len(p.cells) % 2] if len(doors) < 3 else "altar")
        kinds.reverse()
    for x, z in ((2, 2), (6, 2), (2, 6), (6, 6)):
        p.wall(x, 1, z, pal["wall_post"])
        p.candle(x, 2, z, "white", candles=p.rnd.randint(1, 3), lit=p.rnd.random() < 0.8)
    for d in doors:
        _door(p, *centres[d], d, BRANCHES, pal)
    _cobwebs(p, (2, 4, 2, 6, 5, 6), 0.08)
    return p


def corner():
    return _junction("crypt/corner", ("south", "east"))


def t_junction():
    return _junction("crypt/t_junction", ("west", "east", "south"))


def crossing():
    return _junction("crypt/crossing", ("north", "east", "south", "west"))


# ------------------------------------------------------------------ rooms
def _coffin(p, x, z, along, lid="smooth_stone", base="minecraft:polished_andesite", state_="closed"):
    """A stone coffin two cells long from (x, z) in direction `along`: a base course with a
    slab lid. state_: closed, open (lid on the floor beside it, bones inside), broken."""
    x2, z2 = _step(x, z, along)
    for cx, cz in ((x, z), (x2, z2)):
        p.set(cx, 1, cz, base)
    if state_ == "closed":
        p.slab(x, 2, z, lid)
        p.slab(x2, 2, z2, lid)
    elif state_ == "open":
        p.set(x2, 1, z2, f"minecraft:bone_block[axis={'x' if along in ('east', 'west') else 'z'}]")
        p.skull(x, 2, z, rotation=ROT[OPPOSITE[along]] + 2)
    else:                                              # broken: half a lid, a crack
        p.slab(x, 2, z, lid)
        p.set(x2, 1, z2, "minecraft:cracked_stone_bricks")


def tomb_hall():
    """15 x 8 x 15. Four piers round a central crossing, eight stone coffins against the
    walls, rows of burial niches above them, a skeleton spawner in the middle."""
    p = Piece("crypt/tomb_hall", 15, 8, 15, "crypt/tomb_hall")
    pal = _pal(p, "stone")
    _room_shell(p, pal, 2, 2, 12, 12, 6)
    # ceiling: ribs along the cross, keystone; a flat crown
    for i in range(2, 13):
        p.set(i, 7, 7, pal["trim"])
        p.set(7, 7, i, pal["trim"])
    p.set(7, 7, 7, pal["accent"])
    # floor: polished cross-aisles, a ring round the spawner
    for i in range(2, 13):
        p.set(i, 0, 7, pal["trim"])
        p.set(7, 0, i, pal["trim"])
    for x, z in _rect(6, 6, 8, 8):
        p.set(x, 0, z, pal["accent"] if (x, z) != (7, 7) else "minecraft:smooth_stone")
    # piers with bases and capitals
    for x, z in ((5, 5), (9, 5), (5, 9), (9, 9)):
        p.set(x, 1, z, pal["accent"])
        p.pillar(x, z, 2, 5, "minecraft:stone_bricks")
        p.set(x, 6, z, pal["trim"])
        for d in HORIZONTAL:
            ax, az = _step(x, z, d)
            p.stairs(ax, 6, az, pal["trim_stair"], OPPOSITE[d], half="top")
            if p.rnd.random() < 0.5:
                p.stairs(ax, 1, az, pal["trim_stair"], OPPOSITE[d])
    # coffins against the walls, foot toward the room
    coffins = ((2, 4, "east"), (2, 10, "east"), (12, 4, "west"), (12, 10, "west"),
               (4, 2, "south"), (10, 2, "south"), (4, 12, "north"), (10, 12, "north"))
    states = ["closed", "closed", "open", "closed", "broken", "closed", "closed", "open"]
    p.rnd.shuffle(states)
    for (x, z, along), st in zip(coffins, states):
        _coffin(p, x, z, along, state_=st)
    # burial niches in the inner wall layer at y 3 between the coffins; candles below
    for z in (3, 5, 9, 11):
        _niche(p, 1, 3, z, "east", p.rnd.choice(("skull", "candles", "bones")), "white")
        _niche(p, 13, 3, z, "west", p.rnd.choice(("skull", "candles", "bones")), "white")
    for x in (3, 5, 9, 11):
        _niche(p, x, 3, 1, "south", p.rnd.choice(("skull", "candles", "bones")), "white")
        _niche(p, x, 3, 13, "north", p.rnd.choice(("skull", "candles", "bones")), "white")
    for x, z in ((3, 3), (11, 3), (3, 11), (11, 11)):
        p.candle(x, 1, z, "white", candles=p.rnd.randint(2, 4))
    # the chest in the north-east corner behind the coffins, a lantern on it
    p.chest(12, 1, 2, "crypt", "west")
    p.spawner(7, 1, 7, "minecraft:skeleton")
    for x, z in ((7, 4), (7, 10), (4, 7), (10, 7)):
        p.hanging_lantern(x, 5, z, chain=1, soul=True)
    _door(p, 7, 0, "north", CORRIDORS, pal, arch=True)
    _door(p, 7, 14, "south", CORRIDORS, pal, arch=True)
    _door(p, 0, 7, "west", CORRIDORS, pal, arch=True)
    _door(p, 14, 7, "east", CORRIDORS, pal, arch=True)
    _cobwebs(p, (2, 5, 2, 12, 6, 12), 0.06)
    for x, z in ((2, 2), (12, 12), (2, 12)):
        if p.get(x, 5, z) == AIR:
            p.set(x, 5, z, "minecraft:cobweb")
    return p


def ossuary():
    """13 x 7 x 13. Walls lined with bone blocks and rows of skulls, a bone pillar on a
    stepped plinth in the middle, bone heaps in the corners; skeleton spawner; a chest in a
    north wall niche."""
    p = Piece("crypt/ossuary", 13, 7, 13, "crypt/ossuary")
    pal = _pal(p, "tuff")
    _room_shell(p, pal, 2, 2, 10, 10, 5)
    bone = lambda: f"minecraft:bone_block[axis={p.rnd.choice(('x', 'y', 'z', 'y'))}]"  # noqa: E731
    # line the inner wall layer with bones; a skull row at y 2 and y 4
    for x, z in _rect(1, 1, 11, 11):
        if x not in (1, 11) and z not in (1, 11):
            continue
        if x in (1, 11) and z in (1, 11):
            continue
        into = "east" if x == 1 else "west" if x == 11 else "south" if z == 1 else "north"
        for y in range(1, 5):
            if y in (2, 4) and (x + z) % 2 == 0:
                p.set(x, y, z, AIR)
                p.skull(x, y, z, rotation=(ROT[into] + p.rnd.choice((-1, 0, 0, 1))) % 16)
            else:
                p.set(x, y, z, bone() if y > 1 else pal["trim"])
    # ceiling ribs of bone
    for i in range(2, 11):
        p.set(i, 6, 6, "minecraft:bone_block[axis=x]")
        p.set(6, 6, i, "minecraft:bone_block[axis=z]")
    # centre: stepped plinth with a bone pillar and skulls, candles
    for x, z in _rect(5, 5, 7, 7):
        p.set(x, 1, z, pal["trim"])
    for x, z, d in ((5, 6, "east"), (7, 6, "west"), (6, 5, "south"), (6, 7, "north")):
        p.stairs(x, 1, z, pal["trim_stair"], d)
    p.pillar(6, 6, 1, 5, "minecraft:bone_block[axis=y]")
    p.set(6, 1, 6, pal["accent"])
    for (x, z), r in zip(((5, 5), (7, 5), (5, 7), (7, 7)), (6, 10, 2, 14)):
        p.skull(x, 2, z, rotation=r)
    # bone heaps in the corners
    for cx, cz in ((2, 2), (10, 2), (2, 10), (10, 10)):
        p.set(cx, 1, cz, bone())
        p.set(cx, 2, cz, bone())
        for d in HORIZONTAL:
            x, z = _step(cx, cz, d)
            if 2 <= x <= 10 and 2 <= z <= 10 and p.rnd.random() < 0.6:
                p.set(x, 1, z, bone())
                if p.rnd.random() < 0.5:
                    p.skull(x, 2, z, rotation=p.rnd.randint(0, 15))
    p.skull(2, 3, 2, rotation=6)
    p.skull(10, 3, 10, rotation=14)
    # the chest in a niche in the north wall, skulls stacked round it
    p.chest(6, 1, 1, "crypt", "south")
    p.set(6, 2, 1, AIR)
    p.skull(6, 2, 1, rotation=0)
    p.spawner(8, 1, 3, "minecraft:skeleton")
    for x, z in ((4, 4), (8, 8)):
        p.hanging_lantern(x, 4, z, chain=1, soul=True)
    for x, z in ((4, 8), (8, 4)):
        p.candle(x, 1, z, "white", candles=p.rnd.randint(2, 4))
    _door(p, 6, 12, "south", CORRIDORS, pal, arch=True)
    _door(p, 0, 6, "west", CORRIDORS, pal, arch=True)
    _door(p, 12, 6, "east", CORRIDORS, pal, arch=True)
    _cobwebs(p, (2, 4, 2, 10, 5, 10), 0.12)
    return p


def chapel():
    """13 x 9 x 15. A nave with a two-stage vault and ribs, pews either side of an aisle,
    an altar on a dais at the north end with a reredos; the chest behind the altar."""
    p = Piece("crypt/chapel", 13, 9, 15, "crypt/chapel")
    pal = _pal(p, "tuff")
    _room_shell(p, pal, 2, 2, 10, 12, 6)
    p.clear((3, 7, 3, 9, 7, 11))
    _vault(p, _rect(3, 3, 9, 11), 7, pal["trim_stair"])
    for z in (4, 7, 10):                               # transverse ribs and pilasters
        for x in range(3, 10):
            p.set(x, 8, z, pal["trim"])
        for x in (1, 11):
            p.pillar(x, z, 2, 5, pal["trim"])
            p.set(x, 6, z, pal["accent"])
        p.set(6, 8, z, pal["accent"])
    # floor: aisle of polished tuff with chiseled stops
    for z in range(5, 13):
        p.set(6, 0, z, pal["trim"])
    for z in (6, 9, 12):
        p.set(6, 0, z, pal["accent"])
    # dais and altar
    for x, z in _rect(2, 2, 10, 3):
        p.set(x, 1, z, pal["trim"])
    for x in range(2, 11):
        p.stairs(x, 1, 4, pal["trim_stair"], "north")
    for x in (5, 6, 7):
        p.set(x, 2, 3, pal["accent"] if x == 6 else "minecraft:polished_tuff")
    p.candle(5, 3, 3, "white", candles=4)
    p.candle(7, 3, 3, "white", candles=3)
    p.skull(6, 3, 3, rotation=0)
    p.chest(6, 2, 2, "crypt", "south")
    for x in (3, 9):                                   # candle stands on the dais
        p.wall(x, 2, 2, "tuff_brick")
        p.candle(x, 3, 2, "white", candles=p.rnd.randint(2, 4))
    # reredos in the north wall: a chiseled column, two lantern niches
    for y in range(2, 7):
        p.set(6, y, 1, pal["accent"] if y % 2 else pal["trim"])
    for x in (4, 8):
        p.set(x, 3, 1, AIR)
        p.set(x, 4, 1, AIR)
        p.lantern(x, 3, 1, soul=True)
        p.slab(x, 4, 1, "polished_tuff", type="top")
    # pews either side of the aisle, backs to the south
    for z in (6, 8, 10):
        for x in (3, 4, 5, 7, 8, 9):
            if (x, z) in ((9, 8), (4, 10)):
                continue                               # broken pew
            p.stairs(x, 1, z, "spruce" if p.rnd.random() < 0.85 else "dark_oak", "south")
    p.slab(9, 1, 8, "spruce")
    p.set(4, 1, 10, "minecraft:cobweb")
    # candle niches along the side walls, lanterns over the aisle
    for z in (5, 8, 11):
        _niche(p, 1, 3, z, "east", "candles", "white")
        _niche(p, 11, 3, z, "west", "candles", "white")
    for z in (6, 9):
        p.hanging_lantern(6, 6, z, chain=1, soul=True)
    _door(p, 6, 14, "south", CORRIDORS, pal, arch=True)
    _door(p, 0, 11, "west", CORRIDORS, pal, arch=True)
    _door(p, 12, 11, "east", CORRIDORS, pal, arch=True)
    _cobwebs(p, (2, 6, 2, 10, 7, 12), 0.08)
    return p


def flooded():
    """13 x 9 x 13. The walking floor is raised to y 2 (connectors at y 3); the chamber's
    pit (floor y 0) has flooded two deep. A causeway with sunken stretches joins the three
    door landings; broken columns stand in the water; a chest lies on the bottom."""
    p = Piece("crypt/flooded", 13, 9, 13, "crypt/flooded")
    pal = _pal(p, "mossy")
    _room_shell(p, pal, 2, 2, 10, 10, 7, floor_y=2)
    p.clear((2, 1, 2, 10, 2, 10))
    for x, z in _rect(2, 2, 10, 10):
        p.set(x, 0, z, p.rnd.choice(("minecraft:mossy_cobblestone", "minecraft:gravel", "minecraft:clay",
                                     "minecraft:mossy_stone_bricks")))
        for y in (1, 2):
            p.set(x, y, z, "minecraft:water[level=0]")
    solid = lambda x, z: [p.set(x, y, z, pal["floor"]) for y in (1, 2)]  # noqa: E731
    # door landings
    for x, z in _rect(5, 9, 7, 10) + _rect(5, 2, 7, 3) + _rect(9, 5, 10, 7):
        solid(x, z)
        p.set(x, 2, z, pal["trim"] if p.rnd.random() < 0.5 else pal["floor"])
    # causeway north-south along x 6 and east along z 6
    for z in range(4, 9):
        solid(6, z)
    for x in (7, 8):
        solid(x, 6)
    for x, z in ((6, 5), (6, 8), (8, 6)):              # sunken stretches: slabs awash
        p.set(x, 2, z, "minecraft:water[level=0]")
        p.slab(x, 2, z, "mossy_stone_brick", waterlogged=True)
    # columns standing in the water (one broken)
    for x, z, top in ((3, 3, 7), (9, 3, 7), (3, 9, 7), (9, 9, 4)):
        p.set(x, 0, z, pal["accent"])
        for y in range(1, top + 1):
            p.set(x, y, z, "minecraft:mossy_stone_bricks" if y < 3 else "minecraft:stone_bricks")
        if top == 7:
            for d in HORIZONTAL:
                ax, az = _step(x, z, d)
                p.stairs(ax, 7, az, pal["trim_stair"], OPPOSITE[d], half="top")
        else:
            p.slab(x, top + 1, z, "mossy_stone_brick")
    p.set(9, 5, 9, "minecraft:soul_lantern[hanging=false,waterlogged=false]")
    for x, z in ((2, 7), (10, 9)):                     # fallen column drums in the water
        p.set(x, 1, z, "minecraft:stone_bricks")
    p.slab(4, 1, 9, "stone_brick", type="top", waterlogged=True)
    # sunken chest and sea lanterns glowing up through the water
    p.set(3, 1, 6, "minecraft:chest[facing=east,type=single,waterlogged=true]",
          {"id": "minecraft:chest", "LootTable": f"{NS}:chests/crypt"})
    p.set(4, 0, 4, "minecraft:sea_lantern")
    p.set(8, 0, 8, "minecraft:sea_lantern")
    # lights and growth
    p.hanging_lantern(6, 6, 6, chain=1, soul=True)
    for x, z in ((5, 9), (7, 3), (10, 5)):
        p.set(x, 3, z, "minecraft:moss_carpet")
    for x, y, z, side in ((2, 4, 5, "west"), (2, 5, 8, "west"), (10, 4, 9, "east"), (4, 5, 2, "north"),
                          (8, 3, 10, "south"), (10, 6, 3, "east")):
        _lichen(p, x, y, z, side)
    for x, z in ((4, 6), (8, 4), (5, 8)):
        if p.get(x, 7, z) == AIR:
            p.set(x, 7, z, "minecraft:hanging_roots[waterlogged=false]")
    _door(p, 6, 12, "south", CORRIDORS, pal, y=3, arch=True)
    _door(p, 6, 0, "north", CORRIDORS, pal, y=3, arch=True)
    _door(p, 12, 6, "east", CORRIDORS, pal, y=3, arch=True)
    _cobwebs(p, (2, 6, 2, 10, 7, 10), 0.05)
    return p


def collapsed():
    """13 x 9 x 13. The vault over the north-east has fallen in: a rubble slope from the
    broken ceiling (a cavity to y 7) down across the floor, a toppled column, a chest dug
    into the foot of the heap; zombie spawner on the clear floor."""
    p = Piece("crypt/collapsed", 13, 9, 13, "crypt/collapsed")
    pal = _pal(p, "ruin")
    _room_shell(p, pal, 2, 2, 10, 10, 6)
    p.clear((6, 7, 2, 10, 7, 6))                       # the cavity the vault fell out of
    rub = _rubble(p)
    for x, z in _rect(2, 2, 10, 10):
        dist = ((x - 10.5) ** 2 + (z - 1.5) ** 2) ** 0.5
        h = int(round(8.4 - 0.95 * dist + p.rnd.uniform(-0.6, 0.6)))
        cap_h = {(7, 5): 0, (6, 5): 1, (5, 5): 2, (8, 5): 2, (6, 6): 2}   # dug-out to the chest
        if (x, z) in cap_h:
            h = min(h, cap_h[(x, z)])
        h = min(h, 7 if (x >= 6 and z <= 6) else 5)
        if h <= 0:
            if dist < 8.5 and p.rnd.random() < 0.35:
                p.slab(x, 1, z, p.rnd.choice(("cobbled_deepslate", "tuff", "deepslate_tile")))
            continue
        for y in range(1, h):
            p.set(x, y, z, rub)
        roll = p.rnd.random()
        if roll < 0.35:
            p.stairs(x, h, z, p.rnd.choice(("cobbled_deepslate", "tuff", "deepslate_bricks")),
                     p.rnd.choice(("south", "west")))
        elif roll < 0.6:
            p.slab(x, h, z, p.rnd.choice(("cobbled_deepslate", "tuff")))
        else:
            p.set(x, h, z, rub)
    for x, z in ((8, 4), (9, 3), (7, 5)):               # a little gravel where it settled
        y = 1
        while p.get(x, y, z) not in (None, AIR) and y < 7:
            y += 1
        if p.get(x, y - 1, z) not in (None, AIR):
            p.set(x, y - 1, z, "minecraft:gravel")
    # the chest dug into the heap's foot
    p.chest(7, 1, 4, "crypt", "south")
    p.set(7, 2, 4, AIR)
    p.set(7, 3, 4, "minecraft:cobbled_deepslate")
    p.set(7, 1, 5, AIR)
    p.set(7, 2, 5, AIR)
    # toppled column: a stub and its drums lying along x
    p.set(3, 1, 4, pal["accent"])
    p.set(3, 2, 4, "minecraft:deepslate[axis=y]")
    for x in (4, 5):
        p.set(x, 1, 4, "minecraft:deepslate[axis=x]")
    # zombie spawner on the clear floor, a fallen lantern, candles
    p.spawner(4, 1, 8, "minecraft:zombie")
    p.set(3, 1, 6, "minecraft:soul_lantern[hanging=false,waterlogged=false]")
    p.hanging_lantern(5, 5, 9, chain=1, soul=True)
    for x, z in ((2, 10), (9, 10)):
        p.candle(x, 1, z, "white", candles=p.rnd.randint(1, 3))
    for x, y, z, side in ((10, 2, 8, "east"), (5, 3, 2, "north"), (2, 4, 3, "west")):
        _lichen(p, x, y, z, side)
    _door(p, 6, 12, "south", CORRIDORS, pal, arch=True)
    _door(p, 0, 6, "west", CORRIDORS, pal, arch=True)
    _cobwebs(p, (2, 5, 2, 10, 7, 10), 0.08)
    return p


def guard_room():
    """15 x 7 x 15. The crypt guards' room: weapon racks, a whetstone and anvil, bunks and
    a chest, a table with stools and barrels, a barred cell with old remains. Vault guardian
    spawner in the middle; four doors."""
    p = Piece("crypt/guard_room", 15, 7, 15, "crypt/guard_room")
    pal = _pal(p, "deepslate")
    _room_shell(p, pal, 2, 2, 12, 12, 5)
    for x, z in _rect(3, 3, 11, 11):                   # checker field
        p.set(x, 0, z, "minecraft:polished_deepslate" if (x + z) % 2 else "minecraft:deepslate_tiles")
    for x, z in _rect(6, 6, 8, 8):
        p.set(x, 0, z, pal["accent"] if (x, z) != (7, 7) else "minecraft:polished_andesite")
    for i in range(2, 13):                             # ceiling ribs
        p.set(i, 6, 7, pal["trim"])
        p.set(7, 6, i, pal["trim"])
    p.set(7, 6, 7, pal["accent"])
    # weapon racks (north wall, west half): posts with spear heads, hooks, whetstone, anvil
    p.set(2, 1, 2, "minecraft:grindstone[face=floor,facing=east]")
    for x in (3, 4, 5):
        p.fence(x, 1, 2, "dark_oak")
        p.set(x, 2, 2, state("minecraft:lightning_rod", facing="up", powered=False, waterlogged=False))
        p.set(x, 3, 1, AIR)
        p.set(x, 3, 1, state("minecraft:tripwire_hook", facing="south", attached=False, powered=False))
    p.set(2, 1, 4, "minecraft:chipped_anvil[facing=north]")
    p.set(2, 1, 5, "minecraft:barrel[facing=east,open=false]")
    # bunks and the chest (north-east)
    p.bed(11, 1, 3, "gray", "north")
    p.bed(12, 1, 3, "gray", "north")
    p.chest(10, 1, 2, "crypt", "south")
    p.set(9, 1, 2, "minecraft:barrel[facing=up,open=false]")
    p.candle(9, 2, 2, "white", candles=2)
    # table and stools (south-east), barrels
    p.fence(10, 1, 10, "dark_oak")
    p.set(10, 2, 10, "minecraft:dark_oak_pressure_plate[powered=false]")
    p.fence(10, 1, 11, "dark_oak")
    p.set(10, 2, 11, "minecraft:dark_oak_pressure_plate[powered=false]")
    p.stairs(9, 1, 10, "dark_oak", "west")
    p.stairs(11, 1, 11, "dark_oak", "east")
    p.candle(10, 3, 10, "white", candles=1)
    for x, y, z in ((12, 1, 12), (12, 2, 12), (11, 1, 12), (12, 1, 9)):
        p.barrel(x, y, z, facing=p.rnd.choice(("up", "west", "north")))
    # the cell (south-west): bars on two sides, remains and a chain inside
    for z in range(9, 13):
        p.bars(5, 1, z)
        p.bars(5, 2, z)
        p.bars(5, 3, z)
    for x in range(2, 5):
        p.bars(x, 1, 9)
        p.bars(x, 2, 9)
        p.bars(x, 3, 9)
    p.set(3, 1, 9, AIR)                                # a bent bar
    p.set(2, 1, 12, "minecraft:bone_block[axis=x]")
    p.skull(3, 1, 12, rotation=9)
    p.chain(2, 4, 11)
    p.chain(2, 5, 11)
    p.set(4, 1, 11, "minecraft:cobweb")
    # guardian spawner in the middle; lights
    p.spawner(7, 1, 7, GUARDIAN)
    for x, z in ((7, 4), (7, 10), (4, 7), (10, 7)):
        p.hanging_lantern(x, 4, z, chain=1, soul=True)
    for x, z, f in ((1, 4, "east"), (13, 4, "west"), (13, 10, "west")):
        p.wall_torch(x + (1 if f == "east" else -1), 3, z, f, soul=True)
    _door(p, 7, 0, "north", CORRIDORS, pal, arch=True)
    _door(p, 7, 14, "south", CORRIDORS, pal, arch=True)
    _door(p, 0, 7, "west", CORRIDORS, pal, arch=True)
    _door(p, 14, 7, "east", CORRIDORS, pal, arch=True)
    _cobwebs(p, (2, 4, 2, 12, 5, 12), 0.05)
    return p


def treasure():
    """13 x 8 x 13, one door (south). A dais across the north end with a great sarcophagus,
    three treasure chests, shadow-block columns, gold plinths with candles, a coffered
    ceiling glowing with shadow ore; a vault guardian spawner on the floor before the dais."""
    p = Piece("crypt/treasure", 13, 8, 13, "crypt/treasure")
    pal = _pal(p, "deepslate")
    pal["wall"] = p.mix(("minecraft:polished_deepslate", 3), ("minecraft:deepslate_tiles", 4),
                        ("minecraft:deepslate_bricks", 3))
    _room_shell(p, pal, 2, 2, 10, 10, 6)
    # coffered ceiling: beams on x 6 and z 6, the four coffers lit with shadow ore
    for x, z in _rect(3, 3, 9, 9):
        if x == 6 or z == 6:
            p.set(x, 6, z, pal["trim"])
        elif x in (3, 9) or z in (3, 9):
            pass
        else:
            p.set(x, 7, z, SHADOW_ORE)
    p.clear((4, 6, 4, 5, 6, 5))
    p.clear((7, 6, 4, 8, 6, 5))
    p.clear((4, 6, 7, 5, 6, 8))
    p.clear((7, 6, 7, 8, 6, 8))
    p.set(6, 7, 6, pal["accent"])
    # floor: aisle and inlays
    for z in range(6, 11):
        p.set(6, 0, z, "minecraft:polished_blackstone" if z % 2 else pal["accent"])
    for x, z in ((4, 8), (8, 8)):
        p.set(x, 0, z, "minecraft:raw_gold_block")
    # dais: x 3..9, z 2..4, a step at z 5
    for x, z in _rect(2, 2, 10, 4):
        p.set(x, 1, z, pal["trim"])
    for x in range(3, 10):
        p.stairs(x, 1, 5, pal["trim_stair"], "north")
    # sarcophagus on the dais
    for x in (5, 6, 7):
        p.set(x, 2, 3, pal["accent"] if x != 6 else "minecraft:polished_deepslate")
    p.slab(5, 3, 3, "deepslate_tiles")
    p.slab(7, 3, 3, "deepslate_tiles")
    p.skull(6, 3, 3, rotation=0, kind="wither_skeleton")
    p.set(6, 2, 4, "minecraft:gold_block")
    p.candle(6, 3, 4, "yellow", candles=3)
    # chests: either end of the dais and behind the sarcophagus
    p.chest(3, 2, 2, "crypt_treasure", "south")
    p.chest(9, 2, 2, "crypt_treasure", "south")
    p.chest(6, 2, 2, "crypt_treasure", "south")
    for x in (4, 8):
        p.set(x, 2, 2, SHADOW)
        p.candle(x, 3, 2, "purple", candles=2)
    # columns and gold plinths
    for x in (3, 9):
        p.set(x, 1, 7, pal["accent"])
        p.pillar(x, 7, 2, 5, SHADOW)
        p.set(x, 6, 7, pal["accent"])
    for x in (4, 8):
        p.set(x, 1, 6, "minecraft:gold_block")
        p.candle(x, 2, 6, "yellow", candles=p.rnd.randint(2, 4))
    # wall niches with soul lanterns and skulls
    for z in (4, 9):
        p.set(1, 2, z, AIR)
        p.lantern(1, 2, z, soul=True)
        p.set(11, 2, z, AIR)
        p.skull(11, 2, z, rotation=4)
    p.spawner(6, 1, 8, GUARDIAN)
    _door(p, 6, 12, "south", EMPTY, pal, arch=True)
    _cobwebs(p, (2, 5, 2, 10, 6, 10), 0.05)
    return p


def cap():
    """Dead end: the doorway bricked up (3 wide, 4 high, 1 deep: the opening plus the
    threshold row under it), so it fits wherever the opening is clear. The pools' fallback;
    its connector becomes masonry. The parent's own door frame shows round it."""
    p = Piece("crypt/cap", 3, 4, 1, "crypt/cap")
    fill = p.mix(("minecraft:cracked_deepslate_bricks", 4), ("minecraft:cobbled_deepslate", 3),
                 ("minecraft:deepslate_bricks", 2), ("minecraft:tuff", 1))
    for x in range(3):
        p.set(x, 0, 0, "minecraft:polished_deepslate")
        for y in (1, 2, 3):
            p.set(x, y, 0, fill)
    p.set(1, 2, 0, "minecraft:chiseled_deepslate")
    p.jigsaw(1, 1, 0, "north", DOOR, DOOR, EMPTY, final_state="minecraft:cracked_deepslate_bricks")
    return p


PLACE = {
    "name": "crypt",
    "pieces": {"crypt/start": start, "crypt/corridor": corridor, "crypt/corner": corner,
               "crypt/t_junction": t_junction, "crypt/crossing": crossing,
               "crypt/tomb_hall": tomb_hall, "crypt/ossuary": ossuary, "crypt/chapel": chapel,
               "crypt/flooded": flooded, "crypt/collapsed": collapsed,
               "crypt/guard_room": guard_room, "crypt/treasure": treasure, "crypt/cap": cap},
    # Surface-anchored through the start piece. Horizon's place_start (jigsaw.rs) samples
    # start_height, adds base_height(WORLD_SURFACE_WG) at the centre of the start's (rotated) box,
    # which is the first free cell above the terrain (generator.rs base_height: top block + 1),
    # and moves the piece so its bottom + ground_level_delta (1 for a single_pool_element)
    # lands there. So the bottom layer goes to top block + start_height, and layer GROUND (26,
    # the mausoleum floor and turf) replaces the top block of terrain when start_height is
    # -GROUND. Rotation turns the box about y only, so it changes nothing here. The vestibule
    # floor ends up 26 below the surface.
    # max_distance stays the default 80: lay_out_children centres the reach box on the centre of
    # the start's box horizontally and on its bottom + 1 vertically. The start keeps the old
    # 11 x 19 footprint and its vestibule at the bottom, so both centres sit where they did
    # relative to the vestibule's doors, and every piece at the dungeon level has the same
    # reach as before. (The extra height above y 12 meets no other piece.)
    "step": "surface_structures",
    "start_height": -GROUND,        # -26
    "surface": True,
    "terrain": "none",
    "biomes": ["#minecraft:is_forest", "#minecraft:is_taiga", "#minecraft:is_savanna", "#minecraft:is_badlands", "#minecraft:is_hill", "#minecraft:is_mountain", "#minecraft:is_jungle", "minecraft:plains", "minecraft:sunflower_plains", "minecraft:meadow", "minecraft:desert", "minecraft:snowy_plains", "minecraft:cherry_grove"],
    "spacing": 18,
    "separation": 7,
    "salt": 418200111,
    "size": 5,
    "pools": {
        "crypt/start": [("crypt/start", 1)],
        "crypt/corridors": {"fallback": "crypt/caps", "elements": [
            ("crypt/corridor", 4), ("crypt/corner", 2), ("crypt/t_junction", 1), ("crypt/crossing", 1),
        ]},
        "crypt/branches": {"fallback": "crypt/caps", "elements": [
            {"piece": "crypt/treasure", "guaranteed": 1, "min_depth": 2},
            ("crypt/corridor", 2), ("crypt/corner", 1), ("crypt/t_junction", 1),
            ("crypt/tomb_hall", 2), ("crypt/ossuary", 2), ("crypt/collapsed", 2),
            {"piece": "crypt/chapel", "weight": 1, "limit": 1},
            {"piece": "crypt/flooded", "weight": 1, "limit": 1},
            {"piece": "crypt/guard_room", "weight": 2, "limit": 2},
        ]},
        "crypt/caps": [("crypt/cap", 1)],
    },
}
