"""Ruined forge: a burned-out stone smithy (surface). PLACEHOLDER geometry from 0.2;
rewrite to the brief in docs/design/places.md section 1.
"""
from structkit import AIR, NS, Piece  # noqa: F401


def build():
    p = Piece("ruined_forge", 9, 6, 9, "forge")
    floor = p.mix(("minecraft:cobblestone", 5), ("minecraft:mossy_cobblestone", 2), ("minecraft:stone_bricks", 2))
    wall = p.mix(("minecraft:stone_bricks", 5), ("minecraft:cracked_stone_bricks", 2), ("minecraft:mossy_stone_bricks", 2))
    p.fill(0, 0, 0, 8, 0, 8, floor)
    p.fill(0, 1, 0, 8, 5, 8, AIR)
    for x in range(9):
        for z in range(9):
            if x in (0, 8) or z in (0, 8):
                corner = x in (0, 8) and z in (0, 8)
                # the walls have crumbled: lower away from the corners
                top = 4 if corner else p.rnd.choice((1, 2, 2, 3, 3))
                for y in range(1, top + 1):
                    p.set(x, y, z, wall())
    for y in (1, 2):
        p.set(4, y, 8, AIR)                                       # doorway
    p.set(1, 1, 1, "minecraft:furnace[facing=south,lit=false]")
    p.set(2, 1, 1, "minecraft:blast_furnace[facing=south,lit=false]")
    p.set(4, 1, 1, "minecraft:smithing_table")
    p.set(6, 1, 2, "minecraft:damaged_anvil[facing=north]")
    p.set(7, 1, 6, "minecraft:cauldron")
    p.set(7, 1, 1, "minecraft:mossy_cobblestone")
    p.set(6, 1, 7, "minecraft:cobblestone")
    p.chest(1, 1, 6, "ruined_forge", "east")
    return p


PLACE = {
    "name": "ruined_forge",
    "pieces": {"ruined_forge": build},
    "step": "surface_structures",
    "start_height": -1,
    "surface": True,
    "terrain": "beard_thin",
    "biomes": [
        "#minecraft:is_forest",
        "minecraft:plains",
        "minecraft:sunflower_plains",
        "minecraft:meadow",
    ],
    "spacing": 28,
    "separation": 10,
    "salt": 418200101,
}
