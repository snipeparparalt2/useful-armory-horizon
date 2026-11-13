"""Armory blacksmith: a smithy added to vanilla villages' house pools. PLACEHOLDER geometry from
0.2; rewrite to the brief in docs/design/places.md section 9. Keep the jigsaw connector: name
and target minecraft:building_entrance, at ground level on the front edge, facing out (south).
"""
from structkit import AIR, NS, Piece  # noqa: F401


def build():
    p = Piece("village/armory_blacksmith", 9, 7, 9, "blacksmith")
    p.fill(0, 0, 0, 8, 0, 8, "minecraft:cobblestone")
    p.fill(0, 1, 0, 8, 6, 8, AIR)
    p.shell(0, 1, 0, 8, 4, 6, "minecraft:oak_planks")             # the shop
    p.fill(0, 1, 0, 8, 1, 6, "minecraft:cobblestone")             # stone footing course
    p.fill(1, 1, 1, 7, 1, 5, AIR)
    for x, z in ((0, 0), (8, 0), (0, 6), (8, 6), (0, 8), (8, 8)):
        p.fill(x, 1, z, x, 4, z, "minecraft:oak_log[axis=y]")
    p.fill(0, 4, 0, 8, 4, 8, "minecraft:spruce_planks")           # roof, over the porch too
    p.fill(1, 5, 1, 7, 5, 7, "minecraft:spruce_slab[type=bottom,waterlogged=false]")
    for y in (1, 2):
        p.set(4, y, 6, AIR)                                       # door
    p.set(2, 2, 6, "minecraft:glass")
    p.set(6, 2, 6, "minecraft:glass")
    p.chest(1, 1, 1, "village_blacksmith", "south")
    p.set(4, 1, 1, "minecraft:blast_furnace[facing=south,lit=false]")
    p.set(7, 1, 1, "minecraft:smithing_table")
    p.set(7, 1, 4, "minecraft:lantern[hanging=false,waterlogged=false]")
    # the porch
    p.set(1, 1, 7, "minecraft:furnace[facing=south,lit=false]")
    p.set(6, 1, 7, "minecraft:anvil[facing=east]")
    p.set(7, 1, 7, "minecraft:grindstone[face=floor,facing=north]")
    # where a village street joins on
    p.jigsaw(4, 0, 8, "south_up", "minecraft:building_entrance", "minecraft:building_entrance",
             "minecraft:empty", final_state="minecraft:cobblestone", joint="aligned")
    return p


VILLAGES = ("plains", "desert", "savanna", "snowy", "taiga")

PLACE = {
    "name": "village/armory_blacksmith",
    "pieces": {"village/armory_blacksmith": build},
    # appended to each vanilla village house pool with horizon:add_to
    "add_to": [f"minecraft:village/{v}/houses" for v in VILLAGES],
    "weight": 2,
}
