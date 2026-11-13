"""Aquite shrine: a prismarine water shrine (surface). PLACEHOLDER geometry from 0.2;
rewrite to the brief in docs/design/places.md section 3.
"""
from structkit import AIR, NS, Piece  # noqa: F401


def build():
    p = Piece("aquite_shrine", 7, 6, 7, "shrine")
    for x in range(7):
        for z in range(7):
            edge = x in (0, 6) or z in (0, 6)
            p.set(x, 0, z, "minecraft:dark_prismarine" if edge else "minecraft:prismarine_bricks")
    p.fill(0, 1, 0, 6, 5, 6, AIR)
    for x, z in ((1, 1), (5, 1), (1, 5), (5, 5)):
        p.fill(x, 1, z, x, 3, z, "minecraft:prismarine_bricks")
        p.set(x, 4, z, "minecraft:sea_lantern")
    for x, z in ((3, 0), (0, 3), (6, 3), (3, 6)):
        p.set(x, 1, z, f"{NS}:aquiteore")                         # glowing ore set in the rim
    p.fill(2, 1, 2, 4, 1, 4, "minecraft:prismarine")
    p.set(3, 1, 3, "minecraft:dark_prismarine")
    p.chest(3, 2, 3, "aquite_shrine", "south")
    return p


PLACE = {
    "name": "aquite_shrine",
    "pieces": {"aquite_shrine": build},
    "step": "surface_structures",
    "start_height": -1,
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
