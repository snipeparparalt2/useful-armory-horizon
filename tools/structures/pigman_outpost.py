"""Pigman outpost: a nether brick keep (Nether wastes, placed by height). PLACEHOLDER
geometry from 0.2; rewrite to the brief in docs/design/places.md section 5.
"""
from structkit import AIR, NS, Piece  # noqa: F401


def build():
    p = Piece("pigman_outpost", 9, 6, 9, "outpost")
    brick = p.mix(("minecraft:nether_bricks", 6), ("minecraft:cracked_nether_bricks", 2))
    p.shell(0, 0, 0, 8, 5, 8, brick)
    for x, z in ((1, 1), (7, 1), (1, 7), (7, 7)):
        p.fill(x, 1, z, x, 4, z, "minecraft:gold_block" if (x, z) in ((1, 1), (7, 1)) else "minecraft:chiseled_nether_bricks")
    for y in (1, 2):
        p.set(4, y, 8, AIR)                                       # door
    p.set(4, 0, 4, "minecraft:magma_block")
    p.spawner(4, 1, 4, "minecraft:zombified_piglin")
    p.chest(4, 1, 1, "pigman_outpost", "south")
    p.set(3, 1, 1, "minecraft:gold_block")
    p.set(5, 1, 1, "minecraft:gold_block")
    p.set(2, 1, 6, "minecraft:lantern[hanging=false,waterlogged=false]")
    p.set(6, 1, 6, "minecraft:lantern[hanging=false,waterlogged=false]")
    return p


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
