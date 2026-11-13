#!/usr/bin/env python3
"""Preview sheets of the mod's structure pieces, for reviewing buildings.

    python3 -I tools/dev/render_nbt.py OUT.png [piece names or globs ...]
    python3 -I tools/dev/render_nbt.py --each DIR [piece names or globs ...]
    options: --layers 1,4,7   plan heights to draw (default: up to 4 spread over the piece)
             --width 1800     the most a piece's sheet may be wide

Pieces are read from content/data/useful_armory/structure/ (run tools/gen_phase1.py first)
and named by their path there without .nbt (crypt/room, village/armory_blacksmith); globs
like 'crypt/*' work. With no names every piece is drawn.

Each piece gets a sheet: an isometric view from the south-east, one from the north-west, a
cutaway from the south-east with the south half removed, and floor plans of a few layers
(north up, x to the right). In plans: white = cell not set (the world shows through),
grey = air the piece sets, faded colour = the block under an air cell. Marks: C loot
container, S spawner, J jigsaw (arrow = its front), D door, H ladder, triangles = stairs
(pointing the way up), thin lines = fences / walls / panes / bars.
"""
import argparse
import hashlib
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from structkit import AIR, DATA, HORIZONTAL, OPPOSITE, Piece, block_name, ccw, cw, match_any, parse_block  # noqa: E402

BG = (250, 250, 248)
INK = (30, 30, 34)

