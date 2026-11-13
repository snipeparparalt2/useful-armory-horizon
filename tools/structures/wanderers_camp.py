"""Wanderer's camp: tents round a fire (surface). PLACEHOLDER geometry from 0.2;
rewrite to the brief in docs/design/places.md section 2.
"""
from structkit import AIR, NS, Piece  # noqa: F401


def build():
    p = Piece("wanderers_camp", 7, 4, 7, "camp")
    ground = p.mix(("minecraft:coarse_dirt", 3), ("minecraft:dirt_path", 1), ("minecraft:gravel", 1))
    p.fill(0, 0, 0, 6, 0, 6, ground)
    p.fill(0, 1, 0, 6, 3, 6, AIR)
    p.set(3, 0, 3, "minecraft:cobblestone")
    p.set(3, 1, 3, "minecraft:campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    for x0, z0, wool in ((0, 0, "minecraft:white_wool"), (4, 4, "minecraft:red_wool")):
        for z in range(z0, z0 + 3):                                # a ridge tent, open at both ends
            p.set(x0, 1, z, wool)
            p.set(x0 + 2, 1, z, wool)
            p.set(x0 + 1, 2, z, wool)
    p.chest(5, 1, 1, "wanderers_camp", block="minecraft:barrel")
    p.set(5, 1, 2, "minecraft:crafting_table")
    p.set(1, 1, 5, "minecraft:hay_block[axis=y]")
    p.set(3, 1, 5, "minecraft:spruce_log[axis=x]")
    p.set(1, 1, 3, "minecraft:spruce_log[axis=z]")
    p.set(2, 1, 4, "minecraft:lantern[hanging=false,waterlogged=false]")
    return p


PLACE = {
    "name": "wanderers_camp",
    "pieces": {"wanderers_camp": build},
    "step": "surface_structures",
    "start_height": -1,
    "surface": True,
    "terrain": "beard_thin",
    "biomes": [
        "#minecraft:is_forest",
        "#minecraft:is_taiga",
        "#minecraft:is_savanna",
        "minecraft:plains",
        "minecraft:snowy_plains",
        "minecraft:desert",
        "minecraft:meadow",
    ],
    "spacing": 24,
    "separation": 8,
    "salt": 418200102,
}
