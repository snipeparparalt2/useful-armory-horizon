#!/usr/bin/env python3
"""New 0.1.7 art: trinkets, backpacks, golem core, soul jars, waystone, soul forge, gold chicken
and the new mobs.

Usage:  python3 tools/gen_new_art.py content/assets/useful_armory/textures

Writes only the files listed in build() below; it never touches the existing equipment, ores
or worn armour (tools/gen_textures.py owns those). Palettes and helpers come from gen_textures.

Mob textures are 64x64 humanoid (zombie) layout with both limb UV areas painted, plus <mob>_e.png
holding only the glowing pixels. The shadow hound uses the 64x32 wolf layout and the gold chicken
the 64x32 chicken layout.
"""
import math
import os
import random
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_textures as B  # noqa: E402


def hx(h):
    return B.hx(h)


# ------------------------------------------------------------------ 2. a small painter for new art
def ramp(*hexes):
    return [B.hx(h) for h in hexes]


R = {
    'gold': ramp('3a2204', '6e4608', 'a87010', 'e0a81e', 'f8d850', 'fff6b0'),
    'silver': ramp('1e2228', '4a5058', '7c8490', 'b0b8c2', 'dde2e8', 'ffffff'),
    'iron': ramp('1a1a20', '34363e', '54565f', '74777f', '9a9da6', 'c8cacf'),
    'leather': ramp('2a1508', '4e2a12', '74421e', '98602e', 'b88048', 'd8a46c'),
    'darkleather': ramp('1a0e06', '32190a', '4a2810', '643a1a', '7e5028', '9a6a3a'),
    'cord': ramp('1c1410', '3a2c22', '5a4636', '7a644e', '9a846a', 'bca88c'),
    'wool': ramp('3a0808', '6a1010', '9a1c1c', 'c43030', 'e05a4a', 'f49a88'),
    'cork': ramp('2e1c0c', '5a3a1c', '86592c', 'aa7a40', 'c89a5a', 'e2bc80'),
    'soul': ramp('0b2f3a', '1a5f6e', '2fa4a8', '5fd8cf', 'a8f5ea', 'e8fffb'),
    'wstone': ramp('17191d', '23262c', '30343b', '3e434b', '50565f', '68707a'),
    'forge': ramp('120e15', '1c1720', '28202e', '362c3e', '463a50', '5c4e68'),
    'bone': ramp('3a3226', '6a5e4a', '9a8c70', 'c2b494', 'e0d4b6', 'fbf4e2'),
    'feather': ramp('5a3a04', '8e6008', 'c08e12', 'e8b820', 'f8dc52', 'fff6b4'),
    'beak': ramp('5a2c04', '8e4808', 'c86a10', 'e89020', 'f8b850', 'ffe0a0'),
    'wattle': ramp('3a0404', '6a0a0a', 'a01414', 'd02020', 'f04a3a', 'ff8a7a'),
}
for _m in ('aquite', 'colosifite', 'emerald', 'lapis', 'obsidian', 'quartz', 'redstone', 'shadow'):
    R[_m] = B.MATERIALS[_m]['ramp']

GROUPS = ('012345', 'ABCDEF', 'abcdef', 'pqrstu')  # 'G' is a placeholder handled by soul_jar
WHITE = (255, 255, 255, 255)


def paint(rows, pals, outline=True, alpha=None):
    """rows: ascii art. pals: up to 4 ramps, one per char group (0-5, A-F, a-f, p-u).
    alpha: optional {group_index: alpha} for see-through groups (glass)."""
    h, w = len(rows), len(rows[0])
    assert all(len(r) == w for r in rows), [len(r) for r in rows]
    img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    px = img.load()
    grp = [[None] * w for _ in range(h)]
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch in '. ':
                continue
            for gi, chars in enumerate(GROUPS):
                if ch in chars:
                    c = pals[gi][chars.index(ch)]
                    a = (alpha or {}).get(gi, 255)
                    px[x, y] = c[:3] + (a,)
                    grp[y][x] = (gi, chars.index(ch))
                    break
            else:
                raise ValueError(ch)
    if outline:
        add_outline(img, grp, pals)
    return img


def add_outline(img, grp, pals):
    px = img.load()
    w, h = img.size
    for y in range(h):
        for x in range(w):
            if grp[y][x] is not None:
                continue
            best = None
            for dx, dy, lit in ((1, 0, True), (0, 1, True), (-1, 0, False), (0, -1, False)):
                xx, yy = x + dx, y + dy
                if 0 <= xx < w and 0 <= yy < h and grp[yy][xx] is not None:
                    gi, _ = grp[yy][xx]
                    o = B.mix(pals[gi][0], pals[gi][1], 0.3) if lit else pals[gi][0]
                    if best is None or sum(o[:3]) < sum(best[:3]):
                        best = o
            if best is not None:
                px[x, y] = best[:3] + (255,)


def canvas(n=16):
    return [['.'] * n for _ in range(n)]


def rows_of(c):
    return [''.join(r) for r in c]


def stamp(c, x0, y0, art):
    for dy, row in enumerate(art):
        for dx, ch in enumerate(row):
            if ch != ' ':
                c[y0 + dy][x0 + dx] = ch