# ------------------------------------------------------------------ colours
COLOURS = {
    "stone": (125, 125, 125), "cobblestone": (118, 116, 114), "mossy_cobblestone": (96, 118, 88),
    "stone_bricks": (122, 122, 122), "cracked_stone_bricks": (104, 104, 108), "mossy_stone_bricks": (100, 122, 92),
    "chiseled_stone_bricks": (138, 138, 138), "smooth_stone": (158, 158, 158), "andesite": (136, 136, 134),
    "polished_andesite": (146, 148, 146), "diorite": (190, 190, 190), "granite": (150, 105, 85), "tuff": (108, 108, 98),
    "gravel": (132, 126, 122), "sand": (219, 207, 163), "sandstone": (216, 202, 155), "red_sand": (190, 102, 33),
    "dirt": (134, 96, 67), "coarse_dirt": (119, 85, 59), "dirt_path": (148, 122, 65), "grass_block": (98, 150, 60),
    "podzol": (92, 64, 30), "mud": (60, 57, 60), "clay": (160, 166, 180), "snow_block": (240, 248, 248),
    "bricks": (150, 75, 60), "mud_bricks": (137, 104, 79), "terracotta": (152, 94, 67),
    "deepslate": (80, 80, 84), "cobbled_deepslate": (74, 74, 78), "polished_deepslate": (86, 86, 90),
    "deepslate_bricks": (70, 70, 74), "cracked_deepslate_bricks": (60, 60, 64), "deepslate_tiles": (52, 52, 56),
    "cracked_deepslate_tiles": (46, 46, 50), "chiseled_deepslate": (66, 66, 70), "sculk": (12, 40, 52),
    "blackstone": (42, 36, 42), "polished_blackstone": (54, 49, 57), "polished_blackstone_bricks": (48, 42, 50),
    "gilded_blackstone": (90, 70, 40), "basalt": (80, 80, 86), "obsidian": (20, 16, 32), "crying_obsidian": (60, 20, 110),
    "netherrack": (110, 50, 50), "nether_bricks": (62, 28, 34), "cracked_nether_bricks": (50, 22, 28),
    "chiseled_nether_bricks": (72, 32, 38), "red_nether_bricks": (90, 14, 18), "magma_block": (160, 70, 24),
    "soul_sand": (82, 62, 50), "soul_soil": (76, 58, 46), "shroomlight": (240, 150, 70), "glowstone": (250, 210, 120),
    "prismarine": (95, 160, 150), "prismarine_bricks": (100, 172, 160), "dark_prismarine": (50, 95, 80),
    "sea_lantern": (210, 235, 230), "quartz_block": (232, 228, 220), "purpur_block": (170, 125, 170),
    "gold_block": (248, 212, 60), "iron_block": (220, 220, 220), "diamond_block": (100, 230, 225),
    "emerald_block": (40, 200, 90), "lapis_block": (30, 70, 160), "redstone_block": (170, 20, 10),
    "copper_block": (192, 107, 79), "coal_block": (20, 20, 20), "amethyst_block": (134, 98, 190),
    "coal_ore": (100, 100, 100), "iron_ore": (150, 130, 115), "deepslate_iron_ore": (100, 90, 85),
    "gold_ore": (160, 145, 90), "copper_ore": (130, 120, 100), "deepslate_coal_ore": (60, 60, 64),
    "water": (55, 100, 210), "lava": (230, 100, 20), "ice": (150, 185, 240), "packed_ice": (140, 170, 230),
    "glass": (196, 226, 236), "tinted_glass": (60, 50, 70), "iron_bars": (100, 104, 108),
    "cobweb": (236, 236, 240), "hay_block": (200, 170, 40), "bookshelf": (150, 110, 70), "chiseled_bookshelf": (140, 100, 60),
    "bone_block": (226, 222, 200), "moss_block": (90, 120, 50), "moss_carpet": (90, 120, 50),
    "vine": (60, 110, 30), "glow_lichen": (110, 140, 120), "melon": (110, 150, 40), "pumpkin": (200, 120, 30),
    "chest": (200, 140, 40), "trapped_chest": (200, 120, 40), "barrel": (140, 100, 58), "spawner": (36, 56, 84),
    "ladder": (165, 125, 72), "crafting_table": (140, 96, 56), "furnace": (100, 100, 100), "blast_furnace": (90, 90, 96),
    "smoker": (90, 80, 70), "smithing_table": (60, 60, 70), "anvil": (64, 64, 64), "chipped_anvil": (64, 64, 64),
    "damaged_anvil": (64, 64, 64), "grindstone": (130, 130, 130), "cauldron": (60, 60, 64), "water_cauldron": (55, 90, 190),
    "lectern": (160, 120, 70), "campfire": (240, 130, 30), "soul_campfire": (80, 210, 220), "lantern": (250, 200, 90),
    "soul_lantern": (90, 220, 230), "torch": (255, 210, 90), "wall_torch": (255, 210, 90), "soul_torch": (90, 220, 230),
    "soul_wall_torch": (90, 220, 230), "iron_chain": (70, 74, 82), "candle": (230, 220, 190), "skeleton_skull": (220, 220, 210),
    "rail": (150, 140, 120), "powered_rail": (190, 150, 60), "jigsaw": (160, 60, 190), "air": None, "cave_air": None,
    "flower_pot": (130, 70, 50), "decorated_pot": (150, 80, 60),
    # ours
    "aquiteore": (60, 220, 190), "deepslate_aquite_ore": (50, 180, 160), "colosifiteore": (205, 135, 60),
    "deepslate_colosifite_ore": (165, 105, 50), "shadowore": (110, 90, 220), "deepslate_shadow_ore": (100, 80, 200),
    "colosfiteblock": (240, 140, 25), "shadowblock": (40, 30, 80), "ultimateblock": (230, 60, 200),
}
DYE = {"white": (234, 236, 236), "orange": (240, 118, 20), "magenta": (190, 70, 180), "light_blue": (58, 175, 217),
       "yellow": (248, 198, 40), "lime": (112, 185, 26), "pink": (237, 141, 172), "gray": (62, 68, 72),
       "light_gray": (142, 142, 135), "cyan": (21, 137, 145), "purple": (122, 42, 173), "blue": (53, 57, 157),
       "brown": (114, 72, 41), "green": (85, 110, 28), "red": (161, 39, 35), "black": (21, 21, 26)}
WOOD = {"oak": ((168, 135, 82), (105, 82, 50)), "spruce": ((114, 84, 48), (58, 40, 22)),
        "birch": ((196, 178, 122), (216, 214, 206)), "jungle": ((160, 115, 80), (85, 68, 25)),
        "acacia": ((168, 90, 50), (103, 96, 86)), "dark_oak": ((66, 43, 20), (60, 46, 26)),
        "mangrove": ((117, 54, 48), (84, 67, 41)), "cherry": ((226, 178, 172), (54, 33, 44)),
        "pale_oak": ((228, 218, 214), (90, 84, 80)), "bamboo": ((194, 172, 80), (140, 140, 50)),
        "crimson": ((101, 48, 70), (92, 25, 29)), "warped": ((43, 104, 99), (58, 58, 77))}
