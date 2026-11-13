"""Bandit fort (surface; plains, forests, taiga, savanna; common). PLACEHOLDER: a small
stockade with a gate, a hut and one chest, to prove the pipeline. Rewrite to the brief in
docs/design/places.md section 10 (about 37 x 16 x 37, four spawners, three chests).
"""
from structkit import AIR, Piece


def build():
    p = Piece("bandit_fort", 13, 8, 13, "bandit_fort")
    ground = p.mix(("minecraft:coarse_dirt", 3), ("minecraft:dirt_path", 1), ("minecraft:grass_block[snowy=false]", 2))
    p.floor(0, 0, 0, 12, 12, ground)
    p.clear((0, 1, 0, 12, 7, 12))
    for x in range(1, 12):                                  # palisade: logs topped with fences
        for z in range(1, 12):
            if x in (1, 11) or z in (1, 11):
                for y in (1, 2, 3):
                    p.log(x, y, z, "spruce", "y")
                p.fence(x, 4, z, "spruce")
    for y in (1, 2, 3, 4):                                  # the gate gap, south side
        for x in (5, 6, 7):
            p.set(x, y, 11, AIR)
    p.fence_gate(6, 1, 11, "spruce", "south")
    p.walls(3, 1, 3, 7, 3, 6, "minecraft:spruce_planks")    # a hut
    p.door(5, 1, 6, "spruce", "north")
    p.pane(3, 2, 4)
    p.pane(7, 2, 4)
    p.gable_roof(3, 7, 3, 6, 4, "spruce", "x", overhang=1, gable_fill="minecraft:spruce_planks",
                 under="minecraft:spruce_planks")
    p.chest(4, 1, 4, "bandit_fort", "south")
    p.set(9, 0, 8, "minecraft:cobblestone")
    p.set(9, 1, 8, "minecraft:campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    p.spawner(9, 1, 4, "minecraft:pillager")
    p.lantern(6, 1, 5)
    return p


PLACE = {
    "name": "bandit_fort",
    "pieces": {"bandit_fort": build},
    "step": "surface_structures",
    "start_height": -1,
    "surface": True,
    "terrain": "beard_thin",
    "biomes": [
        "#minecraft:is_forest",
        "#minecraft:is_taiga",
        "#minecraft:is_savanna",
        "minecraft:plains",
        "minecraft:sunflower_plains",
        "minecraft:meadow",
    ],
    "spacing": 20,
    "separation": 8,
    "salt": 418200109,
}