# ------------------------------------------------------------------ 3. trinkets
GEM_CUT = [          # stamped with its top-left at (4, 1)
    '   54   ',
    '  5443  ',
    ' D4332C ',
    '  D32C  ',
    '  CDDC  ',
]


def ring(gem, band):
    c = canvas()
    cx, cy, ox, oy, ix, iy = 7.5, 10.2, 5.7, 4.0, 3.5, 2.0
    for y in range(16):
        for x in range(16):
            dx, dy = x - cx, y - cy
            if (dx / ox) ** 2 + (dy / oy) ** 2 <= 1 and (dx / ix) ** 2 + (dy / iy) ** 2 > 1:
                inner = (dx / (ix + 1.1)) ** 2 + (dy / (iy + 1.0)) ** 2 <= 1
                t = -(dx / ox) * 0.7 - (dy / oy)
                if dy < 0 and inner:
                    sh = 1                          # far side of the band, seen from inside
                else:
                    sh = 5 if t > 0.95 else (4 if t > 0.35 else (3 if t > -0.35 else 2))
                c[y][x] = 'ABCDEF'[sh]
    stamp(c, 4, 2, GEM_CUT)
    return paint(rows_of(c), [R[gem], R[band]])


CORD_TOP = [         # cord loop the charms and recall charm hang from, top-left at (5, 0)
    '      ',
    ' eddc ',
    'e    b',
    'd    b',
    ' cEDb ',
]

CHARM_COLOSIFITE = [
    '................',
    '................',
    '................',
    '................',
    '................',
    '.......ED.......',
    '......E55D......',
    '.....E5443C.....',
    '.....D4433C.....',
    '.....EDDDDC.....',
    '.....D4332B.....',
    '.....D3322B.....',
    '......D22B......',
    '.......CB.......',
    '................',
    '................',
]

CHARM_OBSIDIAN = [
    '................',
    '................',
    '................',
    '................',
    '................',
    '.......FD.......',
    '.......54.......',
    '......5543......',
    '......FED3......',
    '.....543FE......',
    '.....4433D......',
    '.....EF322......',
    '......3DE1......',
    '.......21.......',
    '................',
    '................',
]

RECALL = [
    '................',
    '................',
    '................',
    '................',
    '................',
    '......CDDB......',
    '.....E4444C.....',
    '....E445543C....',
    '....D4p4443B....',
    '....D4rq443B....',
    '....D43sr32B....',
    '....D433t32B....',
    '....C3332q2A....',
    '.....C2222A.....',
    '......BBBA......',
    '................',
]


def charm(art, body, metal, extra=None):
    c = [list(r) for r in art]
    stamp(c, 5, 0, CORD_TOP)
    return paint(rows_of(c), [R[body], R[metal], R['cord'], R[extra] if extra else R['soul']])


def amulet(gem, metal):
    c = canvas()
    for i in range(6):                                  # chain: two strands meeting at the bail
        for x, y in ((3 + i * 0.75, 1 + i), (12 - i * 0.75, 1 + i)):
            c[int(round(y))][int(round(x))] = 'E' if i % 2 == 0 else 'C'
    c[7][7], c[7][8] = 'D', 'C'
    cx, cy = 7.5, 10.5
    for y in range(16):
        for x in range(16):
            d = math.hypot(x - cx, y - cy)
            t = -((x - cx) + (y - cy)) / 4.0
            if d <= 2.2:
                c[y][x] = '5' if t > 0.6 else ('4' if t > 0.0 else ('3' if t > -0.6 else '2'))
            elif d <= 3.6:
                c[y][x] = 'F' if t > 0.55 else ('E' if t > 0.0 else ('D' if t > -0.55 else 'B'))
    c[9][6] = '5'
    c[14][7], c[14][8] = 'C', 'B'
    return paint(rows_of(c), [R[gem], R[metal]])


# ------------------------------------------------------------------ 4. backpacks
PACK_SMALL = [
    '................',
    '......abba......',
    '......a..a......',
    '....45555443....',
    '...5444444433...',
    '...cccccccccb...',
    '...bbbbbbbbba...',
    '...bbbbFEbbba...',
    '...abbbDCbbaa...',
    '...4433333322...',
    '...43cbbbba22...',
    '...43bbECba22...',
    '...43abbbaa21...',
    '...3322222211...',
    '....22111111....',
    '................',
]

PACK_MEDIUM = [
    '................',
    '......abba......',
    '......a..a......',
    '....45555443....',
    '...5444444433...',
    '..ccccccccccbb..',
    '..bbbbbbbbbbba..',
    '..bbbFEbbFEbba..',
    '..abbDCbbDCbaa..',
    '..c44333333322..',
    '..b43cbbbba22a..',
    '..b43bbECba22a..',
    '..a43abbbaa21a..',
    '..a33222222211..',
    '...222111111a...',
    '................',
]

PACK_LARGE = [
    '...rsssssssrq...',
    '..rsttttttsrqp..',
    '..qrrrrrrrrqqp..',
    '...cbbbbbbbbb...',
    '..5544444444333.',
    '.ccccccccccccbb.',
    '.bbbbbbbbbbbbba.',
    '.bbbFEbbbbFEbba.',
    '.abbDCbbbbDCbaa.',
    '.c4443333333322.',
    '.b443cbbbbba22a.',
    '.b443bbbECba22a.',
    '.a443abbbbaa21a.',
    '.a3332222222211.',
    '..2221111111aa..',
    '................',
]