SHAPE_SUFFIXES = ("_stairs", "_slab", "_wall", "_fence_gate", "_fence", "_pressure_plate", "_button")


def _hash(path):
    h = hashlib.md5(path.encode()).digest()
    return (80 + h[0] % 140, 80 + h[1] % 140, 80 + h[2] % 140)


def colour(block):
    path = block_name(block).split(":", 1)[-1]
    if path in COLOURS:
        return COLOURS[path]
    for dye in sorted(DYE, key=len, reverse=True):              # light_blue before blue
        if path.startswith(dye + "_"):
            rest = path[len(dye) + 1:]
            base = DYE[dye]
            if "glass" in rest:
                return tuple(int(c * 0.6 + 255 * 0.4) for c in base)
            if rest == "terracotta":
                return tuple(int(c * 0.7 + 90 * 0.3) for c in base)
            return base
    stripped = path.startswith("stripped_")
    core = path[9:] if stripped else path
    for wood in sorted(WOOD, key=len, reverse=True):              # dark_oak before oak
        if core.startswith(wood + "_"):
            planks, bark = WOOD[wood]
            rest = core[len(wood) + 1:]
            if rest in ("log", "wood", "stem", "hyphae") and not stripped:
                return bark
            if rest == "leaves":
                return (70, 120, 50) if wood != "cherry" else (230, 170, 200)
            return planks
    for suffix in SHAPE_SUFFIXES:                                # stone_brick_stairs -> stone_bricks
        if path.endswith(suffix):
            base = path[: -len(suffix)]
            for cand in (base, base + "s", base + "_block", base + "_planks"):
                if cand in COLOURS:
                    return COLOURS[cand]
            return colour("minecraft:" + base + "s") if not base.endswith("s") else _hash(base)
    if path.endswith("_ore"):
        return (140, 130, 120)
    if path.endswith("_carpet"):
        return COLOURS.get(path[:-7] + "_wool", _hash(path))
    if path.endswith("leaves"):
        return (70, 120, 50)
    if "copper" in path:
        return (170, 110, 80) if "oxidized" not in path else (80, 160, 130)
    return _hash(path)


# ------------------------------------------------------------------ block shapes (cell-local boxes)
def _half(d):
    return {"north": (0, 0, 0, 1, 1, .5), "south": (0, 0, .5, 1, 1, 1),
            "west": (0, 0, 0, .5, 1, 1), "east": (.5, 0, 0, 1, 1, 1)}[d]


def _isect(a, b):
    return tuple(max(a[i], b[i]) for i in range(3)) + tuple(min(a[i + 3], b[i + 3]) for i in range(3))


def _yband(box, y0, y1):
    return (box[0], y0, box[2], box[3], y1, box[5])


def _edge(d, t):
    """A plate of thickness t on the cell side d."""
    return {"north": (0, 0, 0, 1, 1, t), "south": (0, 0, 1 - t, 1, 1, 1),
            "west": (0, 0, 0, t, 1, 1), "east": (1 - t, 0, 0, 1, 1, 1)}[d]


def _arm(d, w, y0, y1):
    lo, hi = .5 - w / 2, .5 + w / 2
    return {"north": (lo, y0, 0, hi, y1, .5), "south": (lo, y0, .5, hi, y1, 1),
            "west": (0, y0, lo, .5, y1, hi), "east": (.5, y0, lo, 1, y1, hi)}[d]


