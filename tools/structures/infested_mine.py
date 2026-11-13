"""Infested mine (underground, Y -20 to 40; common). PLACEHOLDER: one webbed drift with a
cave spider spawner and a chest, to prove the pipeline. Rewrite to the brief in
docs/design/places.md section 11 (about 45 x 14 x 45, six spawners, four chests).
"""
from structkit import Piece


def build():
    p = Piece("infested_mine", 9, 6, 15, "infested_mine")
    rock = p.mix(("minecraft:stone", 5), ("minecraft:cobblestone", 2), ("minecraft:andesite", 1),
                 ("minecraft:tuff", 1))
    p.shell(0, 0, 0, 8, 5, 14, rock)
    for z in (2, 7, 12):                                    # timber sets, some broken
        for x in (1, 7):
            p.pillar(x, z, 1, 3, "minecraft:oak_log[axis=y]")
        for x in range(1, 8):
            p.log(x, 4, z, "oak", "x")
        p.fence(3, 3, z, "oak")
    for z in range(1, 14):
        if z % 5 != 3:
            p.set(4, 1, z, "minecraft:rail[shape=north_south,waterlogged=false]")
    p.scatter((1, 2, 1, 7, 4, 13), "minecraft:cobweb", 0.12)
    p.set(1, 1, 10, "minecraft:white_wool")                 # an egg sac
    p.set(1, 2, 10, "minecraft:cobweb")
    p.set(7, 2, 5, "useful_armory:colosifiteore")
    p.spawner(4, 1, 8, "minecraft:cave_spider")
    p.chest(6, 1, 13, "infested_mine", "north")
    p.hanging_lantern(4, 3, 4)
    return p


PLACE = {
    "name": "infested_mine",
    "pieces": {"infested_mine": build},
    "step": "underground_structures",
    "start_height": (-20, 40),
    "surface": False,
    "terrain": "none",
    "biomes": ["#minecraft:is_overworld"],
    "spacing": 16,
    "separation": 6,
    "salt": 418200110,
}