def backpack(art, leather, strap, metal):
    return paint(art, [R[leather], R[metal], R[strap], R['wool']])


# ------------------------------------------------------------------ 5. golem core, soul jar
def golem_core():
    c = canvas()
    cx, cy = 7.5, 8.0
    for y in range(16):
        for x in range(16):
            d = math.hypot(x - cx, y - cy)
            t = -((x - cx) * 0.8 + (y - cy)) / 5.5
            if d <= 2.3:
                c[y][x] = '5' if d < 0.9 else ('4' if d < 1.7 else '3')
            elif d <= 3.1:
                c[y][x] = 'B'
            elif d <= 6.0:
                sh = 5 if t > 0.62 else (4 if t > 0.2 else (3 if t > -0.25 else (2 if t > -0.6 else 1)))
                c[y][x] = 'ABCDEF'[sh]
    for x, y in ((7, 2), (8, 2), (2, 7), (2, 8), (13, 7), (13, 8), (7, 13), (8, 13)):
        c[y][x] = 'C'                                   # seams
    for x, y in ((4, 4), (11, 4), (4, 11), (11, 11)):
        c[y][x] = 'F' if x + y < 15 else 'B'            # rivets
    return paint(rows_of(c), [R['aquite'], R['iron']])


def jar_mask():
    m = {}
    for y in range(3, 15):
        if y <= 4:
            xs = range(6, 10)
        elif y == 5 or y == 14:
            xs = range(5, 11)
        else:
            xs = range(4, 12)
        for x in xs:
            m[(x, y)] = None
    return m


