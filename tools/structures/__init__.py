"""Every place (structure) the mod generates, one module each.

To add a place: write tools/structures/<name>.py with a PLACE dict (or a list of them) and add
it to the import and MODULES below. tools/gen_phase1.py reads PLACES.

PLACE keys (see tools/structures/crypt.py for a jigsaw example):
  name          structure id path (useful_armory:<name>) and file stem of its worldgen JSON
  pieces        {"<structure file path>": zero-argument builder returning a structkit.Piece}
                (path under data/useful_armory/structure/, no .nbt; Piece.name must match)
  step          generation step, e.g. surface_structures, underground_structures
  start_height  int (absolute), (lo, hi) uniform, or a raw height provider dict
  surface       True adds project_start_to_heightmap: WORLD_SURFACE_WG
  terrain       terrain_adaptation: none, beard_thin, beard_box, bury, encapsulate
  biomes        values of the biome tag has_structure/<name>
  spacing, separation, salt   random_spread placement
  size          jigsaw depth (default 1); max_distance  max_distance_from_center (default 80)
  start_pool    default "<name>/start"
  pools         {"<pool path>": [element, ...] or {"fallback": "<pool path>", "elements": [...]}};
                pool paths are under worldgen/template_pool/ in our namespace; a fallback may be
                a full id like minecraft:empty (the default). Omitted: one "<name>/start" pool
                holding every piece with weight 1.
                element: ("<piece>", weight) or a dict
                  {"piece": "<piece>", "weight": 1, "projection": "rigid",
                   "processors": "minecraft:empty",
                   "limit": N            -> lithostitched:limited (at most N per start)
                   "guaranteed": N       -> lithostitched:guaranteed (tried first until N)
                   "min_depth": D}       (for either wrapper; the parent piece's least depth)
                  {"empty": True, "weight": N} -> minecraft:empty_pool_element
  add_to        instead of a structure: vanilla pool ids to append the piece(s) to with
                horizon:add_to (with "weight", default 1); no structure, set or tag is written.
"""
from . import (aquite_shrine, armory_blacksmith, bandit_fort, colosifite_watchtower, crypt,
               forgotten_armory, infested_mine, miners_cache, pigman_outpost, ruined_forge,
               shadow_vault, wanderers_camp)

MODULES = [
    ruined_forge,
    wanderers_camp,
    aquite_shrine,
    colosifite_watchtower,
    pigman_outpost,
    shadow_vault,
    miners_cache,
    forgotten_armory,
    armory_blacksmith,
    bandit_fort,
    infested_mine,
    crypt,
]


def places():
    out = []
    for module in MODULES:
        place = module.PLACE
        out.extend(place if isinstance(place, list) else [place])
    return out


PLACES = places()