def boxes(block):
    """The block's look as boxes (x0, y0, z0, x1, y1, z1) inside its cell."""
    name, props = parse_block(block)
    path = name.split(":", 1)[-1]
    full = [(0, 0, 0, 1, 1, 1)]
    if path.endswith("_slab"):
        t = props.get("type", "bottom")
        return full if t == "double" else [(0, .5, 0, 1, 1, 1)] if t == "top" else [(0, 0, 0, 1, .5, 1)]
    if path.endswith("_stairs"):
        f, top = props.get("facing", "north"), props.get("half") == "top"
        base = (0, .5, 0, 1, 1, 1) if top else (0, 0, 0, 1, .5, 1)
        y0, y1 = (0, .5) if top else (.5, 1)
        shape = props.get("shape", "straight")
        side = ccw(f) if shape.endswith("left") else cw(f)
        if shape.startswith("outer"):
            step = [_yband(_isect(_half(f), _half(side)), y0, y1)]
        elif shape.startswith("inner"):
            step = [_yband(_half(f), y0, y1), _yband(_isect(_half(OPPOSITE[f]), _half(side)), y0, y1)]
        else:
            step = [_yband(_half(f), y0, y1)]
        return [base] + step
    if path.endswith("_fence") or path.endswith("_wall") or path.endswith("_pane") or path.endswith("_bars"):
        wall = path.endswith("_wall")
        pane = path.endswith("_pane") or path.endswith("_bars")
        out = []
        if wall:
            if props.get("up", "true") == "true":
                out.append((.25, 0, .25, .75, 1, .75))
        elif not pane:
            out.append((.375, 0, .375, .625, 1, .625))
        else:
            out.append((.44, 0, .44, .56, 1, .56))
        for d in HORIZONTAL:
            v = props.get(d, "false")
            if v in ("false", "none"):
                continue
            if wall:
                out.append(_arm(d, .375, 0, 1 if v == "tall" else .8125))
            elif pane:
                out.append(_arm(d, .125, 0, 1))
            else:
                out.append(_arm(d, .125, .375, .9375))
        return out or [(.44, 0, .44, .56, 1, .56)]
    if path.endswith("_fence_gate"):
        f = props.get("facing", "north")
        return [_arm(cw(f), .125, .3, .95), _arm(ccw(f), .125, .3, .95)]
    if path.endswith("_trapdoor"):
        if props.get("open") == "true":
            return [_edge(OPPOSITE[props.get("facing", "north")], .1875)]
        return [(0, .8125, 0, 1, 1, 1)] if props.get("half") == "top" else [(0, 0, 0, 1, .1875, 1)]
    if path.endswith("_door"):
        f = props.get("facing", "north")
        if props.get("open") == "true":
            return [_edge(cw(f) if props.get("hinge") == "right" else ccw(f), .1875)]
        return [_edge(OPPOSITE[f], .1875)]
    if path == "ladder":
        return [_edge(OPPOSITE[props.get("facing", "north")], .125)]
    if path.endswith("wall_torch"):
        d = OPPOSITE[props.get("facing", "north")]
        e = _edge(d, .25)
        return [(max(e[0], .4) if d in ("north", "south") else e[0], .2,
                 max(e[2], .4) if d in ("east", "west") else e[2],
                 min(e[3], .6) if d in ("north", "south") else e[3], .8,
                 min(e[5], .6) if d in ("east", "west") else e[5])]
    if path.endswith("_carpet") or "rail" in path or path.endswith("pressure_plate") or path in ("snow",):
        return [(0, 0, 0, 1, .07, 1)]
    if path.endswith("_bed"):
        return [(0, 0, 0, 1, .5625, 1)]
    if path in ("chest", "trapped_chest", "ender_chest"):
        return [(.0625, 0, .0625, .9375, .875, .9375)]
    if path.endswith("lantern") and path != "sea_lantern" and path != "jack_o_lantern":
        return [(.3, .1, .3, .7, .6, .7)] if props.get("hanging") == "true" else [(.3, 0, .3, .7, .5, .7)]
    if path.endswith("candle"):
        n = int(props.get("candles", "1"))
        return [(.35, 0, .35, .65, .25 + .08 * n, .65)]
    if path.endswith("torch"):
        return [(.42, 0, .42, .58, .65, .58)]
    if path.endswith("chain"):
        return [(.44, 0, .44, .56, 1, .56)]
    if path.endswith("_skull") or path.endswith("_head"):
        return [(.25, 0, .25, .75, .5, .75)]
    if path.endswith("campfire"):
        return [(0, 0, 0, 1, .45, 1)]
    if path == "cobweb":
        return [(.2, .2, .2, .8, .8, .8)]
    if path in ("flower_pot",) or path.startswith("potted_"):
        return [(.3, 0, .3, .7, .4, .7)]
    if path in ("short_grass", "fern", "dead_bush", "vine", "glow_lichen") or path.endswith("_sapling") \
            or path.endswith("_tulip") or path in ("dandelion", "poppy", "cornflower", "azure_bluet", "oxeye_daisy",
                                                   "allium", "lily_of_the_valley", "brown_mushroom", "red_mushroom"):
        return [(.3, 0, .3, .7, .6, .7)]
    return full


