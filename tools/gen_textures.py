#!/usr/bin/env python3
"""Useful Armory texture generator.

Usage:  python3 gen_textures.py <path-to>/assets/useful_armory/textures [--std-armor] [--halo]

--std-armor writes the worn armour at the vanilla 64x32 size instead of 128x64.
--halo      paints the old soft coloured halo around glowing sprites. Off by default: the
            glow is real coloured light now, cast in game by Useful Armory's native half
            (native/useful_armory), so the icons stay clean. GLOW_ITEMS below is what that mod lights.

Every sprite is drawn from a shape template (below) and shaded with a
per-material colour ramp, so changing a palette in MATERIALS and re-running
restyles a whole equipment set at once. File names match the ones the
existing models already point at, so nothing else in the mod has to change.
"""
import colorsys
import math
import os
import random
import sys

from PIL import Image


def hx(h):
    h = h.lstrip('#')
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 255)


def mix(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3)) + (255,)


# ---------------------------------------------------------------- palettes
# ramp: 0 outline, 1 deep shadow, 2 shadow, 3 base, 4 light, 5 highlight
WOOD = [hx(c) for c in ('2a1a0c', '4e3418', '79552a', 'a47b42')]       # outline, dark, mid, light
BLAZE = [hx(c) for c in ('5a2a04', 'a85a08', 'e8a416', 'ffe25a')]
DARKWOOD = [hx(c) for c in ('07060c', '17141f', '2a2535', '423a52')]
GOLD = [hx(c) for c in ('5a3606', 'b47a12', 'f0c12c', 'fff59a')]
STEEL = [hx(c) for c in ('1c2028', '4a5260', '8c96a4', 'd8dee6')]
IRONDARK = [hx(c) for c in ('121216', '2e2f38', '50525f', '82859a')]
VIOLET = [hx(c) for c in ('1c0a3a', '4a1f9a', '8a4df0', 'd9b8ff')]
NETHER = [hx(c) for c in ('2a0a0a', '5a1414', '8f2a22', 'c85a48')]

MATERIALS = {
    'aquite': dict(
        ramp=['08303a', '0e5f62', '14a08e', '22d4ae', '74f2d0', 'dafff4'],
        handle=WOOD, accent=STEEL, speckle=0.0),
    'colosifite': dict(
        ramp=['47180a', '8c3207', 'c85a0b', 'f28c18', 'ffba42', 'ffeaa6'],
        handle=WOOD, accent=IRONDARK, speckle=0.0),
    'emerald': dict(
        ramp=['052e1b', '0a6a33', '169f49', '33cb66', '80ec98', 'dcffe2'],
        handle=WOOD, accent=GOLD, speckle=0.0),
    'lapis': dict(
        ramp=['0b1748', '153083', '234db6', '3d70da', '7aa2f0', 'd0e0ff'],
        handle=WOOD, accent=GOLD, speckle=0.22),
    'obsidian': dict(
        ramp=['08050f', '181026', '291d40', '3e2e5c', '62508a', 'a896cf'],
        handle=BLAZE, accent=GOLD, speckle=0.0),
    'quartz': dict(
        ramp=['66544f', 'a08f8a', 'c8bbb3', 'e4dcd4', 'f5f0ea', 'ffffff'],
        handle=WOOD, accent=NETHER, speckle=0.0),
    'redstone': dict(
        ramp=['2a0303', '680707', 'a60f0f', 'da281a', 'ff5a3a', 'ffb690'],
        handle=WOOD, accent=IRONDARK, speckle=0.18),
    'shadow': dict(
        ramp=['020207', '0b0b15', '161728', '24263f', '3c3f63', '8d7be0'],
        handle=DARKWOOD, accent=VIOLET, speckle=0.0),
    # extra ramps used only for a few borrowed-shape items
    'iron': dict(
        ramp=['24262c', '5a5e68', '8f949e', 'bcc1c9', 'e0e3e8', 'ffffff'],
        handle=WOOD, accent=IRONDARK, speckle=0.0),
    'diamond': dict(
        ramp=['0a3a40', '13777a', '27b3ad', '4ae0d2', '9ff5ea', 'e8fffb'],
        handle=WOOD, accent=GOLD, speckle=0.0),
}
for m in MATERIALS.values():
    m['ramp'] = [hx(c) for c in m['ramp']]


# ---------------------------------------------------------------- canvas
class Sprite:
    """Grid of (group, shade) cells. group: 'm' material, 'h' handle, 'x' accent."""

    def __init__(self, n):
        self.n = n
        self.g = [[None] * n for _ in range(n)]

    @classmethod
    def from_ascii(cls, rows):
        n = len(rows)
        s = cls(n)
        for y, row in enumerate(rows):
            assert len(row) == n, (y, row, len(row))
            for x, ch in enumerate(row):
                s.put(x, y, ch)
        return s

    def put(self, x, y, ch):
        if not (0 <= x < self.n and 0 <= y < self.n) or ch in '. ':
            return
        if ch in '012345':
            self.g[y][x] = ('m', int(ch))
        elif ch in 'abc':
            self.g[y][x] = ('h', 'abc'.index(ch) + 1)
        elif ch == 'A':
            self.g[y][x] = ('h', 0)
        elif ch in 'xyz':
            self.g[y][x] = ('x', 'xyz'.index(ch) + 1)
        else:
            raise ValueError(ch)

    def render(self, mat, seed='', outline=True, fx=None):
        n = self.n
        m = MATERIALS[mat]
        ramp, handle, accent = m['ramp'], m['handle'], m['accent']
        rnd = random.Random(f'{mat}/{seed}')
        img = Image.new('RGBA', (n, n), (0, 0, 0, 0))
        px = img.load()

        def col(cell):
            grp, sh = cell
            if grp == 'm':
                return ramp[sh]
            return (handle if grp == 'h' else accent)[sh]

        for y in range(n):
            for x in range(n):
                c = self.g[y][x]
                if c is None:
                    continue
                grp, sh = c
                if grp == 'm' and m['speckle'] and 2 <= sh <= 4 and rnd.random() < m['speckle']:
                    sh = sh + rnd.choice((-1, 1))
                    c = (grp, sh)
                colr = col(c)
                if fx:
                    colr = fx(x, y, c, colr, m)
                px[x, y] = colr
        if not outline:
            return img
        # auto outline: darker on the shaded (bottom/right) side, softer on the lit side
        for y in range(n):
            for x in range(n):
                if self.g[y][x] is not None:
                    continue
                best = None
                for dx, dy, lit in ((1, 0, True), (0, 1, True), (-1, 0, False), (0, -1, False)):
                    xx, yy = x + dx, y + dy
                    if 0 <= xx < n and 0 <= yy < n and self.g[yy][xx] is not None:
                        grp = self.g[yy][xx][0]
                        if grp == 'm':
                            o = mix(ramp[0], ramp[1], 0.25) if lit else ramp[0]
                        elif grp == 'h':
                            o = mix(handle[0], handle[1], 0.35) if lit else handle[0]
                        else:
                            o = mix(accent[0], accent[1], 0.35) if lit else accent[0]
                        if best is None or sum(o[:3]) < sum(best[:3]):
                            best = o
                if best is not None:
                    px[x, y] = best
        return img


def diag(n, x, y):
    """along (0 = bottom-left corner), across (negative = upper-left side)."""
    yy = n - 1 - y
    return x + yy, x - yy


# ---------------------------------------------------------------- helpers
WHITE = (255, 255, 255, 255)