def soul_jar(phase=None):
    """phase None = empty jar; 0..1 = filled jar, swirl phase for the animation."""
    c = canvas()
    mask = jar_mask()
    for (x, y) in mask:
        edge = not all((x + dx, y + dy) in mask for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        if y == 3:
            ch = 't'
        elif edge:
            ch = 's' if (x <= 5 or (y == 5 and x < 8)) else 'q'
        else:
            ch = 'G'                                    # see-through glass, filled in below
            if phase is not None and y >= 6:
                v = math.sin(x * 1.3 + y * 0.9 - phase * 2 * math.pi) + math.sin(y * 1.7 - x * 0.6 + phase * 2 * math.pi)
                sh = 2 if v < -0.9 else (3 if v < 0.4 else (4 if v < 1.3 else 5))
                if y == 6:
                    sh = min(sh, 3)
                ch = str(sh)
        c[y][x] = ch
    for y in range(6, 12):
        if c[y][5] in 'G2345':
            c[y][5] = 'u'
    c[7][6] = 'u' if c[7][6] == 'G' else c[7][6]
    stamp(c, 6, 1, ['dffd', 'cddb'])
    glass = [(x, y) for y in range(16) for x in range(16) if c[y][x] == 'G']
    for x, y in glass:
        c[y][x] = 'u'                                   # treat as solid while outlining
    img = paint(rows_of(c), [R['soul'], R['iron'], R['cork'], R['silver']])
    px = img.load()
    for x, y in glass:
        px[x, y] = R['silver'][4][:3] + (64,)
    return img


# ------------------------------------------------------------------ 6. blocks
def stone_field(rmp, seed, n=16):
    rnd = random.Random(seed)
    g = [[2] * n for _ in range(n)]
    for _ in range(40):
        x, y = rnd.randrange(n), rnd.randrange(n)
        tone = rnd.choice((1, 1, 3, 3, 3, 4))
        for i in range(rnd.choice((1, 2, 3))):
            g[y][(x + i) % n] = tone
    return g


RUNE = [            # waystone glyph, 6 wide x 10 tall, placed at (5, 3)
    '..##..',
    '.#..#.',
    '..##..',
    '...#..',
    '#..#..',
    '.#.#.#',
    '..###.',
    '...#..',
    '..#.#.',
    '.#...#',
]


def waystone_side():
    rm = R['wstone']
    g = stone_field(rm, 'waystone-side')
    for y in range(16):
        for x in range(16):
            if x in (0, 15) or y in (0, 15):
                g[y][x] = 4 if (x == 0 or y == 0) else 0
            elif x in (1, 14) or y in (1, 14):
                g[y][x] = 3 if (x == 1 or y == 1) else 1
    for y in range(2, 14):                              # recessed panel
        g[y][3] = 0
        g[y][12] = 4
    for x in range(3, 13):
        g[2][x] = 0
        g[13][x] = 4
    base = Image.new('RGBA', (16, 16))
    px = base.load()
    for y in range(16):
        for x in range(16):
            px[x, y] = rm[g[y][x]]
    glow = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
    gp = glow.load()
    aq = R['aquite']
    for dy, row in enumerate(RUNE):
        for dx, ch in enumerate(row):
            if ch == '#':
                x, y = 5 + dx, 3 + dy
                px[x, y] = aq[1]                        # carved groove, dim when unlit
                if x + 1 < 16:
                    px[x + 1, y] = B.mix(rm[g[y][x + 1]], rm[0], 0.5)
                gp[x, y] = aq[4] if (dx + dy) % 3 else aq[5]
    return base, glow


def waystone_top():
    rm = R['wstone']
    g = stone_field(rm, 'waystone-top')
    base = Image.new('RGBA', (16, 16))
    px = base.load()
    glow = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
    gp = glow.load()
    aq = R['aquite']
    for y in range(16):
        for x in range(16):
            sh = g[y][x]
            if x in (0, 15) or y in (0, 15):
                sh = 4 if (x == 0 or y == 0) else 0
            d = math.hypot(x - 7.5, y - 7.5)
            if 4.6 <= d <= 5.5:
                sh = 0                                  # carved ring
            px[x, y] = rm[sh]
            if 4.6 <= d <= 5.5 and (int(math.degrees(math.atan2(y - 7.5, x - 7.5))) // 30) % 2 == 0:
                gp[x, y] = aq[4]
            if d <= 1.6:
                px[x, y] = aq[3] if d < 0.9 else aq[2]
                gp[x, y] = aq[5] if d < 0.9 else aq[4]
    return base, glow


def forge_bricks(seed):
    rm = R['forge']
    rnd = random.Random(seed)
    g = [[2] * 16 for _ in range(16)]
    for y in range(16):
        row = y // 4
        off = 0 if row % 2 == 0 else 4
        for x in range(16):
            if y % 4 == 3 or (x + off) % 8 == 7:
                g[y][x] = 0                             # mortar
            elif y % 4 == 0 or (x + off) % 8 == 0:
                g[y][x] = 3                             # lit brick edge
            else:
                g[y][x] = rnd.choice((2, 2, 2, 1, 3))
    return g


def to_img(g, rm):
    img = Image.new('RGBA', (16, 16))
    px = img.load()
    for y in range(16):
        for x in range(16):
            px[x, y] = rm[g[y][x]]
    return img


def soul_forge(frames=6):
    rm, sl = R['forge'], R['soul']
    side = to_img(forge_bricks('forge-side'), rm)
    # top: brick rim with an iron grate over the soul fire
    g = forge_bricks('forge-top')
    top = to_img(g, rm)
    tpx = top.load()
    top_glow = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
    tg = top_glow.load()
    for y in range(4, 12):
        for x in range(4, 12):
            if x in (4, 11) or y in (4, 11):
                tpx[x, y] = R['iron'][2 if (x == 11 or y == 11) else 4]
            elif x % 2 == 1:
                tpx[x, y] = R['iron'][1]
            else:
                tpx[x, y] = sl[3]
                tg[x, y] = sl[4]
    # front: mouth with animated soul fire, two glowing rune slots above it
    fronts, glows = [], []
    for f in range(frames):
        g = forge_bricks('forge-front')
        img = to_img(g, rm)
        px = img.load()
        gl = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
        gp = gl.load()
        for y in range(6, 15):
            for x in range(3, 13):
                arch = y > 6 or 5 <= x <= 10
                if not arch:
                    continue
                if x in (3, 12) or y == 6 or (y == 7 and x in (4, 11)):
                    px[x, y] = R['iron'][4 if (x == 3 or y == 6) else 2]
                    continue
                if y == 14:
                    px[x, y] = R['iron'][1]
                    continue
                h = 13 - y
                flick = math.sin(x * 1.9 + f * 2 * math.pi / frames) + math.sin(x * 0.7 - f * 4 * math.pi / frames)
                height = 2.6 + 0.9 * flick
                if h <= height:
                    k = h / max(height, 0.1)
                    sh = 5 if k < 0.25 else (4 if k < 0.55 else (3 if k < 0.85 else 2))
                    px[x, y] = sl[sh]
                    gp[x, y] = sl[min(5, sh + 1)]
                else:
                    px[x, y] = B.mix(rm[1], sl[1], 0.35 if h <= height + 2 else 0.12)   # soul-lit back wall
        for x in (5, 6, 9, 10):
            px[x, 3] = sl[2]
            gp[x, 3] = sl[4]
        fronts.append(img)
        glows.append(gl)
    return side, top, top_glow, B.strip(fronts), B.strip(glows)


# ------------------------------------------------------------------ 7. gold chicken (64x32, vanilla chicken UV layout)
def box(px, u, v, w, h, d, face_fn):
    faces = {
        'top': (u + d, v, w, d), 'bottom': (u + d + w, v, w, d),
        'right': (u, v + d, d, h), 'front': (u + d, v + d, w, h),
        'left': (u + d + w, v + d, d, h), 'back': (u + 2 * d + w, v + d, w, h),
    }
    for name, (x0, y0, fw, fh) in faces.items():
        for y in range(fh):
            for x in range(fw):
                px[x0 + x, y0 + y] = face_fn(name, x, y, fw, fh)


def gold_chicken():
    img = Image.new('RGBA', (64, 32), (0, 0, 0, 0))
    px = img.load()
    fe, bk, wt = R['feather'], R['beak'], R['wattle']
    rnd = random.Random('gold-chicken')

    def feathers(name, x, y, fw, fh):
        sh = {'top': 4, 'front': 3, 'left': 3, 'right': 3, 'back': 2, 'bottom': 2}[name]
        if name in ('front', 'left', 'right', 'back') and y % 3 == 2 and (x + y) % 2 == 0:
            sh -= 1                                     # feather rows
        if name == 'top' and rnd.random() < 0.25:
            sh = 5
        if rnd.random() < 0.08:
            sh = min(5, sh + 1)
        return fe[max(1, sh)]

    def head(name, x, y, fw, fh):
        c = feathers(name, x, y, fw, fh)
        if name == 'front' and y == 1 and x in (0, 3):
            return (20, 14, 6, 255)                     # eyes
        if name in ('left', 'right') and y == 1 and x == (1 if name == 'left' else 1):
            return (20, 14, 6, 255)
        return c

    box(px, 0, 0, 4, 6, 3, head)
    box(px, 14, 0, 4, 2, 2, lambda n, x, y, w, h: bk[4 if n == 'top' else (3 if y == 0 else 2)])
    box(px, 14, 4, 2, 2, 2, lambda n, x, y, w, h: wt[3 if y == 0 else 2])
    box(px, 0, 9, 6, 8, 6, feathers)
    box(px, 26, 0, 3, 5, 3, lambda n, x, y, w, h: bk[3 if (n == 'front' or n == 'top') else 2] if y < h - 1 or n in ('top', 'bottom') else bk[1])
    box(px, 24, 13, 1, 4, 6, lambda n, x, y, w, h: fe[4 if n in ('top', 'left') else (3 if y < 2 else 2)])
    return img



# ------------------------------------------------------------------ mobs
SHADE = {'front': 0.0, 'right': 0.12, 'left': 0.12, 'back': 0.22, 'top': -0.08, 'bottom': 0.32}
GLOW_CHARS = '*+'


def face_colour(pal, ch, face):
    if ch in ('.', ' '):
        return None
    c = pal[ch]
    if ch in GLOW_CHARS:
        return c
    k = SHADE[face]
    if k >= 0:
        return B.mix(c, (0, 0, 0, 255), k)
    return B.mix(c, (255, 255, 255, 255), -k)


class Skin:
    def __init__(self, size, pal):
        self.img = Image.new('RGBA', size, (0, 0, 0, 0))
        self.e = Image.new('RGBA', size, (0, 0, 0, 0))
        self.px, self.ep = self.img.load(), self.e.load()
        self.pal = pal

    def box(self, u, v, w, h, d, faces):
        """faces: name -> list of strings (exact face size) or a single fill char."""
        rects = {
            'top': (u + d, v, w, d), 'bottom': (u + d + w, v, w, d),
            'right': (u, v + d, d, h), 'front': (u + d, v + d, w, h),
            'left': (u + d + w, v + d, d, h), 'back': (u + 2 * d + w, v + d, w, h),
        }
        for name, (x0, y0, fw, fh) in rects.items():
            art = faces.get(name, faces.get('*'))
            if art is None:
                continue
            if isinstance(art, str):
                art = [art * fw] * fh
            assert len(art) == fh and all(len(r) == fw for r in art), (name, fw, fh, art)
            for y, row in enumerate(art):
                for x, ch in enumerate(row):
                    col = face_colour(self.pal, ch, name)
                    if col is None:
                        continue
                    self.px[x0 + x, y0 + y] = col
                    if ch in GLOW_CHARS:
                        self.ep[x0 + x, y0 + y] = col


def narrow(rows, w):
    """Cut a 4-wide limb column down/up to a side face of width w (for d=4 it is unchanged)."""
    return [r[:w] for r in rows]


def humanoid(pal, head_front, head_side, head_back, head_top, body_front, body_back, arm, leg,
             hat=None):
    s = Skin((64, 64), pal)
    s.box(0, 0, 8, 8, 8, {'front': head_front, 'right': head_side,
                          'left': [r[::-1] for r in head_side], 'back': head_back,
                          'top': head_top, 'bottom': head_top})
    if hat:
        s.box(32, 0, 8, 8, 8, hat)
    side_body = [r[:4] for r in body_back]
    s.box(16, 16, 8, 12, 4, {'front': body_front, 'back': body_back, 'right': side_body,
                             'left': side_body, 'top': body_front[0][0], 'bottom': body_back[-1][0]})
    for (u, v) in ((40, 16), (32, 48)):
        s.box(u, v, 4, 12, 4, {'*': arm, 'top': arm[0][0], 'bottom': arm[-1][0]})
    for (u, v) in ((0, 16), (16, 48)):
        s.box(u, v, 4, 12, 4, {'*': leg, 'top': leg[0][0], 'bottom': leg[-1][0]})
    return s


def P(**kw):
    return {k: hx(v) if isinstance(v, str) else v for k, v in kw.items()}


# ------------------------------------------------------------------ shade (cave wraith)
SHADE_PAL = P(k='0d0a14', d='1a1426', m='2a2040', l='3e2f5e', h='5a4486', v='8d7be0',
              **{'*': 'e2d0ff', '+': 'a070ff'})
SHADE_MOB = dict(
    head_front=['lmmmmmml', 'mddddddm', 'dkkkkkkd', 'dk*kk*kd', 'dkkkkkkd', 'dkk++kkd', 'mdkkkkdm', 'lmddddml'],
    head_side=['llmmmmll', 'lmmmmmml', 'mmmddmmm', 'mmddddmm', 'mdddddmm', 'mddddddm', 'dddddddd', 'mdmddmdm'],
    head_back=['llmmmmll', 'lmmlmmml', 'mmmmmmmm', 'mmmhmmmm', 'mmmmmmmm', 'mdmmmmdm', 'dmdmmdmd', 'd.dmd.dm'],
    head_top='l',
    body_front=['dmmllmmd', 'dmmllmmd', 'dmmhlmmd', 'dmmllmmd', 'ddmllmdd', 'ddmmmmdd', 'dddmmddd',
                'dddmmddd', 'ddmddmdd', 'dmdddddm', 'md.dd.dm', '.d.d..d.'],
    body_back=['dmmmmmmd', 'dmmlmmmd', 'dmmmmmmd', 'ddmmmmdd', 'ddmmmmdd', 'dddmmddd', 'dddmdddd',
               'ddmddmdd', 'dmddddmd', 'mddmdddm', 'd.dd.ddm', '.d..d.d.'],
    arm=['mllm', 'mllm', 'mmmm', 'dmmd', 'dmmd', 'dmmd', 'ddmd', 'dddd', 'dkkd', 'dkkd', 'kvvk', 'k++k'],
    leg=['dmmd', 'dmmd', 'ddmd', 'dddd', 'dddd', 'dkdd', 'kddk', 'dkkd', 'kdkd', '.d.k', '....', '....'],
)

# ------------------------------------------------------------------ tide lurker (beach / river ambusher)
TIDE_PAL = P(**{'1': '173a35', '2': '1e4a44', '3': '2e6b5f', '4': '4a9480'}, b='c8c0a8', B='8a8270',
             c='14243e', C='1e3558', x='2c4a74', g='23401a', G='3a6a24', h='58922e', k='08160f',
             **{'*': '8affe8'})
TIDE_MOB = dict(
    head_front=['3Gg34gG3', '343g3433', '3222322b', '2*k22*k2', '33322333', '3kkkkkk3', '3kbkbkk3', '23333332'],
    head_side=['G3g33gG3', '33g3b333', '333B3333', '33333233', '32333333', '3333b333', '23333332', '22222222'],
    head_back=['GgGgGgGg', 'gGhgGhgG', 'GgGgGgGg', '3gG3gG3g', '33g33g33', '3333g333', '33b33333', '22222222'],
    head_top='g',
    body_front=['cCCxxCCc', 'cCCxxCCc', 'c3CxxC3c', 'cCCCCCCc', 'cCCbCCCc', 'cCCCCCCc', 'BBBBBBBB',
                'cCcCCcCc', 'cCCCCCCc', 'gCC3CCcg', '3g333c3g', '33333333'],
    body_back=['cCCCCCCc', 'cCCCCCCc', 'cCgCCCCc', 'cCgCCCCc', 'cCCCCbCc', 'cCCCCCCc', 'BBBBBBBB',
               'cCcCCcCc', 'cCCCCCCc', 'cCC3CCgc', '3c333g33', '33333333'],
    arm=['CCCC', 'CcCc', '3333', '34g3', '3g33', '3333', '33b3', '3333', '3333', '2333', '3223', '2222'],
    leg=['cCCc', 'cCCc', 'cCCc', 'cCcc', 'cCCc', 'cCcC', 'c3Cc', '3c33', '3333', '3333', '2332', '2222'],
)

# ------------------------------------------------------------------ ember brute (cracked charcoal giant)
EMBER_PAL = P(**{'1': '120c0a', '2': '1e1510', '3': '2e2018', '4': '46301f'}, l='5a3418', L='7a4a24',
              i='3a3a44', I='5c5e6a', **{'*': 'ffc040', '+': 'ff6a10'})
EMBER_MOB = dict(
    head_front=['34333433', '33+33343', '3**33**3', '33133133', '33333333', '31++++13', '33111133', '23333332'],
    head_side=['34333433', '33333+33', '333+3333', '33333333', '3+333333', '33333+33', '33333333', '22222222'],
    head_back=['33333333', '3333+333', '33+33333', '33333333', '333333+3', '3+333333', '33333333', '22222222'],
    head_top='4',
    body_front=['Ll3333lL', '3Ll33lL3', '33LiIL33', '3+3Ll3+3', '33+33333', '3333+333', '333+3333',
                'llllllll', 'lLLiILLl', 'LllllllL', '3LllllL3', '33LllL33'],
    body_back=['L333333L', '3L3333L3', '33L33L33', '333LL333', '33+3333+', '3+333+33', '333+3333',
               'llllllll', 'LLLLLLLL', '3LLLLLL3', '33LLLL33', '333LL333'],
    arm=['iIIi', 'IiiI', '3333', '33+3', '3+33', '3333', '333+', '3333', '3+33', '4444', '3333', '2222'],
    leg=['3333', '3+33', '33+3', '3333', '3333', '33+3', '3333', 'lLLl', 'LllL', 'lLLl', 'LllL', 'iiii'],
)

# ------------------------------------------------------------------ lost pigman (rotting pig-folk scavenger)
PIG_PAL = P(**{'2': 'a0565a', '3': 'c87878', '4': 'e0a0a0'}, r='6a7a3a', R='4a5a28', n='d08890', N='7a3a40',
            y='e0c040', k='0a0a0a', w='f0e8d0', g='a87810', G='f0d040', c='5a3a24', C='7a5232')
PIG_MOB = dict(
    head_front=['34433443', '3rR34433', '3yk33ky3', '33333333', '33nnnn33', '33nNNn33', '3w3nn3w3', '23333332'],
    head_side=['44333333', '43333333', '33333R33', '3333rR33', '33333333', '33333333', '33333333', '22222222'],
    head_back=['33333333', '333r3333', '33rR3333', '33333333', '33333333', '333333r3', '33333333', '22222222'],
    head_top='3',
    body_front=['33333333', '3r333333', '3Rr33G33', '33333G33', '3333G333', '333G3333', '33G33333',
                'cGcccccc', 'CcCgGCcC', 'CCCCCCCC', 'CcCCCCcC', '3CC33CC3'],
    body_back=['33333333', '33333r33', '3333rR33', '33333333', '33r33333', '33Rr3333', '33333333',
               'cccccccc', 'CCCCCCCC', 'CCCCCCCC', 'CCCCCCCC', '3CC33CC3'],
    arm=['3333', '3333', '33r3', '3333', '3333', '3333', 'gGGg', 'GggG', '3333', '3333', '3333', '2222'],
    leg=['CCCC', 'CcCC', 'CCCC', '3333', '33r3', '3333', '3333', '3333', '3333', '2222', 'NNNN', 'NNNN'],
)

# ------------------------------------------------------------------ vault guardian (shadow-plate knight)
VAULT_PAL = P(**{'1': '0b0b15', '2': '161728', '3': '24263f', '4': '3c3f63'}, v='4a1f9a', V='8a4df0',
              c='2e2f38', C='50525f', **{'*': 'e6d4ff', '+': 'a070ff'})
VAULT_MOB = dict(
    head_front=['33444433', '34333343', '33333333', '2*++++*2', '22222222', '32v22v23', '33322333', '23333332'],
    head_side=['33444333', '34333333', '33333333', '22222222', '33333333', '3v333333', '33333333', '22222222'],
    head_back=['33333333', '33333333', '33333333', '22222222', '33333333', '33333333', '33333333', '22222222'],
    head_top='4',
    body_front=['43333334', '34444443', '333vv333', '33vV+v33', '333vv333', '33333333', '22222222',
                '33333333', '22222222', 'vvvvvvvv', 'CcCcCcCc', 'cCcCcCcC'],
    body_back=['33333333', '34333343', '33333333', '33333333', '33333333', '33333333', '22222222',
               '33333333', '22222222', 'vvvvvvvv', 'CcCcCcCc', 'cCcCcCcC'],
    arm=['4443', '3332', 'vvvv', '3333', '2222', 'cCcC', 'CcCc', '4443', '3332', '3332', '2222', '2222'],
    leg=['cCcC', 'CcCc', '3333', '3343', '3333', '2222', '3333', '3333', '3333', '2222', 'vvvv', '2222'],
)

# ------------------------------------------------------------------ tower sentry (undead colosifite soldier)
SENTRY_PAL = P(**{'1': '24262c', '2': '5a5e68', '3': '8f949e', '4': 'bcc1c9'}, o='c85a0b', O='8c3207',
               z='3a4a3a', Z='566a52', c='34363e', C='54565f', k='101410', **{'*': 'ffba42'})
SENTRY_MOB = dict(
    head_front=['34444443', '43333334', '2zZZZZz2', '2*zZZ*z2', '2zZZZZz2', '2zkkkkz2', '2zZzzZz2', 'cCcCcCcC'],
    head_side=['34444443', '43333334', '33333333', '33333333', '33333333', 'cCcCcCcC', 'CcCcCcCc', 'cCcCcCcC'],
    head_back=['34444443', '43333334', '33333333', '33333333', '33333333', 'cCcCcCcC', 'CcCcCcCc', 'cCcCcCcC'],
    head_top='4',
    body_front=['cCOOOOCc', 'CcOooOcC', 'cCo33oCc', 'Cco33ocC', 'cCo33oCc', 'Cco44ocC', '22222222',
                'cCooooCc', 'CcooooCc', 'cCooooCc', 'CcooooCc', 'cCooooCc'],
    body_back=['cCOOOOCc', 'CcOooOcC', 'cCooooCc', 'CcooooCc', 'cCooooCc', 'CcooooCc', '22222222',
               'cCooooCc', 'CcooooCc', 'cCooooCc', 'CcooooCc', 'cCooooCc'],
    arm=['3443', 'cCcC', 'CcCc', 'cCcC', 'CcCc', '2332', '3443', '3443', '2332', 'zZZz', 'zZZz', 'zzzz'],
    leg=['CcCc', 'cCcC', 'CcCc', 'cCcC', 'CcCc', '2332', '3443', '3333', '3333', '2222', '1111', '1111'],
)


# ------------------------------------------------------------------ shadow hound (64x32 wolf layout)
def shadow_hound():
    pal = P(k='07060c', d='17141f', m='2a2535', l='3e3650', h='564a70', n='050408',
            **{'*': 'd0a8ff'})
    s = Skin((64, 32), pal)
    fur = lambda w, h, seed: [''.join('lmmdml'[(x * 3 + y * 5 + seed) % 6] for x in range(w)) for y in range(h)]
    s.box(0, 0, 6, 6, 4, {'*': fur(6, 6, 1), 'right': fur(4, 6, 2), 'left': fur(4, 6, 3), 'top': 'l', 'bottom': 'd',
                          'front': ['lmmmml', 'mmmmmm', 'm*mm*m', 'dmmmmd', 'dmddmd', 'dddddd']})
    s.box(16, 14, 2, 2, 1, {'*': 'd', 'front': ['lm', 'mk']})                        # ears
    s.box(0, 10, 3, 3, 4, {'*': 'm', 'front': ['mnm', 'mmm', 'ddd'], 'top': 'l', 'bottom': 'd'})   # snout
    s.box(21, 0, 8, 6, 7, {'*': fur(8, 6, 4), 'right': fur(7, 6, 5), 'left': fur(7, 6, 6), 'top': 'h', 'bottom': 'd'})  # mane
    s.box(18, 14, 6, 9, 6, {'*': fur(6, 9, 7), 'right': fur(6, 9, 8), 'left': fur(6, 9, 9), 'top': 'l', 'bottom': 'd'})  # body
    s.box(0, 18, 2, 8, 2, {'*': ['mm', 'mm', 'md', 'mm', 'dm', 'dd', 'dd', 'kk'], 'top': 'm', 'bottom': 'k'})     # legs
    s.box(9, 18, 2, 8, 2, {'*': ['dd', 'dm', 'mm', 'ml', 'mm', 'll', 'lh', 'hh'], 'top': 'd', 'bottom': 'h'})                    # tail
    return s


MOBS = {
    'shade': (SHADE_PAL, SHADE_MOB),
    'tide_lurker': (TIDE_PAL, TIDE_MOB),
    'ember_brute': (EMBER_PAL, EMBER_MOB),
    'lost_pigman': (PIG_PAL, PIG_MOB),
    'vault_guardian': (VAULT_PAL, VAULT_MOB),
    'tower_sentry': (SENTRY_PAL, SENTRY_MOB),
}



# ------------------------------------------------------------------ assemble
def build(tex):
    out, meta = {}, {}
    out['item/aquite_ring.png'] = ring('aquite', 'silver')
    out['item/lapis_ring.png'] = ring('lapis', 'gold')
    out['item/quartz_ring.png'] = ring('quartz', 'gold')
    out['item/ring_of_luck.png'] = ring('emerald', 'gold')
    out['item/colosifite_charm.png'] = charm(CHARM_COLOSIFITE, 'colosifite', 'iron')
    out['item/obsidian_charm.png'] = charm(CHARM_OBSIDIAN, 'obsidian', 'gold')
    out['item/emerald_amulet.png'] = amulet('emerald', 'gold')
    out['item/shadow_amulet.png'] = amulet('shadow', 'iron')
    out['item/recall_charm.png'] = charm(RECALL, 'wstone', 'iron', extra='aquite')
    out['item/backpack_small.png'] = backpack(PACK_SMALL, 'leather', 'darkleather', 'iron')
    out['item/backpack_medium.png'] = backpack(PACK_MEDIUM, 'leather', 'darkleather', 'iron')
    out['item/backpack_large.png'] = backpack(PACK_LARGE, 'leather', 'darkleather', 'gold')
    out['item/golem_core.png'] = golem_core()
    out['item/soul_jar.png'] = soul_jar(None)
    out['item/soul_jar_full.png'] = B.strip([soul_jar(f / 8) for f in range(8)])
    meta['item/soul_jar_full.png'] = '{\n  "animation": { "frametime": 3 }\n}\n'

    ws, wsg = waystone_side()
    wt, wtg = waystone_top()
    out['block/waystone_side.png'], out['block/waystone_side_glow.png'] = ws, wsg
    out['block/waystone_top.png'], out['block/waystone_top_glow.png'] = wt, wtg
    side, top, top_glow, front, front_glow = soul_forge()
    out['block/soul_forge_side.png'] = side
    out['block/soul_forge_top.png'] = top
    out['block/soul_forge_top_glow.png'] = top_glow
    out['block/soul_forge_front.png'] = front
    out['block/soul_forge_front_glow.png'] = front_glow
    meta['block/soul_forge_front.png'] = '{\n  "animation": { "frametime": 3 }\n}\n'
    meta['block/soul_forge_front_glow.png'] = '{\n  "animation": { "frametime": 3 }\n}\n'

    out['entity/chicken/gold_chicken.png'] = gold_chicken()
    for name, (pal, parts) in MOBS.items():
        s = humanoid(pal, **parts)
        out[f'entity/{name}/{name}.png'] = s.img
        if s.e.getbbox():
            out[f'entity/{name}/{name}_e.png'] = s.e
    h = shadow_hound()
    out['entity/shadow_hound/shadow_hound.png'] = h.img
    out['entity/shadow_hound/shadow_hound_e.png'] = h.e

    for rel, img in out.items():
        p = os.path.join(tex, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        img.save(p)
        if rel in meta:
            with open(p + '.mcmeta', 'w') as f:
                f.write(meta[rel])
    return out


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    made = build(sys.argv[1])
    print(f'wrote {len(made)} textures to {sys.argv[1]}')
