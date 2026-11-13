"""Colosifite watchtower: a stone tower with sentries (surface). PLACEHOLDER geometry
from 0.2; rewrite to the brief in docs/design/places.md section 4.
"""
from structkit import AIR, NS, Piece  # noqa: F401


def build():
    p = Piece("colosifite_watchtower", 7, 15, 7, "tower")
    wall = p.mix(("minecraft:stone_bricks", 6), ("minecraft:cracked_stone_bricks", 2), ("minecraft:mossy_stone_bricks", 1))
    p.shell(0, 0, 0, 6, 12, 6, wall)
    for y in (4, 8):
        p.fill(1, y, 1, 5, y, 5, "minecraft:spruce_planks")       # upper floors
    for y in range(1, 13):
        p.set(3, y, 1, "minecraft:ladder[facing=south,waterlogged=false]")
    for y in (1, 2):
        p.set(3, y, 6, AIR)                                       # door
    for y in (6, 10):                                             # arrow slits
        for x, z in ((3, 0), (0, 3), (6, 3), (3, 6)):
            p.set(x, y, z, AIR)
    p.fill(0, 13, 0, 6, 14, 6, AIR)
    for x in range(7):                                            # battlements
        for z in range(7):
            if (x in (0, 6) or z in (0, 6)) and (x + z) % 2 == 0:
                corner = x in (0, 6) and z in (0, 6)
                p.set(x, 13, z, f"{NS}:colosfiteblock" if corner else wall())
    p.chest(1, 1, 5, "colosifite_watchtower", "north")
    p.chest(5, 9, 5, "colosifite_watchtower", "north")
    p.spawner(3, 9, 3, f"{NS}:tower_sentry")                      # roofed, so the sentries do not burn
    p.set(5, 5, 1, "minecraft:hay_block[axis=y]")
    p.barrel(1, 5, 5, "up")
    return p


PLACE = {
    "name": "colosifite_watchtower",
    "pieces": {"colosifite_watchtower": build},
    "step": "surface_structures",
    "start_height": -1,
    "surface": True,
    "terrain": "beard_thin",
    "biomes": [
        "#minecraft:is_hill",
        "#minecraft:is_savanna",
        "#minecraft:is_badlands",
    ],
    "spacing": 34,
    "separation": 12,
    "salt": 418200104,
}