def strip(frames):
    w, h = frames[0].size
    img = Image.new('RGBA', (w, h * len(frames)), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        img.paste(f, (0, i * h))
    return img


# ---------------------------------------------------------------- 16px templates
T = {}

T['sword'] = [
    '................',
    '..............5.',
    '............542.',
    '...........5432.',
    '..........5432..',
    '.........5432...',
    '........5432....',
    '...z...5432.....',
    '...xy.5432......',
    '....xy432.......',
    '.....xzy........',
    '....cbxyy.......',
    '...cba..xy......',
    '..cba...........',
    '.xy.............',
    '................',
]

T['dagger'] = [
    '................',
    '................',
    '.............5..',
    '...........542..',
    '..........5432..',
    '.........5432...',
    '........5432....',
    '.....z.5432.....',
    '.....xy432......',
    '......xzy.......',
    '.....cbxy.......',
    '....cba.........',
    '...cba..........',
    '..xy............',
    '................',
    '................',
]

T['pickaxe'] = [
    '................',
    '......55554.....',
    '....45443344....',
    '...43.....4432..',
    '...3......cb32..',
    '.........cba432.',
    '........cba.432.',
    '.......cba..432.',
    '......cba...332.',
    '.....cba....32..',
    '....cba.....32..',
    '...cba......2...',
    '..cba...........',
    '.cba............',
    '................',
    '................',
]

T['axe'] = [
    '................',
    '.......4554.....',
    '.....554433cb...',
    '....5544332cb21.',
    '....544332cba21.',
    '....54332cba....',
    '.....432cba.....',
    '......2cba......',
    '......cba.......',
    '.....cba........',
    '....cba.........',
    '...cba..........',
    '..cba...........',
    '.cba............',
    '................',
    '................',
]

T['shovel'] = [
    '................',
    '...........555..',
    '..........55443.',
    '.........554432.',
    '.........54432..',
    '.........4432...',
    '........cb32....',
    '.......cba......',
    '......cba.......',
    '.....cba........',
    '....cba.........',
    '...cba..........',
    '..cba...........',
    '.xy.............',
    '................',
    '................',
]

T['hoe'] = [
    '................',
    '......455543....',
    '.....4433322cb..',
    '....43....cba...',
    '....3....cba....',
    '........cba.....',
    '.......cba......',
    '......cba.......',
    '.....cba........',
    '....cba.........',
    '...cba..........',
    '..cba...........',
    '.cba............',
    '................',
    '................',
    '................',
]

T['helmet'] = [
    '................',
    '.....455544.....',
    '...4555544433...',
    '..455554444333..',
    '.45555444443332.',
    '.45554444443332.',
    '.4554444yz43322.',
    '.4544444xy33322.',
    '.xyyyyyzzyyyyyx.',
    '.4543..43..3221.',
    '.454...32...221.',
    '.443........221.',
    '.432........211.',
    '..32........21..',
    '................',
    '................',
]

T['chestplate'] = [
    '................',
    '..554......443..',
    '.55544....44332.',
    '.55544333344332.',
    '.55444444443332.',
    '.54435444433322.',
    '.43.54444433.21.',
    '....544yz433....',
    '....544xy333....',
    '....54444332....',
    '....54443332....',
    '....44433322....',
    '...xyyyyyyyyx...',
    '...4333222221...',
    '................',
    '................',
]

T['leggings'] = [
    '................',
    '..555444444333..',
    '..xyyyyzzyyyyx..',
    '..554444443332..',
    '..554444443332..',
    '..554444443332..',
    '..55443..43332..',
    '..55443..43332..',
    '..54443..43322..',
    '..yzzyx..yzyyx..',
    '..54433..43322..',
    '..54433..43322..',
    '..44333..33222..',
    '..44332..33221..',
    '..33222..22211..',
    '................',
]

T['boots'] = [
    '................',
    '................',
    '................',
    '..55444..44333..',
    '..55443..44332..',
    '..55443..44332..',
    '..54443..43332..',
    '..yzyyx..yzyyx..',
    '..54433..43322..',
    '..54433..43322..',
    '.554433..433222.',
    '.544333..333222.',
    '.222211..222111.',
    '................',
    '................',
    '................',
]

T['ingot'] = [
    '................',
    '................',
    '................',
    '................',
    '......55555554..',
    '.....545444432..',
    '....5454444322..',
    '...55555554222..',
    '...43333333221..',
    '...4333333321...',
    '...433333332....',
    '...22222222.....',
    '................',
    '................',
    '................',
    '................',
]

T['stick'] = [
    '................',
    '................',
    '............54..',
    '...........543..',
    '..........543...',
    '.........543....',
    '........543.....',
    '.......543......',
    '......543.......',
    '.....543........',
    '....543.........',
    '...543..........',
    '..543...........',
    '..43............',
    '................',
    '................',
]

T['string'] = [
    '................',
    '................',
    '.....4555.......',
    '...44....54.....',
    '..4........5....',
    '..4.........4...',
    '..3....44...4...',
    '...33.4..4.4....',
    '.....3....4.....',
    '....4.3..4.33...',
    '...4...33....3..',
    '...4..........3.',
    '....3.........3.',
    '.....33.........',
    '................',
    '................',
]


# ---------------------------------------------------------------- 32px programmatic weapons
def _handle(s, top, wrap_to=9):
    """Shared 16px haft: accent pommel, wrapped grip, plain shaft up to `top`."""
    n = s.n
    for y in range(n):
        for x in range(n):
            a, c = diag(n, x, y)
            if 2 <= a <= 4 and abs(c) <= 1:
                s.put(x, y, 'z' if c < 0 else ('y' if c == 0 else 'x'))
            elif 5 <= a <= top and abs(c) <= 1:
                ch = 'c' if c < 0 else ('b' if c == 0 else 'a')
                if a <= wrap_to and a % 3 == 0:
                    ch = 'b' if c < 0 else 'a'
                s.put(x, y, ch)


def _collar(s, a_lo, a_hi, half=1):
    n = s.n
    for y in range(n):
        for x in range(n):
            a, c = diag(n, x, y)
            if a_lo <= a <= a_hi and abs(c) <= half:
                s.put(x, y, 'z' if c < 0 else ('y' if c == 0 else 'x'))


def pickaxe16():
    n = 16
    s = Sprite(n)
    _handle(s, 23)
    _collar(s, 20, 21, half=2)
    for y in range(n):
        for x in range(n):
            a, c = diag(n, x, y)
            k = abs(c)
            if k > 9:
                continue
            hi = min(27.5 - 0.115 * c * c, 28 - k)
            th = 4.6 if k <= 3 else (3.6 if k <= 7 else 2.4)
            if hi - th < a <= hi:
                outer = a > hi - 2.0
                if c < -1:
                    sh = 5 if outer else 4
                elif c <= 1:
                    sh = 4 if outer else 3
                else:
                    sh = 3 if outer else 2
                if k >= 8:
                    sh = 3 if c < 0 else 1
                s.put(x, y, str(sh))
    return s


def axe16():
    n = 16
    s = Sprite(n)
    _handle(s, 23)
    _collar(s, 16, 17, half=1)
    for y in range(n):
        for x in range(n):
            a, c = diag(n, x, y)
            ch = None
            if 19 <= a <= 23 and abs(c) <= 1:                      # eye
                ch = '3' if c < 0 else '2'
            lo, hi = {-2: (19, 23), -3: (18, 23), -4: (17, 24), -5: (15, 23),
                      -6: (14, 22), -7: (13, 21), -8: (14, 20)}.get(c, (1, 0))
            if lo <= a <= hi:                                      # bearded blade
                sh = {-2: 2, -3: 3, -4: 3, -5: 4, -6: 4, -7: 5, -8: 5}[c]
                if a <= 15:
                    sh -= 1
                if a >= hi - 1 and c <= -4:
                    sh = min(5, sh + 1)
                ch = str(sh)
            if 19 <= a <= 23 and c in (2, 3) and not (c == 3 and a in (19, 23)):   # poll
                ch = '2' if c == 2 else '1'
            if ch:
                s.put(x, y, ch)
    return s


def shovel16():
    n = 16
    s = Sprite(n)
    _handle(s, 19)
    _collar(s, 17, 18, half=1)
    width = {19: 1, 20: 2, 21: 3, 22: 3, 23: 3, 24: 3, 25: 3, 26: 2, 27: 1}
    for y in range(n):
        for x in range(n):
            a, c = diag(n, x, y)
            w = width.get(a)
            if w is not None and abs(c) <= w:
                sh = 5 if c <= -2 else (4 if c == -1 else (3 if c <= 1 else 2))
                if c == 0 and 21 <= a <= 25:
                    sh = 4                                          # centre ridge
                if a <= 20:
                    sh = max(2, sh - 1)
                if abs(c) == w and c > 0:
                    sh = 2
                s.put(x, y, str(sh))
    return s


def hoe16():
    n = 16
    s = Sprite(n)
    _handle(s, 24)
    rows = {1: (5, 12, '55554443'), 2: (4, 13, '5443333221'), 3: (4, 6, '543'),
            4: (4, 5, '43'), 5: (4, 5, '32'), 6: (5, 5, '2')}
    for y, (x0, x1, shades) in rows.items():
        for i, x in enumerate(range(x0, x1 + 1)):
            s.put(x, y, shades[i])
    _collar(s, 21, 22, half=1)
    return s


def greatsword():
    """Long two-hander: slim fullered blade, modest cross-guard, long wrapped grip."""
    n = 32
    s = Sprite(n)
    for y in range(n):
        for x in range(n):
            a, c = diag(n, x, y)
            ch = None
            if 3 <= a <= 5 and abs(c) <= 1:                                            # pommel
                ch = 'z' if c < 0 else ('y' if c == 0 else 'x')
            elif 6 <= a <= 14 and abs(c) <= 1:                                         # grip
                ch = 'a' if (a % 3 == 0) else ('c' if c < 0 else ('b' if c == 0 else 'a'))
            elif a in (15, 16) and abs(c) <= 7:                                        # guard
                ch = 'x' if a == 15 else ('z' if c < -1 else 'y')
            elif a == 17 and abs(c) in (6, 7):                                         # upturned tips
                ch = 'z' if c < 0 else 'x'
            if 17 <= a <= 60:                                                          # blade
                w = 2 if a <= 51 else (1 if a <= 56 else 0)
                if abs(c) <= w:
                    ch = {-2: '5', -1: '4', 0: '3', 1: '3', 2: '2'}[c]
                    if c == 0 and a <= 44:
                        ch = '2'                                                       # fuller
                    if w < 2:
                        ch = '5' if c <= 0 else '3'
                    if a <= 18:
                        ch = '2'
            if ch:
                s.put(x, y, ch)
    return s


def halberd():
    n = 32
    s = Sprite(n)
    for y in range(n):
        for x in range(n):
            a, c = diag(n, x, y)
            ch = None
            if 4 <= a <= 50 and c in (0, 1):                                           # shaft
                ch = 'c' if c == 0 else 'a'
                if c == 0 and a % 5 == 0:
                    ch = 'b'
            if 2 <= a <= 4 and abs(c) <= 1:                                            # butt cap
                ch = 'y' if c <= 0 else 'x'
            # axe blade, upper-left side: narrow neck flaring to a crescent edge
            if c <= -2:
                k = -c
                half = 2.5 + 0.085 * (k - 2) ** 2
                edge = 11 - 0.05 * (a - 43) ** 2
                if abs(a - 43) <= half and k <= edge:
                    d = edge - k
                    ch = '5' if d < 1.5 else ('4' if d < 3.2 else '3')
                    if k <= 3:
                        ch = '2'
                    elif a < 41 and ch != '5':
                        ch = str(int(ch) - 1)
            # back spike, lower-right side
            if 40 <= a <= 46:
                w = 6 - 2 * abs(a - 43)
                if 2 <= c <= 2 + w:
                    ch = '3' if a <= 43 else '2'
            # collars
            if a in (33, 34, 52) and abs(c) <= 2:
                ch = 'z' if c < 0 else ('y' if c == 0 else 'x')
            if 39 <= a <= 47 and c in (-1, 0, 1) and abs(c) + 0 <= 1:                  # socket
                ch = '3' if c < 0 else ('2' if c == 0 else '1')
            # spear tip
            if 53 <= a <= 60:
                w = 2 if a <= 55 else (1 if a <= 58 else 0)
                if abs(c) <= w:
                    ch = '5' if c < 0 or w == 0 else ('4' if c == 0 else '2')
            if ch:
                s.put(x, y, ch)
    return s


def long_stick():
    n = 32
    s = Sprite(n)
    for y in range(n):
        for x in range(n):
            a, c = diag(n, x, y)
            if 5 <= a <= 57 and c in (0, 1):
                ch = 'c' if c == 0 else 'a'
                if c == 0 and a % 7 in (0, 1):
                    ch = 'b'
                s.put(x, y, ch)
    return s


# ---------------------------------------------------------------- blocks
STONE = [hx(c) for c in ('686868', '747474', '7f7f7f', '8a8a8a', '949494')]
STONE_SHADOW = hx('585858')


def stone_base(seed):
    """Tileable stone: a flat mid grey broken up by short horizontal strokes."""
    rnd = random.Random(seed)
    n = 16
    g = [[2] * n for _ in range(n)]
    for _ in range(46):
        x, y = rnd.randrange(n), rnd.randrange(n)
        tone = rnd.choice((1, 1, 1, 3, 3, 3, 0, 4))
        for i in range(rnd.choice((2, 3, 3, 4, 5))):
            g[y][(x + i) % n] = tone
    img = Image.new('RGBA', (n, n))
    px = img.load()
    for y in range(n):
        for x in range(n):
            px[x, y] = STONE[g[y][x]]
    return img


ORE_LAYOUTS = {
    'shards': [
        '................',
        '..55........4...',
        '.5432......543..',
        '..32........2...',
        '......54........',
        '.....5432...55..',
        '......32...5432.',
        '.45.........32..',
        '4432..54........',
        '.22..5432.......',
        '......32....45..',
        '...........4432.',
        '..54........22..',
        '.5432...45......',
        '..32...4432.....',
        '........22......',
    ],
    'nuggets': [
        '................',
        '.445........44..',
        '.5432......5432.',
        '..322......3322.',
        '......544.......',
        '.....54332......',
        '......3322......',
        '.44..........54.',
        '5432........5432',
        '3322....44...322',
        '.22....5432.....',
        '.......3322.....',
        '..445...22......',
        '..5432.......44.',
        '...322......5432',
        '.............322',
    ],
    'voids': [
        '................',
        '.33.........23..',
        '3212.......2112.',
        '.215........21..',
        '......232.......',
        '.....32112......',
        '......2152......',
        '.23..........32.',
        '2112........3211',
        '.251....33...212',
        '.......3212.....',
        '........251.....',
        '..332...........',
        '..2112.......23.',
        '...215......2112',
        '.............251',
    ],
}


def ore(mat, layout, seed):
    """The mineral only, on a transparent background.

    The ore block models draw the game's own stone texture underneath
    (`minecraft:block/stone`), so the rock always matches the player's stone, resource
    packs included, and no vanilla pixels are shipped in the mod.
    """
    img = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
    px = img.load()
    ramp = MATERIALS[mat]['ramp']
    rows = ORE_LAYOUTS[layout]
    n = 16
    filled = [[rows[y][x] != '.' for x in range(n)] for y in range(n)]
    for y in range(n):
        for x in range(n):
            if filled[y][x]:
                px[x, y] = ramp[int(rows[y][x])]
            elif filled[(y - 1) % n][x] or filled[y][(x - 1) % n]:
                px[x, y] = STONE_SHADOW          # the ore sits in a pocket: shadow below/right
    return img


def metal_block(mat, seed, style='plates'):
    """Storage block: 1px bevel (lit top/left, shaded bottom/right) around a simple field."""
    ramp = MATERIALS[mat]['ramp']
    acc = MATERIALS[mat]['accent']
    rnd = random.Random(f'{mat}/{seed}')
    n = 16
    g = [[3] * n for _ in range(n)]
    for y in range(n):
        for x in range(n):
            ring = min(x, y, n - 1 - x, n - 1 - y)
            tl = x + y < n - 1
            if style == 'void':
                base = (2, 1, 3, 0)        # field, shaded field, lit rim, dark rim
            else:
                base = (3, 2, 5, 1)
            if ring == 0:
                sh = base[2] if tl else base[3]
                if (x, y) in ((n - 1, 0), (0, n - 1)):
                    sh = base[0]
            elif ring == 1:
                sh = base[0] + 1 if tl else base[1]
                if (x, y) in ((n - 2, 1), (1, n - 2)):
                    sh = base[0]
            else:
                sh = base[0]
            g[y][x] = sh
    inner = range(2, n - 2)
    if style == 'plates':                  # short bright/dark dashes, like poured metal
        for y, x0, x1, tone in ((4, 7, 10, 4), (6, 3, 5, 4), (8, 8, 9, 4), (10, 4, 6, 4),
                                (7, 10, 12, 2), (9, 11, 12, 2), (11, 8, 11, 2), (12, 5, 7, 2)):
            for x in range(x0, x1 + 1):
                g[y][x] = tone
        for x, y in ((3, 3), (4, 3), (3, 4)):
            g[y][x] = 5
    elif style == 'facets':                # big cut-gem facets
        for y in inner:
            for x in inner:
                u, v = x + y, x - y
                sh = 4 if u < 13 else (3 if u < 19 else 2)
                if v in (-5, 4) and 9 <= u <= 21:
                    sh = max(1, sh - 1)    # facet edges
                if u in (13, 19):
                    sh = min(5, sh + 1)
                g[y][x] = sh
        for x, y in ((3, 3), (4, 3), (3, 4), (5, 3), (3, 5)):
            g[y][x] = 5
    else:                                  # 'void': dark mottled field
        for _ in range(16):
            x, y = rnd.choice(inner), rnd.choice(inner)
            tone = rnd.choice((1, 1, 3))
            for i in range(rnd.choice((1, 2, 3))):
                if x + i in inner:
                    g[y][x + i] = tone
    img = Image.new('RGBA', (n, n))
    px = img.load()
    for y in range(n):
        for x in range(n):
            px[x, y] = ramp[g[y][x]]
    if style == 'void':                    # a few faint sparks, nothing more
        for x, y, b in ((4, 5, 2), (10, 3, 1), (11, 10, 2), (5, 11, 1), (8, 7, 1)):
            px[x, y] = acc[b]
    return img


# ---------------------------------------------------------------- worn armour (64x32)
class Layer:
    def __init__(self, mat):
        m = MATERIALS[mat]
        self.ramp, self.acc = m['ramp'], m['accent']
        self.speckle = m['speckle'] * 0.5
        self.rnd = random.Random('armor/' + mat)
        self.img = Image.new('RGBA', (64, 32), (0, 0, 0, 0))
        self.px = self.img.load()

    def m(self, x, y, sh):
        sh = max(0, min(5, sh))
        if self.speckle and 2 <= sh <= 4 and self.rnd.random() < self.speckle:
            sh += self.rnd.choice((-1, 1))
        self.px[x, y] = self.ramp[sh]

    def a(self, x, y, sh):
        self.px[x, y] = self.acc[max(0, min(3, sh))]

    def plate(self, x0, y0, w, h, base=3, rim=True):
        """Bevelled plate: lit top/left edge, shaded bottom/right edge."""
        for y in range(y0, y0 + h):
            for x in range(x0, x0 + w):
                sh = base
                if rim:
                    if y == y0 or x == x0:
                        sh = base + 1
                    if y == y0 + h - 1 or x == x0 + w - 1:
                        sh = base - 1
                    if (x, y) == (x0, y0):
                        sh = base + 2
                self.m(x, y, sh)

    def trim(self, x0, x1, y, studs=True):
        for x in range(x0, x1):
            self.a(x, y, 3 if (studs and (x - x0) % 4 == 1) else 2)

    def clear(self, x0, y0, w, h):
        for y in range(y0, y0 + h):
            for x in range(x0, x0 + w):
                self.px[x, y] = (0, 0, 0, 0)


def armor_layer1(mat):
    L = Layer(mat)
    # ---- helmet: head box at (0,0), faces 8x8
    L.plate(8, 0, 8, 8, base=3)                     # top
    for y in range(1, 7):                           # crest ridge front-to-back
        L.m(11, y, 5)
        L.m(12, y, 4)
    for fx in (0, 8, 16, 24):                       # right, front, left, back
        L.plate(fx, 8, 8, 2, base=4, rim=False)
        for x in range(fx, fx + 8):
            L.m(x, 8, 5 if fx in (0, 8) else 4)
            L.m(x, 9, 4 if fx in (0, 8) else 3)
        L.trim(fx, fx + 8, 10)
    # sides and back come further down
    for fx, lit in ((0, 1), (16, 0), (24, 0)):
        for y in range(11, 15):
            for x in range(fx, fx + 8):
                L.m(x, y, 3 + lit - (1 if y >= 13 else 0))
        for x in range(fx, fx + 8):
            L.m(x, 14, 1)
    L.clear(0, 14, 2, 1)                            # sides sweep up toward the face
    L.clear(22, 14, 2, 1)
    # front: cheek guards + nasal bar around an open face
    for y in range(11, 14):
        L.m(8, y, 4)
        L.m(9, y, 3 if y < 13 else 2)
        L.m(14, y, 3 if y < 13 else 2)
        L.m(15, y, 2)
    for y in range(11, 13):
        L.m(11, y, 4)
        L.m(12, y, 2)
    L.a(11, 9, 3)                                   # brow gem
    L.a(12, 9, 2)
    # ---- chestplate: body box at (16,16)
    L.plate(20, 16, 8, 4, base=3)                   # shoulders/top
    L.clear(22, 17, 4, 2)                           # neck hole
    faces = ((16, 4, 2), (20, 8, 3), (28, 4, 2), (32, 8, 2))   # x, w, base  (right, front, left, back)
    for fx, w, base in faces:
        for y in range(20, 31):
            for x in range(fx, fx + w):
                sh = base
                if y == 20:
                    sh = base + 1
                if y in (26, 28):                   # lames over the belly
                    sh = base - 1
                if y in (27, 29):
                    sh = base + (1 if fx == 20 else 0)
                L.m(x, y, sh)
        L.trim(fx, fx + w, 30)
    for y in range(21, 26):                         # breast plates
        for x in range(20, 28):
            left = x < 24
            sh = 4 if left else 3
            if x in (23, 24):
                sh = 2                              # sternum seam
            if y == 21 and x not in (23, 24):
                sh = 5 if left else 4
            if y == 25:
                sh = 2
            if x in (20, 27):
                sh = 3 if left else 2
            L.m(x, y, sh)
    for (x, y, s) in ((23, 22, 3), (24, 22, 2), (23, 23, 2), (24, 23, 1)):
        L.a(x, y, s)                                # chest emblem
    for y in range(21, 30):                         # spine
        L.m(35, y, 1)
        L.m(36, y, 3)
    # ---- pauldrons: arm box at (40,16)
    L.plate(44, 16, 4, 4, base=4)
    for fx, base in ((40, 4), (44, 3), (48, 2), (52, 2)):   # outer, front, inner, back
        for y in range(20, 25):
            for x in range(fx, fx + 4):
                sh = base
                if y == 20:
                    sh = base + 1
                if y == 22:
                    sh = base - 1                   # overlapping plate seam
                if y == 24:
                    sh = base - 1
                L.m(x, y, sh)
        if fx != 48:
            L.trim(fx, fx + 4, 25, studs=False)
            L.a(fx + 1, 25, 3)
    # ---- boots: leg box at (0,16)
    L.plate(8, 16, 4, 4, base=1, rim=False)         # sole
    for fx, base in ((0, 3), (4, 3), (8, 2), (12, 2)):      # outer, front, inner, back
        L.trim(fx, fx + 4, 26, studs=False)
        L.a(fx + 1, 26, 3)
        for y in range(27, 32):
            for x in range(fx, fx + 4):
                sh = base
                if y == 27:
                    sh = base + 1
                if y == 30:
                    sh = base - 1
                if y == 31:
                    sh = 1
                L.m(x, y, sh)
    L.m(5, 29, 5)                                   # toe-cap glint
    L.m(6, 29, 5)
    return L.img


def armor_layer2(mat):
    L = Layer(mat)
    # ---- belt/tassets on the body box
    for fx, w, base in ((16, 4, 2), (20, 8, 3), (28, 4, 2), (32, 8, 2)):
        L.trim(fx, fx + w, 27)
        for y in range(28, 32):
            for x in range(fx, fx + w):
                sh = base + (1 if y == 28 else 0) - (1 if y == 31 else 0)
                L.m(x, y, sh)
    L.a(23, 27, 3)
    L.a(24, 27, 3)
    for y in range(28, 32):                         # front split
        L.m(23, y, 2)
        L.m(24, y, 1)
    # ---- legs
    L.plate(4, 16, 4, 4, base=3)
    for fx, base in ((0, 3), (4, 3), (8, 2), (12, 2)):
        for y in range(20, 30):
            for x in range(fx, fx + 4):
                sh = base
                if y == 20:
                    sh = base + 1
                if x == fx + 3:
                    sh = base - 1
                if y in (23, 27):
                    sh = base - 1                   # plate seams above/below the knee
                if y == 29:
                    sh = 1
                L.m(x, y, sh)
    for (x, y, s) in ((5, 24, 5), (6, 24, 4), (5, 25, 4), (6, 25, 3), (5, 26, 3), (6, 26, 2)):
        L.m(x, y, s)                                # knee cop
    L.a(4, 25, 2)
    L.a(7, 25, 1)
    return L.img


# Classic silhouettes: the shapes the mod has always used, re-coded as shade maps.
# 0/1 = outline (shadow side / lit side), 2-5 = material shades, A/a/b/c = handle.
C = {}

C['sword'] = [
    '.............110',
    '............1540',
    '...........15450',
    '..........15450.',
    '.........15450..',
    '........15450...',
    '..01...15450....',
    '..120.15450.....',
    '...0405450......',
    '...140450.......',
    '....0400........',
    '...ab0420.......',
    '..acA.0020......',
    '01bA....00......',
    '140.............',
    '000.............',
]

C['pickaxe'] = [
    '................',
    '................',
    '......11111.....',
    '.....1555550ab..',
    '......000044cA..',
    '..........a440..',
    '.........abA330.',
    '........acA.020.',
    '.......abA..120.',
    '......acA...120.',
    '.....abA....120.',
    '....acA......0..',
    '...abA..........',
    '..acA...........',
    '..bA............',
    '................',
]

C['axe'] = [
    '................',
    '.........11.....',
    '........1550....',
    '.......15550....',
    '......15555ab...',
    '......155543A...',
    '.......00a3320..',
    '........abA220..',
    '.......acA.00...',
    '......abA.......',
    '.....abA........',
    '....acA.........',
    '...abA..........',
    '..acA...........',
    '..bA............',
    '................',
]

C['shovel'] = [
    '................',
    '................',
    '...........111..',
    '..........14550.',
    '.........134450.',
    '........1223340.',
    '.........a2230..',
    '........acA20...',
    '.......acA.0....',
    '......abA.......',
    '.....acA........',
    '....abA.........',
    '..AacA..........',
    '..acA...........',
    '...aA...........',
    '................',
]

C['hoe'] = [
    '................',
    '.......111......',
    '......15540.....',
    '.......00440ab..',
    '.........033cA..',
    '..........a220..',
    '.........abA0...',
    '........acA.....',
    '.......abA......',
    '......acA.......',
    '.....abA........',
    '....acA.........',
    '...abA..........',
    '..acA...........',
    '..bA............',
    '................',
]

C['helmet'] = [
    '................',
    '................',
    '................',
    '.....111111.....',
    '....13333320....',
    '...1355333320...',
    '...1353332320...',
    '...1331110220...',
    '...1311100020...',
    '...1311000020...',
    '...1200000020...',
    '....10....00....',
    '................',
    '................',
    '................',
    '................',
]

C['chestplate'] = [
    '................',
    '................',
    '....11....11....',
    '..11331..13310..',
    '.133320..133320.',
    '.13333311333320.',
    '.13355333333320.',
    '..135333333320..',
    '..033333333320..',
    '...1333333320...',
    '...0333333320...',
    '...0333333320...',
    '...0233333320...',
    '....02222220....',
    '.....000000.....',
    '................',
]

C['leggings'] = [
    '................',
    '................',
    '....11111111....',
    '...1333333320...',
    '...1355333320...',
    '...1353223320...',
    '...1332003320...',
    '...1320..1320...',
    '...1320..1320...',
    '...1320..1320...',
    '...1320..1320...',
    '...1320..1320...',
    '...1320..1320...',
    '...1220..1220...',
    '...1000..1000...',
    '................',
]

C['boots'] = [
    '................',
    '................',
    '................',
    '....111..111....',
    '...1320..1320...',
    '...1520..1520...',
    '...1320..1320...',
    '...1320..1320...',
    '...1320..1320...',
    '..15320..13331..',
    '.133320..123320.',
    '.12220....02220.',
    '.1000......0000.',
    '................',
    '................',
    '................',
]


# ---------------------------------------------------------------- glow colours + extra animation styles
HALO = False        # True (--halo) paints the halo into the sprite; False leaves the glow to the game
GLOW_ITEMS = {}     # sprite file -> glow colour, filled by build(): the sprites whose items cast light
GLOW = {            # material -> the colour its items glow in game (and the glow lines on worn armour)
    'aquite': (140, 255, 226),
    'shadow': (158, 96, 255),
    'soul': (232, 170, 236),
    'magma': (255, 140, 30),
    'legacy': (80, 230, 240),
    'soulstar': (150, 240, 255),
    'flesh_glow': (180, 255, 70),
}


def add_glow(img, rgb, strength=1.0):
    """Semi-transparent halo hugging the outside of the sprite."""
    n = img.width
    k = n // 16
    px = img.load()
    solid = [(x, y) for y in range(n) for x in range(n) if px[x, y][3] == 255]
    grid = [[px[x, y][3] == 255 for x in range(n)] for y in range(n)]
    r = 2 * k + 1
    for y in range(n):
        for x in range(n):
            if grid[y][x]:
                continue
            best = 99.0
            for yy in range(max(0, y - r), min(n, y + r + 1)):
                for xx in range(max(0, x - r), min(n, x + r + 1)):
                    if grid[yy][xx]:
                        d = math.hypot(xx - x, yy - y) / k
                        if d < best:
                            best = d
            a = 105 if best <= 1.0 else (62 if best <= 1.5 else (30 if best <= 2.3 else 0))
            if a:
                px[x, y] = rgb + (int(a * strength),)
    return img


def render_glow(sprite, mat, seed, fx=None, outline=True, glow=None, strength=1.0):
    img = sprite.render(mat, seed, outline=outline, fx=fx)
    if glow and HALO:
        add_glow(img, glow, strength)
    return img


def anim_static(sprite, mat, seed, outline=True, glow=None):
    return [render_glow(sprite, mat, seed, outline=outline, glow=glow)]


def anim_glint(sprite, mat, seed, outline=True, glow=None, color=None, sweep=10, idle=14):
    """A bright glint (or a coloured wisp) runs up the metal once, then the sprite rests."""
    n = sprite.n
    k = n // 16
    frames = []
    lo, hi = 4 * k, 31 * k
    for f in range(sweep):
        a0 = lo + (hi - lo) * f / (sweep - 1)

        def fx(x, y, cell, colr, m, a0=a0):
            grp, sh = cell
            if grp != 'm' or sh < 2:
                return colr
            d = abs(diag(n, x, y)[0] - a0) / k
            if d <= 1.0:
                if color:
                    return mix(colr, color + (255,), 0.85)
                return mix(m['ramp'][min(5, sh + 2)], WHITE, 0.45 if sh >= 4 else 0.15)
            if d <= 2.6:
                if color:
                    return mix(colr, color + (255,), 0.4)
                return m['ramp'][min(5, sh + 1)]
            return colr
        frames.append(render_glow(sprite, mat, seed, fx=fx, outline=outline, glow=glow))
    return frames + [render_glow(sprite, mat, seed, outline=outline, glow=glow)] * idle


def anim_pulse(sprite, mat, seed, outline=True, glow=None, count=16, body=0.0):
    """Highlights, accents and the halo breathe slowly."""
    frames = []
    for f in range(count):
        t = (1 - math.cos(2 * math.pi * f / count)) / 2

        def fx(x, y, cell, colr, m, t=t):
            grp, sh = cell
            if grp == 'x':
                return mix(colr, mix(m['accent'][3], WHITE, 0.35), 0.75 * t)
            if grp == 'm':
                if sh == 5:
                    return mix(colr, WHITE if body else m['accent'][3], 0.6 * t)
                if sh >= 2 and body:
                    return mix(colr, m['ramp'][sh + 1], body * t)
                if sh == 4:
                    return mix(colr, m['ramp'][5], 0.3 * t)
            return colr
        frames.append(render_glow(sprite, mat, seed, fx=fx, outline=outline, glow=glow, strength=0.45 + 0.55 * t))
    return frames


def anim_flow(sprite, mat, seed, outline=True, glow=None, count=12):
    """Bands of heat crawl up the blade (lava)."""
    n = sprite.n
    frames = []
    for f in range(count):
        ph = 2 * math.pi * f / count

        def fx(x, y, cell, colr, m, ph=ph):
            grp, sh = cell
            if grp != 'm' or sh < 2:
                return colr
            a, c = diag(n, x, y)
            s = sh + int(round(0.95 * math.sin(a * 1.05 + c * 0.35 - ph)))
            return m['ramp'][max(2, min(5, s))]
        frames.append(render_glow(sprite, mat, seed, fx=fx, outline=outline, glow=glow,
                                  strength=0.75 + 0.25 * math.sin(ph)))
    return frames


def anim_prism(sprite, mat, seed, outline=True, glow=None, count=14):
    """The brightest edge cycles through the rainbow."""
    n = sprite.n
    frames = []
    for f in range(count):
        def fx(x, y, cell, colr, m, f=f):
            grp, sh = cell
            if grp == 'm' and sh == 5:
                a = diag(n, x, y)[0]
                r, g, b = colorsys.hsv_to_rgb((f / count + a * 0.035) % 1.0, 0.55, 1.0)
                return (int(r * 255), int(g * 255), int(b * 255), 255)
            return colr
        frames.append(render_glow(sprite, mat, seed, fx=fx, outline=outline, glow=glow))
    return frames


META = {
    'glint': '{\n  "animation": { "frametime": 2 }\n}\n',
    'pulse': '{\n  "animation": { "frametime": 3 }\n}\n',
    'flow': '{\n  "animation": { "frametime": 2 }\n}\n',
    'prism': '{\n  "animation": { "frametime": 2 }\n}\n',
    'ultimate': '{\n  "animation": { "frametime": 20, "interpolate": true }\n}\n',   # same as the original mod
}
ANIMS = {'glint': anim_glint, 'pulse': anim_pulse, 'flow': anim_flow, 'prism': anim_prism}


# ---------------------------------------------------------------- unique items: palettes
SOULPINK = [hx(c) for c in ('2e2038', '7a5a8c', 'd8b8e6', 'ffffff')]
CYAN = [hx(c) for c in ('07343c', '129aa6', '48e2d6', 'e6fffb')]
MAGMAROCK = [hx(c) for c in ('140705', '36160e', '5a2817', '8a4424')]
DIAMONDH = [hx(c) for c in ('0a3a40', '13777a', '27b3ad', '9ff5ea')]
BLOOD = [hx(c) for c in ('3a0000', '8a0808', 'd81414', 'ff6a54')]
GLOWGREEN = [hx(c) for c in ('1a3a08', '4a9a10', 'a8f030', 'f0ffb0')]
EMBER = [hx(c) for c in ('5a1400', 'c83a00', 'ff7a10', 'ffd24a')]


def _mat(name, ramp, handle, accent, speckle=0.0):
    MATERIALS[name] = dict(ramp=[hx(c) for c in ramp], handle=handle, accent=accent, speckle=speckle)


_mat('soul', ['100104', '34060b', '5c0d16', '8a1722', 'b63840', 'e8868e'], DARKWOOD, SOULPINK)
_mat('magma', ['360900', '861c00', 'd64600', 'ff8600', 'ffc21a', 'fff29a'], MAGMAROCK, IRONDARK)
_mat('pigman', ['381216', '782c32', 'b65656', 'de8880', 'f4b8ac', 'ffe8de'], DIAMONDH, GOLD)
_mat('reaper', ['0e1014', '2c3038', '565c68', '8a929e', 'c2c8d0', 'ffffff'], WOOD, STEEL)
_mat('legacy', ['010204', '090c11', '131920', '202934', '34445a', '5ed0e0'], DARKWOOD, CYAN)
_mat('soulstar', ['082830', '16666e', '36b4b6', '8ae8e0', 'd6fff8', 'ffffff'], WOOD, SOULPINK)
_mat('cream', ['3a2600', '8a5a00', 'c89410', 'e8c830', 'f6ee70', 'ffffd0'], WOOD, EMBER)
_mat('flesh_bloody', ['2a0c06', '5a2012', '8a4226', 'ae6238', 'c88654', 'e8be8e'], WOOD, BLOOD)
_mat('flesh_glow', ['2a1606', '5a3412', '8a5a26', 'ae8238', 'c8a654', 'f0e08e'], WOOD, GLOWGREEN)
_mat('slap', ['03131a', '0b2c38', '144e5c', '217886', '48b2be', 'b8f2f8'], WOOD, CYAN)

ULT_HUES = [0.0, 0.07, 0.15, 0.33, 0.58, 0.76, 0.88]     # the original mod's colour cycle


def hue_ramp(h):
    def c(dh, s, v):
        r, g, b = colorsys.hsv_to_rgb((h + dh) % 1.0, s, v)
        return (int(r * 255), int(g * 255), int(b * 255), 255)
    return [c(0.045, 0.95, 0.18), c(0.03, 0.95, 0.40), c(0.015, 0.92, 0.64),
            c(0.0, 0.88, 0.93), c(-0.02, 0.52, 1.0), c(-0.03, 0.16, 1.0)]


for _i, _h in enumerate(ULT_HUES):
    MATERIALS[f'ultimate{_i}'] = dict(ramp=hue_ramp(_h), handle=WOOD, accent=STEEL, speckle=0.0)


# ---------------------------------------------------------------- unique items: shapes
T['saber'] = [
    '................',
    '...........54...',
    '..........5543..',
    '.........55432..',
    '........554432..',
    '.......554432...',
    '......554332....',
    '.....554332.....',
    '....55432.......',
    '..z.5432........',
    '..xy432.........',
    '...xzy..........',
    '..cbxy..........',
    '.cba............',
    '.xy.............',
    '................',
]

T['broad'] = [
    '................',
    '............555.',
    '...........5543.',
    '..........55432.',
    '.........554332.',
    '........554332..',
    '.......554332...',
    '......554332....',
    '..z..554332.....',
    '..xy.54332......',
    '...xy4332.......',
    '....xzy2........',
    '...cbxy.........',
    '..cba.xy........',
    '.xy.............',
    '................',
]

T['scythe'] = [
    '................',
    '....5555554.....',
    '..554444443321..',
    '.543......3321c.',
    '.42.........cba.',
    '.3.........cba..',
    '..........cba...',
    '.........cba....',
    '........cba.....',
    '.......cba......',
    '......cba.......',
    '.....cba........',
    '....cba.........',
    '...cba..........',
    '..xy............',
    '................',
]

T['flesh'] = [
    '................',
    '................',
    '.........44.....',
    '.......554y3....',
    '.....5544x332...',
    '....544y43332...',
    '...5444433x32...',
    '..54x44y3322....',
    '..4443x3322.....',
    '..33y32222......',
    '...2222.........',
    '................',
    '................',
    '................',
    '................',
    '................',
]

T['nugget'] = [
    '................',
    '................',
    '................',
    '................',
    '................',
    '......554.......',
    '.....55443......',
    '.....54433......',
    '.....44332......',
    '......332.......',
    '................',
    '................',
    '................',
    '................',
    '................',
    '................',
]


def star16():
    s = Sprite(16)
    for y in range(16):
        for x in range(16):
            dx, dy = x - 7.5, y - 7.5
            v = (abs(dx) / 7.2) ** 0.62 + (abs(dy) / 7.2) ** 0.62
            if v <= 1.0:
                lit = -(dx + dy)
                sh = 5 if lit > 2.5 else (4 if lit > 0 else (3 if lit > -3 else 2))
                if abs(dx) < 1 and abs(dy) < 1:
                    s.put(x, y, 'z' if (dx < 0 and dy < 0) else 'y')
                elif abs(dx) + abs(dy) <= 2.2:
                    s.put(x, y, 'y' if lit > 0 else 'x')
                else:
                    s.put(x, y, str(sh))
    return s


def ball16():
    s = Sprite(16)
    spots = {(9, 9): 'y', (10, 9): 'x', (6, 10): 'y', (10, 6): 'z', (8, 11): 'x', (5, 7): 'y', (7, 5): 'z', (8, 8): 'x'}
    for y in range(16):
        for x in range(16):
            dx, dy = x - 7.5, y - 8.0
            if math.hypot(dx, dy) <= 5.4:
                t = -(dx + dy) / 7.6
                sh = 5 if t > 0.62 else (4 if t > 0.25 else (3 if t > -0.3 else 2))
                s.put(x, y, spots.get((x, y), str(sh)))
    return s


def _line(x0, y0, x1, y1):
    pts = []
    n = max(abs(x1 - x0), abs(y1 - y0), 1)
    for i in range(n + 1):
        pts.append((int(round(x0 + (x1 - x0) * i / n)), int(round(y0 + (y1 - y0) * i / n))))
    return pts


def bow16(pull=0):
    """Triple slap: recurve limbs with a grip wrap; pull 1-3 draws the string back with three arrows."""
    s = Sprite(16)
    for y in range(1, 13):
        for x in range(1, 13):
            d = math.hypot(x - 12.5, y - 12.5)
            if 9.9 <= d <= 12.3:
                if abs(x - y) <= 1:
                    s.put(x, y, 'z' if d > 11.4 else ('y' if d > 10.6 else 'x'))
                else:
                    s.put(x, y, '1' if d > 11.6 else (('5' if x + y < 9 else '4') if d > 10.7 else '2'))
    k = pull * 1.6
    px_, py_ = int(round(6.5 + k)), int(round(6.5 + k))
    string = _line(12, 2, px_, py_) + _line(px_, py_, 2, 12) if pull else _line(12, 2, 2, 12)
    for (x, y) in string:
        if s.g[y][x] is None:
            s.put(x, y, 'z')
    if pull:                                   # one shaft, three heads fanned at the tip
        shaft = _line(px_, py_, 2, 2)
        for (x, y) in shaft:
            s.put(x, y, 'c')
        for (x, y) in ((1, 1), (2, 1), (1, 2), (4, 1), (1, 4)):
            s.put(x, y, '5')
        for (x, y) in ((3, 1), (1, 3)):
            s.put(x, y, '4')
    return s


def part_of(sprite, keep):
    """Cut one piece (handle / guard / blade) out of a finished sprite."""
    p = Sprite(sprite.n)
    for y in range(sprite.n):
        for x in range(sprite.n):
            c = sprite.g[y][x]
            if c is not None and keep(x, y, c, diag(sprite.n, x, y)[0]):
                p.g[y][x] = c
    return p


# ---------------------------------------------------------------- worn armour, double resolution (128x64)
class HDLayer:
    def __init__(self, mat, glow=None):
        self.img = Image.new('RGBA', (128, 64), (0, 0, 0, 0))
        self.px = self.img.load()
        self.glowc = glow
        self.use(mat)

    def use(self, mat):
        m = MATERIALS[mat]
        self.ramp, self.acc = m['ramp'], m['accent']
        self.speckle = m['speckle'] * 0.4
        self.rnd = random.Random('hd/' + mat)

    def m(self, x, y, sh):
        sh = max(0, min(5, sh))
        if self.speckle and 2 <= sh <= 4 and self.rnd.random() < self.speckle:
            sh += self.rnd.choice((-1, 1))
        self.px[x, y] = self.ramp[sh]

    def a(self, x, y, sh):
        self.px[x, y] = self.acc[max(0, min(3, sh))]

    def g(self, x, y, bright=1):
        """Glow pixel on glowing sets, plain accent stud otherwise."""
        if self.glowc:
            self.px[x, y] = mix(self.glowc + (255,), WHITE, 0.55 if bright == 2 else 0.1)
        else:
            self.a(x, y, 3 if bright == 2 else 2)

    def glow_only(self, x, y, bright=1):
        if self.glowc:
            self.g(x, y, bright)

    def plate(self, x0, y0, w, h, base=3):
        for y in range(y0, y0 + h):
            for x in range(x0, x0 + w):
                sh = base
                if y == y0 or x == x0:
                    sh = base + 1
                if y == y0 + h - 1 or x == x0 + w - 1:
                    sh = base - 1
                if (x, y) == (x0, y0):
                    sh = base + 2
                self.m(x, y, sh)

    def clear(self, x0, y0, w, h):
        for y in range(y0, y0 + h):
            for x in range(x0, x0 + w):
                self.px[x, y] = (0, 0, 0, 0)


def armor_hd1(mat, glow=None, parts=None):
    """Helmet, chestplate (with pauldrons) and boots at 2x the vanilla layout."""
    P = parts or {}
    L = HDLayer(mat, glow)
    # ---- helmet
    L.use(P.get('helmet', mat))
    X, Y = 16, 0
    L.plate(X, Y, 16, 16, base=4)
    for v in range(1, 15):
        L.m(X + 7, Y + v, 5)
        L.m(X + 8, Y + v, 3)
    for u, v in ((2, 2), (13, 2), (2, 13), (13, 13)):
        L.m(X + u, Y + v, 2)
    for bx, name in ((0, 'right'), (8, 'front'), (16, 'left'), (24, 'back')):
        X, Y = bx * 2, 16
        for u in range(16):
            L.m(X + u, Y, 5)
            L.m(X + u, Y + 1, 4)
            L.m(X + u, Y + 2, 3 if u % 8 == 7 else 4)
            L.m(X + u, Y + 3, 3)
            if u % 4 == 1:
                L.g(X + u, Y + 4, 1)
            else:
                L.a(X + u, Y + 4, 2)
            L.a(X + u, Y + 5, 1)
        if name == 'front':
            for v in range(6, 12):
                wdt = 3 if v < 10 else 2
                for u in range(wdt):
                    L.m(X + u, Y + v, 2 if v == 6 else (4 if u == 0 else 3))
                    L.m(X + 15 - u, Y + v, 2 if (v == 6 or u == 0) else 3)
            for u in (0, 1, 14, 15):
                L.m(X + u, Y + 11, 1)
            for v in range(6, 11):
                L.m(X + 7, Y + v, 4 if v < 10 else 2)
                L.m(X + 8, Y + v, 2 if v < 10 else 1)
            for u, v, s in ((7, 2, 3), (8, 2, 2), (6, 3, 2), (9, 3, 1)):
                L.a(X + u, Y + v, s)
            L.g(X + 7, Y + 3, 2)
            L.g(X + 8, Y + 3, 1)
            L.g(X + 7, Y + 4, 1)
            L.g(X + 8, Y + 4, 1)
        else:
            for u in range(16):
                long_ = name == 'back' or (name == 'right' and u < 8) or (name == 'left' and u >= 8)
                bottom = 13 if long_ else 11
                for v in range(6, bottom + 1):
                    sh = 3
                    if v == 6:
                        sh = 2
                    elif u % 8 == 0:
                        sh = 4
                    elif u % 8 == 7:
                        sh = 2
                    if v == bottom - 1:
                        sh = 4
                    if v == bottom:
                        sh = 1
                    L.m(X + u, Y + v, sh)
    # ---- chestplate
    L.use(P.get('chest', mat))
    X, Y = 40, 32
    L.plate(X, Y, 16, 8, base=3)
    L.clear(X + 4, Y + 2, 8, 4)
    for bx, w, name in ((16, 4, 'right'), (20, 8, 'front'), (28, 4, 'left'), (32, 8, 'back')):
        X, Y, W = bx * 2, 40, w * 2
        for u in range(W):
            L.m(X + u, Y, 4)
            L.m(X + u, Y + 1, 3)
        if name == 'front':
            L.plate(X, Y + 2, 8, 10, base=3)
            L.plate(X + 8, Y + 2, 8, 10, base=3)
            for u in range(1, 7):
                L.m(X + u, Y + 3, 4)
            for u, v, s in ((2, 4, 5), (3, 4, 5), (2, 5, 4), (10, 4, 4), (11, 4, 4)):
                L.m(X + u, Y + v, s)
            L.m(X, Y + 11, 1)
            L.m(X + 15, Y + 11, 1)
            for u in range(6, 10):
                L.m(X + u, Y, 2)
            for u, v, s in ((7, 5, 3), (8, 5, 2), (6, 6, 2), (9, 6, 1), (6, 7, 2), (9, 7, 1), (7, 8, 1), (8, 8, 1)):
                L.a(X + u, Y + v, s)
            for u, v, b in ((7, 6, 2), (8, 6, 1), (7, 7, 1), (8, 7, 1)):
                L.g(X + u, Y + v, b)
        elif name == 'back':
            L.plate(X, Y + 2, 16, 10, base=3)
            for v in range(3, 11):
                L.m(X + 7, Y + v, 4)
                L.m(X + 8, Y + v, 2)
            for u in (2, 3, 4, 5, 10, 11, 12, 13):
                L.m(X + u, Y + 6, 2)
                L.m(X + u, Y + 7, 4)
        else:
            L.plate(X, Y + 2, W, 10, base=3)
        for v in range(12, 20):                     # belly lames
            for u in range(W):
                top = v % 2 == 0
                sh = 3 if top else 2
                if top and u == 0:
                    sh = 4
                if not top and u == W - 1:
                    sh = 1
                L.m(X + u, Y + v, sh)
        if name in ('front', 'back'):
            for v in range(12, 20):
                L.m(X + 7, Y + v, 2)
                L.m(X + 8, Y + v, 1 if name == 'front' else 3)
                if v % 2:
                    L.glow_only(X + 7, Y + v, 1)
        for u in range(W):                          # hem
            if u % 4 == 1:
                L.g(X + u, Y + 20, 1)
            else:
                L.a(X + u, Y + 20, 2)
            L.a(X + u, Y + 21, 1)
    # ---- pauldrons
    L.use(P.get('arms', mat))
    X, Y = 88, 32
    L.plate(X, Y, 8, 8, base=4)
    for u, v, s in ((3, 3, 3), (4, 3, 2), (3, 4, 2), (4, 4, 1)):
        L.a(X + u, Y + v, s)
    for bx, name in ((40, 'outer'), (44, 'front'), (48, 'inner'), (52, 'back')):
        X, Y = bx * 2, 40
        plates = ((0, 4), (4, 4), (8, 2)) if name != 'inner' else ((0, 4), (4, 3))
        for v0, h in plates:
            for v in range(v0, v0 + h):
                for u in range(8):
                    sh = 3
                    if u == 0:
                        sh = 4
                    if u == 7:
                        sh = 2
                    if v == v0:
                        sh = 5 if v0 == 0 else 4
                    if v == v0 + h - 1 and h > 2:
                        sh = 2
                    L.m(X + u, Y + v, sh)
        if name != 'inner':
            for u in range(8):
                if u in (1, 5):
                    L.g(X + u, Y + 10, 1)
                else:
                    L.a(X + u, Y + 10, 2)
                L.a(X + u, Y + 11, 1)
    # ---- boots
    L.use(P.get('boots', mat))
    X, Y = 16, 32
    for v in range(8):
        for u in range(8):
            L.m(X + u, Y + v, 0 if (u in (0, 7) or v in (0, 7)) else 1)
    for bx, name in ((0, 'outer'), (4, 'front'), (8, 'inner'), (12, 'back')):
        X, Y = bx * 2, 40
        for u in range(8):
            if u in (1, 5):
                L.g(X + u, Y + 12, 1)
            else:
                L.a(X + u, Y + 12, 2)
            L.a(X + u, Y + 13, 1)
            for v in range(14, 22):
                sh = 3
                if u == 0:
                    sh = 4
                if u == 7:
                    sh = 2
                if v == 14:
                    sh = 4
                if v == 17:
                    sh = 2
                L.m(X + u, Y + v, sh)
            L.m(X + u, Y + 22, 1)
            L.m(X + u, Y + 23, 0)
        if name == 'front':
            for v in range(18, 22):
                for u in range(1, 7):
                    L.m(X + u, Y + v, 3 if v == 21 else 4)
            L.m(X + 2, Y + 18, 5)
            L.m(X + 3, Y + 18, 5)
            L.m(X + 2, Y + 19, 5)
    return L.img


def armor_hd2(mat, glow=None, parts=None):
    """Leggings: belt and tassets on the body, plated legs with mail at the knee joint."""
    P = parts or {}
    L = HDLayer(mat, glow)
    L.use(P.get('belt', mat))
    for bx, w, name in ((16, 4, 'right'), (20, 8, 'front'), (28, 4, 'left'), (32, 8, 'back')):
        X, Y, W = bx * 2, 40, w * 2
        for u in range(W):
            L.a(X + u, Y + 14, 2)
            L.a(X + u, Y + 15, 1)
        segs = ((0, 5), (5, 6), (11, 5)) if name == 'front' else (((0, 8), (8, 8)) if W == 16 else ((0, 8),))
        for u0, wd in segs:
            L.plate(X + u0, Y + 16, wd, 8, base=3)
            for u in range(u0, u0 + wd):
                L.m(X + u, Y + 23, 1)
        if name == 'front':
            for u in range(6, 10):
                L.a(X + u, Y + 14, 3)
                L.a(X + u, Y + 15, 2)
            L.g(X + 7, Y + 14, 2)
            L.g(X + 8, Y + 14, 1)
    L.use(P.get('legs', mat))
    L.plate(8, 32, 8, 8, base=3)
    for bx, name in ((0, 'outer'), (4, 'front'), (8, 'inner'), (12, 'back')):
        X, Y = bx * 2, 40
        L.plate(X, Y, 8, 9, base=3)
        for v in range(9, 13):
            for u in range(8):
                L.m(X + u, Y + v, 2 if (u + v) % 2 else 1)
        L.plate(X, Y + 13, 8, 7, base=3)
        for u in range(8):
            L.m(X + u, Y + 19, 1)
        if name == 'front':
            for u in range(1, 7):
                L.m(X + u, Y + 9, 4)
                L.m(X + u, Y + 12, 2)
            for v in (10, 11):
                for u in range(8):
                    L.m(X + u, Y + v, 2 if u == 7 else 4)
            L.m(X + 2, Y + 10, 5)
            L.m(X + 3, Y + 10, 5)
            L.glow_only(X + 4, Y + 11, 1)
        if name == 'outer':
            for v in range(2, 7):
                L.a(X + 3, Y + v, 2)
                L.a(X + 4, Y + v, 1)
            L.glow_only(X + 3, Y + 4, 1)
    return L.img


# ---------------------------------------------------------------- output map
SETS = ['aquite', 'colosifite', 'emerald', 'lapis', 'obsidian', 'quartz', 'redstone', 'shadow']
TOOLS = ['sword', 'pickaxe', 'axe', 'shovel', 'hoe', 'helmet', 'chestplate', 'leggings', 'boots']

# existing file name -> material that the item using it is actually made of
POLE_FILES = {
    'aquite': 'aquite', 'colosifite': 'colosifite', 'emerald': 'emerald', 'shadow': 'shadow',
    'diamond': 'lapis',      # dagger/greatsword/halberd "_diamond" files are the Lapis items
    'iron': 'quartz',        # "_iron" files are the Quartz items
}
INGOT_FILES = {'aquite_ingot': 'aquite', 'colosifite_ingot': 'colosifite', 'obsidain_ingot': 'obsidian',
               'redstone_ingot': 'redstone', 'shadow_ingot': 'shadow'}
ARMOR_LAYER_NAMES = {   # material -> (equipment file stem, legacy stem)
    'aquite': ('aquite', 'aquite'), 'colosifite': ('colosifite_', 'colosifite_'),
    'emerald': ('emerald_', 'emerald_'), 'lapis': ('lapis_', 'lapis_'),
    'obsidian': ('obsidian_', 'obsidian_'), 'quartz': ('quartz__', 'quartz__'),
    'redstone': ('redstone_', 'redstone_'), 'shadow': ('shadow_', 'shadow_'),
}


# ---------------------------------------------------------------- what gets drawn
WEAPONS = ('sword', 'dagger', 'greatsword', 'halberd')
ARMOR_ICONS = ('helmet', 'chestplate', 'leggings', 'boots')
CLASSIC = ('sword', 'pickaxe', 'axe', 'shovel', 'hoe') + ARMOR_ICONS    # drawn from the C[...] silhouettes


def set_style(mat, kind):
    """(animation, glow colour) for one piece of a regular material set."""
    glow = GLOW.get(mat)
    if mat in ('aquite', 'colosifite') and kind in WEAPONS:
        return 'glint', glow
    if mat == 'shadow':
        return 'pulse', glow
    if mat == 'redstone' and kind in ('sword',) + ARMOR_ICONS:
        return 'pulse', glow
    return None, glow


def build(root, hd_armor=True):
    out, meta = {}, {}
    sp = {k: Sprite.from_ascii(v) for k, v in T.items()}
    cl = {k: Sprite.from_ascii(v) for k, v in C.items()}
    sp.update(greatsword=greatsword(), halberd=halberd())

    def emit(rel, sprite, mat, seed, anim=None, glow=None, outline=True, **kw):
        if glow:
            GLOW_ITEMS[rel] = glow
        if anim:
            frames = ANIMS[anim](sprite, mat, seed, outline=outline, glow=glow, **kw)
            out[rel] = strip(frames)
            meta[rel] = META[anim]
        else:
            out[rel] = render_glow(sprite, mat, seed, outline=outline, glow=glow)

    # ---- the eight regular sets
    for mat in SETS:
        for t in TOOLS:
            anim, glow = set_style(mat, t)
            kw = {'body': 0.35} if (anim == 'pulse' and mat == 'redstone') else {}
            emit(f'items/{mat}_{t}.png', cl[t], mat, t, anim, glow, outline=False, **kw)
    for stem, mat in INGOT_FILES.items():
        emit(f'items/{stem}.png', sp['ingot'], mat, 'ingot')
    for suffix, mat in POLE_FILES.items():
        for kind in ('dagger', 'greatsword', 'halberd'):
            anim, glow = set_style(mat, kind)
            emit(f'items/{kind}_{suffix}.png', sp[kind], mat, kind, anim, glow)
    emit('items/long_stick.png', long_stick(), 'iron', 'longstick')
    emit('items/stick.png', sp['stick'], 'diamond', 'stick')
    emit('items/string.png', sp['string'], 'obsidian', 'string', outline=False)

    # ---- Ultimate set: the original seven-colour cycle, one frame per colour
    def ultimate(rel, sprite, seed, outline=True):
        out[rel] = strip([sprite.render(f'ultimate{i}', seed, outline=outline) for i in range(len(ULT_HUES))])
        meta[rel] = META['ultimate']
    for t in ARMOR_ICONS:
        ultimate(f'items/ultimate_{t}.png', cl[t], t, outline=False)
    ultimate('items/material_ultimate_ingot.png', sp['ingot'], 'ingot')
    ultimate('items/material_ultimate_nugget.png', sp['nugget'], 'nugget')
    out['blocks/storage_ultimate.png'] = strip([metal_block(f'ultimate{i}', 'block', 'plates')
                                                for i in range(len(ULT_HUES))])
    meta['blocks/storage_ultimate.png'] = META['ultimate']

    # ---- unique weapons and oddities
    emit('items/bruh_sword.png', sp['saber'], 'soul', 'souleater', 'glint', GLOW['soul'],
         color=GLOW['soul'], sweep=12, idle=8)                                    # Soul eater
    emit('items/idk_sword.png', sp['broad'], 'magma', 'magmasword', 'flow', GLOW['magma'])   # magma sword
    emit('items/pigman_sword.png', cl['sword'], 'pigman', 'pigman', 'glint', None, outline=False,
         color=(255, 226, 110))                                                   # Pigman sword
    emit('items/reaper_scythe.png', sp['scythe'], 'reaper', 'scythe', 'prism')    # Reaper scythe
    emit('items/stone_sword.png', sp['broad'], 'legacy', 'legacy', 'pulse', GLOW['legacy'])  # The nether's legacy
    legacy = sp['broad']
    emit('items/stone_sword_start.png', part_of(legacy, lambda x, y, c, a: c[0] == 'h' or (c[0] == 'x' and a <= 5)),
         'legacy', 'legacy')                                                      # Sword handle
    emit('items/stone_sword_mid.png', part_of(legacy, lambda x, y, c, a: c[0] == 'x' and a > 5),
         'legacy', 'legacy')                                                      # Sword middle
    emit('items/stone_sword_end.png', part_of(legacy, lambda x, y, c, a: c[0] == 'm'),
         'legacy', 'legacy')                                                      # obsidian blade
    emit('items/nether_star.png', star16(), 'soulstar', 'star', 'pulse', GLOW['soulstar'])   # Souled nether star
    emit('items/magma_cream_je3_be2.png', ball16(), 'cream', 'cream', 'pulse', None, body=0.25)   # enchanted Magma
    emit('items/adsbfas.png', sp['flesh'], 'flesh_bloody', 'flesh')               # Bloody rotten flesh
    emit('items/rotten_flesh_je3_be2.png', sp['flesh'], 'flesh_glow', 'flesh', 'pulse', GLOW['flesh_glow'])
    emit('items/rbow.png', bow16(0), 'slap', 'bow', outline=False)                # Triple slap
    for i in range(3):
        emit(f'items/rbow{i}.png', bow16(i + 1), 'slap', 'bow', outline=False)

    # ---- blocks
    out['blocks/aquite_ore.png'] = ore('aquite', 'shards', 'stone-a')
    out['blocks/colosifite_ore.png'] = ore('colosifite', 'nuggets', 'stone-c')
    out['blocks/shadow_ore.png'] = ore('shadow', 'voids', 'stone-s')
    out['blocks/colosifite_block.png'] = metal_block('colosifite', 'block', 'plates')
    out['blocks/aquite_block.png'] = metal_block('aquite', 'block', 'facets')
    out['blocks/shadow_block.png'] = metal_block('shadow', 'block', 'void')

    # ---- worn armour: 128x64 by default, 64x32 with --std-armor
    ult_parts = {'helmet': 'ultimate0', 'chest': 'ultimate1', 'arms': 'ultimate2',
                 'belt': 'ultimate3', 'legs': 'ultimate4', 'boots': 'ultimate5'}
    worn = dict(ARMOR_LAYER_NAMES)
    worn['ultimate'] = ('ultimate', 'ultimate')
    for mat, (stem, legacy_stem) in worn.items():
        if mat == 'ultimate':
            hd1, hd2 = armor_hd1('ultimate0', parts=ult_parts), armor_hd2('ultimate3', parts=ult_parts)
            std1, std2 = hd1.resize((64, 32), Image.NEAREST), hd2.resize((64, 32), Image.NEAREST)
        else:
            hd1, hd2 = armor_hd1(mat, GLOW.get(mat)), armor_hd2(mat, GLOW.get(mat))
            std1, std2 = armor_layer1(mat), armor_layer2(mat)
        l1, l2 = (hd1, hd2) if hd_armor else (std1, std2)
        out[f'entity/equipment/humanoid/{stem}.png'] = l1
        out[f'entity/equipment/humanoid_leggings/{stem}.png'] = l2
        out[f'models/armor/{legacy_stem}_layer_1.png'] = std1     # legacy copies stay standard size
        out[f'models/armor/{legacy_stem}_layer_2.png'] = std2

    for rel, img in out.items():
        # Horizon's item/block atlases use singular modern texture paths.
        asset_rel = ('item/' + rel[6:] if rel.startswith('items/') else
                     'block/' + rel[7:] if rel.startswith('blocks/') else rel)
        p = os.path.join(root, asset_rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        img.save(p)
        mp = p + '.mcmeta'
        if rel in meta:
            with open(mp, 'w') as f:
                f.write(meta[rel])
        elif os.path.exists(mp):
            os.remove(mp)       # this sprite is no longer animated
    return out


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output')
    parser.add_argument('--std-armor', action='store_true')
    parser.add_argument('--halo', action='store_true')
    args = parser.parse_args()
    HALO = args.halo
    made = build(args.output, hd_armor=not args.std_armor)
    print(f'wrote {len(made)} textures to {args.output}')
