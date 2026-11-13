"""Forgotten armory: a buried arsenal (underground, Y -30 to 20, rare). PLACEHOLDER
geometry from 0.2; rewrite to the brief in docs/design/places.md section 8.
"""
from structkit import AIR, NS, Piece  # noqa: F401


def build():
    p = Piece("forgotten_armory", 17, 6, 9, "armory")
    wall = p.mix(("minecraft:stone_bricks", 6), ("minecraft:cracked_stone_bricks", 2), ("minecraft:mossy_stone_bricks", 1))
    p.shell(0, 0, 0, 16, 5, 8, wall)
    for x in (5, 11):                                             # two inner walls, a doorway in each
        p.fill(x, 1, 1, x, 4, 7, wall)
        for y in (1, 2):
            p.set(x, y, 4, AIR)
    # west room: the library
    p.fill(1, 1, 1, 4, 2, 1, "minecraft:bookshelf")
    p.chest(1, 1, 7, "forgotten_armory", "north")
    p.set(4, 1, 7, "minecraft:lantern[hanging=false,waterlogged=false]")
    # middle room: the guard post
    for x, z in ((6, 1), (10, 1), (6, 7), (10, 7)):
        p.fill(x, 1, z, x, 4, z, "minecraft:chiseled_stone_bricks")
    p.spawner(8, 1, 4, f"{NS}:vault_guardian")
    p.set(8, 4, 2, "minecraft:cobweb")
    p.set(7, 4, 6, "minecraft:cobweb")
    # east room: the workshop
    p.set(15, 1, 1, "minecraft:smithing_table")
    p.set(14, 1, 1, "minecraft:damaged_anvil[facing=north]")
    p.set(12, 1, 1, "minecraft:grindstone[face=floor,facing=north]")
    p.set(15, 1, 4, f"{NS}:colosfiteblock")
    p.chest(15, 1, 7, "forgotten_armory", "north")
    p.set(12, 1, 7, "minecraft:lantern[hanging=false,waterlogged=false]")
    return p


PLACE = {
    "name": "forgotten_armory",
    "pieces": {"forgotten_armory": build},
    "step": "underground_structures",
    "start_height": (-30, 20),
    "surface": False,
    "terrain": "none",
    "biomes": [
        "#minecraft:is_overworld",
    ],
    "spacing": 40,
    "separation": 14,
    "salt": 418200108,
}
