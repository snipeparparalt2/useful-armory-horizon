"""Shadow vault: a sealed deepslate vault (underground, Y -52 to -12). PLACEHOLDER
geometry from 0.2; rewrite to the brief in docs/design/places.md section 6.
"""
from structkit import AIR, NS, Piece  # noqa: F401


def build():
    p = Piece("shadow_vault", 9, 7, 9, "vault")
    brick = p.mix(("minecraft:deepslate_bricks", 6), ("minecraft:cracked_deepslate_bricks", 2),
                  (f"{NS}:deepslate_shadow_ore", 1))
    p.shell(0, 0, 0, 8, 6, 8, brick)
    p.fill(1, 0, 1, 7, 0, 7, "minecraft:deepslate_tiles")
    for x, z in ((1, 1), (7, 1), (1, 7), (7, 7)):
        p.fill(x, 1, z, x, 5, z, f"{NS}:shadowblock")
    p.fill(3, 1, 3, 5, 1, 5, "minecraft:polished_deepslate")
    p.set(4, 1, 4, "minecraft:deepslate_tiles")
    p.spawner(4, 2, 4, f"{NS}:vault_guardian")
    p.chest(4, 1, 1, "shadow_vault", "south")
    for x, z in ((2, 1, ), (6, 1), (1, 4), (7, 4)):
        p.set(x, 1, z, "minecraft:soul_lantern[hanging=false,waterlogged=false]")
    return p


PLACE = {
    "name": "shadow_vault",
    "pieces": {"shadow_vault": build},
    "step": "underground_structures",
    "start_height": (-52, -12),
    "surface": False,
    "terrain": "none",
    "biomes": [
        "#minecraft:is_overworld",
    ],
    "spacing": 22,
    "separation": 8,
    "salt": 418200106,
}
