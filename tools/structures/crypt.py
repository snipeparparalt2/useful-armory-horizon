"""Crypt dungeon (underground, Y -10 to 30): built from jigsaw pieces, different every time.

PLACEHOLDER pieces: tiny but real, to show the pool and connector conventions. Rewrite them to
the brief in docs/design/places.md section 12 (entrance, corridor kinds, six room kinds,
treasure room, dead ends), keeping the conventions below.

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
  For rigid pieces the floors line up when P and C are at the same height above each
  piece's floor (all connectors here are at y = 1, one above the floor at y = 0).
* The child's bounding box must not overlap any placed piece and must stay inside the
  start's max_distance_from_center (80 here); otherwise the next candidate is tried.
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

Here every doorway connector has name = target = "useful_armory:crypt/door", so any door
fits any door. Give connectors different names (say crypt/corridor_end and crypt/room_door,
with each one's target naming the other kind) when a door must only take a certain kind.
"""
from structkit import AIR, NS, Piece

DOOR = f"{NS}:crypt/door"
CORRIDORS, ROOMS, CAPS = f"{NS}:crypt/corridors", f"{NS}:crypt/rooms", f"{NS}:crypt/caps"


def _brick(p):
    return p.mix(("minecraft:deepslate_bricks", 6), ("minecraft:cracked_deepslate_bricks", 2),
                 ("minecraft:deepslate_tiles", 1))


def _doorway(p, x, z, along_x):
    """A 3-wide, 3-high opening centred on (x, z) in a wall, floor at y = 0."""
    for d in (-1, 0, 1):
        for y in (1, 2, 3):
            p.set(x + d if along_x else x, y, z if along_x else z + d, AIR)


def start():
    """Vestibule: 7 x 7 x 7, doors west, east and south."""
    p = Piece("crypt/start", 7, 7, 7, "crypt/start")
    p.shell(0, 0, 0, 6, 6, 6, _brick(p))
    p.floor(1, 0, 1, 5, 5, "minecraft:polished_deepslate")
    _doorway(p, 0, 3, along_x=False)
    _doorway(p, 6, 3, along_x=False)
    _doorway(p, 3, 6, along_x=True)
    p.jigsaw(0, 1, 3, "west", DOOR, DOOR, CORRIDORS)
    p.jigsaw(6, 1, 3, "east", DOOR, DOOR, CORRIDORS)
    p.jigsaw(3, 1, 6, "south", DOOR, DOOR, CORRIDORS)
    p.stairs(3, 1, 1, "deepslate_bricks", "north")        # stub of the way up
    p.hanging_lantern(3, 4, 3, chain=1, soul=True)
    return p


def corridor():
    """Straight corridor: 5 wide, 5 high, 9 long, open at both ends (north and south)."""
    p = Piece("crypt/corridor", 5, 5, 9, "crypt/corridor")
    brick = _brick(p)
    p.fill(0, 0, 0, 4, 4, 8, brick)
    p.clear((1, 1, 0, 3, 3, 8))
    p.floor(1, 0, 0, 3, 8, "minecraft:deepslate_tiles")
    for z in (2, 6):                                      # arch ribs
        p.stairs(1, 3, z, "deepslate_bricks", "west", half="top")
        p.stairs(3, 3, z, "deepslate_bricks", "east", half="top")
    p.skull(1, 1, 4, rotation=12)
    p.candle(3, 1, 4, candles=2)
    p.set(2, 3, 5, "minecraft:cobweb")
    p.jigsaw(2, 1, 0, "north", DOOR, DOOR, ROOMS)
    p.jigsaw(2, 1, 8, "south", DOOR, DOOR, ROOMS)
    return p


def room():
    """Tomb room: 11 x 7 x 11, a door in each wall, two coffins, a chest and a spawner."""
    p = Piece("crypt/room", 11, 7, 11, "crypt/room")
    p.shell(0, 0, 0, 10, 6, 10, _brick(p))
    p.floor(1, 0, 1, 9, 9, "minecraft:polished_deepslate")
    for x, z, facing in ((5, 0, "north"), (5, 10, "south"), (0, 5, "west"), (10, 5, "east")):
        _doorway(p, x, z, along_x=facing in ("north", "south"))
        p.jigsaw(x, 1, z, facing, DOOR, DOOR, CORRIDORS)
    for x in (2, 8):                                      # coffins
        p.fill(x, 1, 2, x, 1, 3, "minecraft:polished_deepslate")
        p.slab(x, 2, 2, "deepslate_tiles")
        p.slab(x, 2, 3, "deepslate_tiles")
    p.chest(8, 1, 8, "crypt", "west")
    p.spawner(5, 1, 5, "minecraft:skeleton")
    for x, z in ((2, 8), (8, 5)):
        p.candle(x, 1, z, candles=3)
    p.hanging_lantern(5, 4, 2, chain=1, soul=True)
    return p


def treasure():
    """Treasure room: 9 x 7 x 9, one door (north). Exactly one per crypt (guaranteed)."""
    p = Piece("crypt/treasure", 9, 7, 9, "crypt/treasure")
    p.shell(0, 0, 0, 8, 6, 8, _brick(p))
    p.floor(1, 0, 1, 7, 7, "minecraft:deepslate_tiles")
    _doorway(p, 4, 0, along_x=True)
    p.jigsaw(4, 1, 0, "north", DOOR, DOOR, "minecraft:empty")
    p.fill(3, 1, 5, 5, 1, 7, "minecraft:polished_deepslate")  # dais
    p.chest(4, 2, 6, "crypt_treasure", "north")
    for x in (1, 7):
        p.pillar(x, 1, 1, 5, f"{NS}:shadowblock")
    p.spawner(4, 1, 3, f"{NS}:vault_guardian")
    p.lantern(3, 2, 6, soul=True)
    p.lantern(5, 2, 6, soul=True)
    return p


def cap():
    """Dead end: a 5 x 5 wall that seals an opening (the pools' fallback)."""
    p = Piece("crypt/cap", 5, 5, 1, "crypt/cap")
    p.fill(0, 0, 0, 4, 4, 0, _brick(p))
    p.jigsaw(2, 1, 0, "north", DOOR, DOOR, "minecraft:empty", final_state="minecraft:deepslate_bricks")
    return p


PLACE = {
    "name": "crypt",
    "pieces": {"crypt/start": start, "crypt/corridor": corridor, "crypt/room": room,
               "crypt/treasure": treasure, "crypt/cap": cap},
    "step": "underground_structures",
    "start_height": (-10, 30),
    "surface": False,
    "terrain": "none",
    "biomes": ["#minecraft:is_overworld"],
    "spacing": 18,
    "separation": 7,
    "salt": 418200111,
    "size": 5,
    "pools": {
        "crypt/start": [("crypt/start", 1)],
        "crypt/corridors": {"fallback": "crypt/caps", "elements": [("crypt/corridor", 1)]},
        "crypt/rooms": {"fallback": "crypt/caps", "elements": [
            {"piece": "crypt/treasure", "guaranteed": 1, "min_depth": 3},
            ("crypt/room", 3),
        ]},
        "crypt/caps": [("crypt/cap", 1)],
    },
}