# ------------------------------------------------------------------ isometric views
def _shade(c, k):
    return tuple(max(0, min(255, int(v * k))) for v in c)


def iso(piece, s, keep=None, label=""):
    W, H, D = piece.size
    pad = 6
    img = Image.new("RGB", ((W + D) * s + 2 * pad, (W + D) * s // 2 + H * s + 2 * pad + 14), BG)
    dr = ImageDraw.Draw(img)
    ox, oy = D * s + pad, H * s + pad + 14

    def pt(X, Y, Z):
        return (ox + (X - Z) * s, oy + (X + Z) * s / 2 - Y * s)

    # floor outline of the piece's box, so unset cells still show its extent
    corners = [pt(0, 0, 0), pt(W, 0, 0), pt(W, 0, D), pt(0, 0, D)]
    dr.polygon(corners, outline=(200, 200, 200))
    items = []
    for (x, y, z), (b, _) in piece.cells.items():
        if b == AIR or block_name(b) in ("minecraft:cave_air", "minecraft:structure_void"):
            continue
        if keep and not keep(x, y, z):
            continue
        c = colour(b)
        if c is None:
            continue
        for bx in boxes(b):
            cx, cy, cz = x + (bx[0] + bx[3]) / 2, y + (bx[1] + bx[4]) / 2, z + (bx[2] + bx[5]) / 2
            items.append((x + y + z, cx + cy + cz, (x, y, z), bx, c))
    items.sort(key=lambda i: (i[0], i[1]))
    edge = s >= 7
    for _, _, (x, y, z), bx, c in items:
        x0, y0, z0, x1, y1, z1 = x + bx[0], y + bx[1], z + bx[2], x + bx[3], y + bx[4], z + bx[5]
        top = [pt(x0, y1, z0), pt(x1, y1, z0), pt(x1, y1, z1), pt(x0, y1, z1)]
        south = [pt(x0, y0, z1), pt(x1, y0, z1), pt(x1, y1, z1), pt(x0, y1, z1)]
        east = [pt(x1, y0, z0), pt(x1, y0, z1), pt(x1, y1, z1), pt(x1, y1, z0)]
        line = _shade(c, .55) if edge else None
        dr.polygon(south, fill=_shade(c, .78), outline=line)
        dr.polygon(east, fill=_shade(c, .6), outline=line)
        dr.polygon(top, fill=c, outline=line)
    dr.text((pad, 2), label, fill=INK, font=_font(11))
    return img


# ------------------------------------------------------------------ floor plans
_FONTS = {}


def _font(size):
    if size not in _FONTS:
        try:
            _FONTS[size] = ImageFont.load_default(size=size)
        except TypeError:
            _FONTS[size] = ImageFont.load_default()
    return _FONTS[size]


def _blend(c, k, to=(255, 255, 255)):
    return tuple(int(a * k + b * (1 - k)) for a, b in zip(c, to))


def plan(piece, y, p):
    W, H, D = piece.size
    left, topm = 22, 30
    img = Image.new("RGB", (left + W * p + 8, topm + D * p + 8), BG)
    dr = ImageDraw.Draw(img)
    dr.text((left, 2), f"y = {y}  (north up)", fill=INK, font=_font(12))
    for x in range(0, W, 5):
        dr.text((left + x * p + 1, 16), str(x), fill=(110, 110, 110), font=_font(9))
    for z in range(0, D, 5):
        dr.text((2, topm + z * p), str(z), fill=(110, 110, 110), font=_font(9))
    f = _font(max(8, int(p * 0.8)))
    for z in range(D):
        for x in range(W):
            X, Z = left + x * p, topm + z * p
            box = [X, Z, X + p - 1, Z + p - 1]
            b = piece.get(x, y, z)
            below = piece.get(x, y - 1, z)
            if b is None:
                dr.rectangle(box, fill=(255, 255, 255))
                if p >= 6:
                    dr.point((X + p // 2, Z + p // 2), fill=(215, 215, 215))
                continue
            path = block_name(b).split(":", 1)[-1]
            under = (226, 226, 226)
            if below not in (None, AIR) and colour(below):
                under = _blend(colour(below), .35, (226, 226, 226))
            c = colour(b)
            if b == AIR or c is None:
                dr.rectangle(box, fill=under)
                continue
            props = parse_block(b)[1]
            thin = any(path.endswith(sfx) for sfx in ("_fence", "_wall", "_pane", "_bars"))
            if thin:
                dr.rectangle(box, fill=under)
                cxm, czm = X + p / 2, Z + p / 2
                w = max(1, p // 5)
                dr.rectangle([cxm - w, czm - w, cxm + w, czm + w], fill=c)
                for d in HORIZONTAL:
                    if props.get(d, "false") not in ("false", "none"):
                        ex = {"east": X + p, "west": X, "north": cxm, "south": cxm}[d]
                        ez = {"north": Z, "south": Z + p, "east": czm, "west": czm}[d]
                        dr.line([cxm, czm, ex, ez], fill=c, width=max(1, p // 6))
                continue
            small = path.endswith("_carpet") or "rail" in path or path.endswith("_trapdoor") and props.get("open") != "true"
            dr.rectangle(box, fill=_blend(c, .75, under) if small else c)
            nbt = piece.get_nbt(x, y, z) or {}
            mark, mc = None, (255, 255, 255)
            if "LootTable" in nbt:
                mark, mc = "C", (255, 230, 60)
            elif nbt.get("id") == "minecraft:mob_spawner":
                mark, mc = "S", (255, 80, 80)
            elif path == "jigsaw":
                front = props.get("orientation", "north_up").split("_")[0]
                _arrow(dr, X, Z, p, front, (255, 255, 255))
            elif path.endswith("_door"):
                mark = "D"
            elif path == "ladder":
                mark = "H"
            elif path.endswith("_stairs"):
                _arrow(dr, X, Z, p, props.get("facing", "north"), _shade(c, .45) if sum(c) > 300 else _blend(c, .4))
            elif path.endswith("_bed"):
                mark = "b"
            if mark and p >= 7:
                dr.text((X + p / 2, Z + p / 2), mark, fill=mc, font=f, anchor="mm",
                        stroke_width=1, stroke_fill=(0, 0, 0))
    if p >= 5:
        grid = (0, 0, 0)
        for x in range(0, W + 1):
            col = _blend(grid, .25 if x % 5 == 0 else .07, BG)
            dr.line([left + x * p, topm, left + x * p, topm + D * p], fill=col)
        for z in range(0, D + 1):
            col = _blend(grid, .25 if z % 5 == 0 else .07, BG)
            dr.line([left, topm + z * p, left + W * p, topm + z * p], fill=col)
    return img


def _arrow(dr, X, Z, p, d, fill):
    if p < 5 or d not in HORIZONTAL:
        return
    c, r = (X + p / 2, Z + p / 2), p * .38
    tip = {"north": (0, -1), "south": (0, 1), "east": (1, 0), "west": (-1, 0)}[d]
    side = (-tip[1], tip[0])
    pts = [(c[0] + tip[0] * r, c[1] + tip[1] * r),
           (c[0] - tip[0] * r + side[0] * r, c[1] - tip[1] * r + side[1] * r),
           (c[0] - tip[0] * r - side[0] * r, c[1] - tip[1] * r - side[1] * r)]
    dr.polygon(pts, fill=fill)


def default_layers(piece, n=4):
    H = piece.size[1]
    inner = list(range(1, H - 1)) or list(range(H))
    if len(inner) <= n:
        return inner
    return sorted({inner[round(i * (len(inner) - 1) / (n - 1))] for i in range(n)})


# ------------------------------------------------------------------ the sheet
def legend(piece, width):
    counts = {}
    for b, _ in piece.cells.values():
        if b == AIR:
            continue
        n = block_name(b).split(":", 1)[-1]
        counts[n] = counts.get(n, 0) + 1
    names = sorted(counts, key=lambda n: (-counts[n], n))[:40]
    cell_w, row_h = 190, 14
    per_row = max(1, (width - 10) // cell_w)
    rows = (len(names) + per_row - 1) // per_row
    img = Image.new("RGB", (width, rows * row_h + 6), BG)
    dr = ImageDraw.Draw(img)
    for i, n in enumerate(names):
        X, Y = 6 + (i % per_row) * cell_w, 3 + (i // per_row) * row_h
        c = colour("minecraft:" + n) or (255, 255, 255)
        dr.rectangle([X, Y + 1, X + 10, Y + 11], fill=c, outline=(80, 80, 80))
        dr.text((X + 14, Y), f"{n} {counts[n]}", fill=INK, font=_font(10))
    return img


def sheet(piece, max_width=1800, layers=None):
    piece.finalize()
    W, H, D = piece.size
    s = max(3, min(16, (max_width - 40) // (3 * (W + D))))
    st = piece.stats()
    cut = (D - 1) // 2
    views = [iso(piece, s, label="from south-east"),
             iso(piece.rotated(2), s, label="from north-west"),
             iso(piece, s, keep=lambda x, y, z: z <= cut, label=f"cut: z > {cut} removed")]
    layers = [y for y in (layers or default_layers(piece)) if 0 <= y < H]
    p = max(3, min(20, (max_width - 40) // max(1, len(layers) * (W + 2)), 600 // max(D, 1)))
    plans = [plan(piece, y, p) for y in layers]
    row1_w = sum(v.width for v in views) + 10 * (len(views) - 1)
    row2_w = sum(v.width for v in plans) + 10 * max(0, len(plans) - 1)
    width = max(row1_w, row2_w, 600)
    head = 36
    leg = legend(piece, width)
    height = head + max(v.height for v in views) + 8 + (max(v.height for v in plans) if plans else 0) + 6 + leg.height
    img = Image.new("RGB", (width, height), BG)
    dr = ImageDraw.Draw(img)
    dr.text((6, 3), piece.name, fill=INK, font=_font(16))
    info = (f"{W} x {H} x {D}   blocks {st['blocks']} (+{st['cells'] - st['blocks']} air)   "
            f"loot {st['loot'] or '-'}   spawners {st['spawners'] or '-'}   jigsaws {st['jigsaws']}")
    dr.text((6, 21), info, fill=(70, 70, 70), font=_font(11))
    X, Y = 0, head
    for v in views:
        img.paste(v, (X, Y))
        X += v.width + 10
    Y += max(v.height for v in views) + 8
    X = 0
    for v in plans:
        img.paste(v, (X, Y))
        X += v.width + 10
    Y += (max(v.height for v in plans) if plans else 0) + 6
    img.paste(leg, (0, Y))
    dr.line([0, height - 1, width, height - 1], fill=(160, 160, 160))
    return img


def pieces(patterns):
    root = DATA / "structure"
    found = []
    for path in sorted(root.rglob("*.nbt")):
        name = path.relative_to(root).with_suffix("").as_posix()
        if match_any(name, patterns):
            found.append(Piece.load(path, name))
    return found


def main():
    ap = argparse.ArgumentParser(description="Preview sheets of structure pieces.")
    ap.add_argument("args", nargs="*", help="OUT.png, then piece names or globs")
    ap.add_argument("--each", metavar="DIR", help="also write one PNG per piece into DIR")
    ap.add_argument("--layers", help="comma-separated plan heights, e.g. 1,5,9")
    ap.add_argument("--width", type=int, default=1800, help="most width of one piece's sheet")
    a = ap.parse_args()
    out, patterns = None, list(a.args)
    if patterns and patterns[0].lower().endswith(".png"):
        out = patterns.pop(0)
    if not out and not a.each:
        ap.error("give OUT.png and/or --each DIR")
    layers = [int(v) for v in a.layers.split(",")] if a.layers else None
    found = pieces(patterns)
    if not found:
        sys.exit(f"no pieces match {patterns}")
    sheets = []
    for piece in found:
        st = piece.stats()
        print(f"{st['name']}: size {st['size']}, {st['blocks']} blocks + {st['cells'] - st['blocks']} air, "
              f"loot {st['loot']}, spawners {st['spawners']}, jigsaws {st['jigsaws']}")
        img = sheet(piece, a.width, layers)
        sheets.append(img)
        if a.each:
            d = Path(a.each)
            d.mkdir(parents=True, exist_ok=True)
            img.save(d / (piece.name.replace("/", "__") + ".png"))
    if out:
        full = Image.new("RGB", (max(i.width for i in sheets), sum(i.height for i in sheets)), BG)
        y = 0
        for i in sheets:
            full.paste(i, (0, y))
            y += i.height
        full.save(out)
        print(f"wrote {out} ({full.width} x {full.height})")


if __name__ == "__main__":
    main()
