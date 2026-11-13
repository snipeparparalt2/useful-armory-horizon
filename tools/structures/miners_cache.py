"""Miner's cache: a worked-out mine junction (underground, Y 0 to 40). PLACEHOLDER
geometry from 0.2; rewrite to the brief in docs/design/places.md section 7.
"""
from structkit import AIR, NS, Piece  # noqa: F401


def build():
    p = Piece("miners_cache", 7, 6, 11, "cache")
    rock = p.mix(("minecraft:stone", 5), ("minecraft:cobblestone", 3), ("minecraft:andesite", 1))
    p.shell(1, 0, 0, 5, 4, 10, rock)
    for z in (2, 5, 8):                                           # timber frames
        for x in (1, 5):
            p.fill(x, 1, z, x, 3, z, "minecraft:oak_log[axis=y]")
        p.fill(1, 4, z, 5, 4, z, "minecraft:oak_planks")
    for z in range(1, 10):
        if z not in (4, 7):                                       # a few rails are missing
            p.set(3, 1, z, "minecraft:rail[shape=north_south,waterlogged=false]")
    p.chest(2, 1, 5, "miners_cache", block="minecraft:barrel")
    p.set(4, 1, 9, "minecraft:gravel")
    p.set(4, 2, 9, "minecraft:gravel")
    p.set(4, 1, 8, "minecraft:gravel")
    p.set(2, 1, 9, "minecraft:cobblestone")
    p.set(4, 3, 2, "minecraft:cobweb")
    p.set(2, 3, 8, "minecraft:cobweb")
    p.set(4, 1, 2, "minecraft:lantern[hanging=false,waterlogged=false]")
    p.set(2, 1, 6, f"{NS}:colosifiteore")
    return p


PLACE = {
    "name": "miners_cache",
    "pieces": {"miners_cache": build},
    "step": "underground_structures",
    "start_height": (0, 40),
    "surface": False,
    "terrain": "none",
    "biomes": [
        "#minecraft:is_overworld",
    ],
    "spacing": 18,
    "separation": 6,
    "salt": 418200107,
}
