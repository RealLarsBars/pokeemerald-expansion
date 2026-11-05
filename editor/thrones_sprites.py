"""Game of Thrones character sprites: new medieval looks for the story's cast.

Battle pictures (64x64) are original designs drawn here with sprite_kit (dev-time only,
`python3 thrones_sprites.py` redraws everything into fun/sprites/). The game only needs the
saved pngs. apply() puts them over the base game's files when the Thrones theme is on, and
resetting Fun Modes puts the originals back.
"""
import io
import os

from sprite_kit import Canvas, ramp, to_indexed

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'fun', 'sprites')

# ---------------------------------------------------------------- battle pictures

SKIN = ramp((246, 196, 156))
SKIN_DARK = ramp((196, 136, 96))
PALE = ramp((236, 216, 200))
DEAD = ramp((176, 210, 230))   # the Night King's icy skin
STEEL = ramp((168, 176, 190))
GOLD = ramp((232, 184, 64))
BLACK = ramp((60, 56, 70))
WHITE = ramp((236, 236, 240), 0.6)


def head_colors(skin, hair, extra=None):
    c = {'K': (24, 20, 28), 'S': skin['mid'], 's': skin['lo'], 'z': skin['line'], 'i': hair['hi'], 'H': hair['mid'],
         'h': hair['lo'], 'd': hair['line'], 'E': (30, 26, 40), 'W': (250, 250, 250), 'M': (170, 70, 70)}
    if extra:
        c.update(extra)
    return c


def mir(pts):
    """The same shape on the other side (the figure's middle is between x=31 and x=32)."""
    return [(63 - x, y) for (x, y) in pts]


def mbox(box):
    x0, y0, x1, y1 = box
    return (63 - x1, y0, 63 - x0, y1)


# Arms, drawn for the figure's left (our right); 'down' hangs, 'chest' rests a hand in front,
# 'out' holds something out to the side, 'up' raises it.
ARMS = {
    'down': ([(41, 23), (45, 25), (47, 30), (47, 41), (43, 41), (42, 32), (40, 27)], (42, 39, 48, 45)),
    'chest': ([(41, 23), (45, 25), (47, 31), (45, 37), (36, 37), (36, 33), (42, 32), (40, 27)], (33, 32, 39, 38)),
    'out': ([(41, 23), (45, 25), (51, 30), (49, 35), (43, 31), (40, 27)], (48, 29, 54, 35)),
    'up': ([(41, 23), (45, 24), (49, 17), (49, 11), (45, 11), (44, 18), (40, 27)], (44, 7, 50, 13)),
}


def arm(c, side, pose, sleeve, skin, w=0):
    pts, hand = ARMS[pose]
    pts = [(x + w, y) for (x, y) in pts]
    hand = (hand[0] + w, hand[1], hand[2] + w, hand[3])
    if side == 'left':
        pts, hand = mir(pts), mbox(hand)
    c.poly(pts, sleeve)
    if skin:
        c.ellipse(hand, skin)
    return hand


def body(c, skin, tunic=None, legs=None, boots=None, cloak=None, robe=None, belt=None, sleeves=None,
         left='down', right='down', wide=0, collar=None, gloves=None):
    """A standing figure from the neck down, facing us. The head goes on top at (23, 4)."""
    w = wide
    if cloak:
        c.poly([(21 - w, 21), (42 + w, 21), (47 + w, 25), (52 + w, 61), (11 - w, 61), (16 - w, 25)], cloak)
        for x in (15 - w, 48 + w):
            c.line([(x, 42), (x + (-1 if x < 32 else 1), 60)], cloak['lo'])
    if robe:
        c.poly([(25 - w, 22), (38 + w, 22), (42 + w, 25), (41 + w, 38), (46 + w, 60), (17 - w, 60), (22 - w, 38),
                (21 - w, 25)], robe)
        for x, dx in ((24, -3), (29, -1), (34, 1), (38, 3)):
            c.line([(x, 44), (x + dx, 59)], robe['lo'])
        if boots:
            c.rect((21, 58, 29, 61), boots)
            c.rect((34, 58, 42, 61), boots)
    else:
        c.poly([(24, 42), (31, 42), (31, 56), (24, 56)], legs)
        c.poly([(32, 42), (39, 42), (39, 56), (32, 56)], legs)
        c.poly([(22, 52), (31, 52), (31, 61), (20, 61)], boots)
        c.poly([(32, 52), (41, 52), (43, 61), (32, 61)], boots)
        c.poly([(25 - w, 22), (38 + w, 22), (42 + w, 25), (42 + w, 46), (21 - w, 46), (21 - w, 25)], tunic)
    c.rect((28, 18, 35, 23), skin, light=False)
    if collar:
        c.poly([(24, 21), (39, 21), (42, 25), (21, 25)], collar)
    if belt:
        c.rect((21 - w, 40, 42 + w, 42), belt, light=False)
    sl = sleeves or robe or tunic
    hands = {}
    for side, pose in (('right', right), ('left', left)):
        if pose:
            hands[side] = arm(c, side, pose, sl, gloves or skin, w)
    return hands


def check(art):
    rows = [r for r in art.split('\n') if r]
    assert len(set(map(len, rows))) == 1, [len(r) for r in rows]
    return '\n'.join(rows)


# Heads are 18 wide and drawn last, at (23, 4). Letters: K outline, S/s/z skin, H/h/i/d hair,
# E/W eyes, M mouth. Others are set per character.
MALE_FACE = """
KhHHHSSHHHHHSSHhhK
KhHHSSSSSSSSSSSShK
KhHSSddSSSSSddSShK
.KSSSWESSSSSEWSSK.
.KSSSSSSSzsSSSSSK.
.KSSSSSSSsSSSSSsK.
..KSSSSzMMzSSSSK..
...KSSSSSSSSSsK...
....KKSSSSSSKK....
......KKKKKK......
"""

FEMALE_FACE = """
KhHHHSSHHHHHSSHhhK
KhHHSSSSSSSSSSShhK
KhHSSEESSSSSEESShK
KhHSSWESSSSSEWSShK
.KSSSSSSSzsSSSSSK.
.KSSSSSSSsSSSSSsK.
..KSSSSSzMzSSSSK..
...KSSSSSSSSSsK...
....KKSSSSSSKK....
......KKKKKK......
"""

SHORT_HAIR = """
.....KKKKKKKK.....
...KKHiiHHHHHHKK..
..KHiHHHHHHHHHHhK.
.KHiHHHHHHHHHHHHhK
.KHHHHHhHHHHhHHHhK
KHHHhHHHHHHHHhHHhK
"""

SPIKY_HAIR = """
....K.KKKKKKK.....
...KiKHiiHHHHHK...
..KiHHiHHHHHHHHK..
.KHiHHHHHHHHHHHhK.
.KiHHHHHHHHHHHHHhK
KHHHHhHHHHHHhHHHhK
"""

HERO_HEAD = check(SHORT_HAIR + MALE_FACE)
MAY_HEAD = check(SHORT_HAIR + FEMALE_FACE)
WALLY_HEAD = check(SPIKY_HAIR + MALE_FACE)

MAESTER_HEAD = check("""
.....KKKKKKKK.....
...KKiiiHHHHHHKK..
..KiiHHHHHHHHHHhK.
.KiHHHHHHHHHHHHHhK
.KHHHHhHHHHHhHHHhK
KHHHSSSSSSSSSSShhK
KHHSSSSSSSSSSSSShK
KhSSSddSSSSSddSShK
KhSSSWESSSSSEWSShK
KSSSSSSSzsSSSSSSsK
.KhSSSSSSsSSSSSsK.
.KHhSSSSSSSSSShHK.
.KHHHSHHHHHHSHHhK.
.KHHHHHzMMzHHHHhK.
..KHHHHHHHHHHHhK..
...KHHHHHHHHHhK...
....KKhHHHHhKK....
......KKKKKK......
""")

# Wattson: a hood, bushy white brows and a big white beard, grinning.
THIEF_HEAD = check("""
......KKKKKKKK......
....KKqqOOOOOOKK....
...KqqOOOOOOOOOoK...
..KqOOOOOOOOOOOOoK..
..KqOOKKKKKKKKOOoK..
.KqOOKSSSSSSSSKOooK.
.KqOKHHHSSSSHHHKOoK.
.KqOKSSESSSSESSKOoK.
.KqOKSSSSSzsSSSKOoK.
.KqOKHSSSSsSSSHKOoK.
.KqOKHHHMMMMHHHKOoK.
.KqOKHHHHMMHHHHKOoK.
.KqOOKHHHHHHHHKOOoK.
..KqOKHHHHHHHHKOoK..
..KqOOKHHHHHHKOOoK..
...KKOOKHHHHKOOKK...
.....KKKKKKKKKK.....
""")

# Flannery: a nightcap with a pom-pom, red hair, sleepy eyes.
SLEEPY_HEAD = check("""
...............KK.
.....KKKKKKKK.KWWK
...KKCCcCCCCCKKWWK
..KCCCCCCCcCCCCKK.
.KCCcCCCCCCCCcCCK.
.KWWWWWWWWWWWWWWK.
KHHHHHhHHHHhHHHHhK
KhHHHSSHHHHHSSHhhK
KhHHSSSSSSSSSSShhK
KhHSSSSSSSSSSSSShK
KhHSSddSSSSSddSShK
.KSSSSSSSzsSSSSSK.
.KSSSSSSSsSSSSSsK.
..KSSSSSSMSSSSSK..
...KSSSSSSSSSsK...
....KKSSSSSSKK....
......KKKKKK......
""")

NORMAN_HEAD = check("""
.....KKKKKKKK.....
...KKHHHHHHHHHKK..
..KHHHHHHHHHHHHhK.
.KHHHHHhHHHHHHHHhK
.KHHHHHHHHHHHHHHhK
KHHHhHHHHHHHHHhHhK
KhHHSSSSSSSSSSShhK
KhHSdddSSSSdddSShK
.KSSSWESSSSSEWSSK.
.KSSSSSSSzsSSSSSK.
.KSSSSSSSsSSSSSsK.
..KSSSSzzzzSSSSK..
...KSSSSSSSSSsK...
....KKSSSSSSKK....
......KKKKKK......
""")

# The Night King: bald, icy skin, a crown of ice, glowing eyes.
ICE_HEAD = check("""
..W....W....W.....
..WK..KWK..KWK..W.
..KWK.KWK.KWK..KWK
...KWKKWKKWKK.KWK.
...KbWWbWWbWWWWbK.
..KbbbbbbbbbbbbbK.
.KSSSSSSSSSSSSSSsK
KSSzSSSSSSSSSSzSsK
KSSSSSSSSSSSSSSSsK
KsSSzzzSSSSzzzSSsK
KsSSSWESSSSSEWSssK
.KSSSzSSSzsSSzSSK.
.KsSSSSSSsSSSSSsK.
..KsSSSzzzzSSSsK..
...KsSSSSSSSssK...
....KKsSSSSsKK....
......KKKKKK......
""")

ROXANNE_HEAD = check(SHORT_HAIR + FEMALE_FACE)
WINONA_HEAD = check("""
.....KKKKKKKK.....
...KKHiiHHHHHHKK..
..KHiiHHHHHHHHHhK.
.KHiHHHHHHHHHHHHhK
.KHiHHHHhHHHHHHHhK
KHiHHHhHHHHHHHHHhK
""" + FEMALE_FACE)

BRAWLY_HEAD = check("""
.....KKKKKKKK.....
...KKHiiHHHHHHKK..
..KHiHHHHHHHHHHhK.
.KRRRRRRRRRRRRRRRK
.KrrrrrrrrrrrrrrrK
KHHHhHHHHHHHHhHHhK
KhHHHSSHHHHHSSHhhK
KhHHSSSSSSSSSSSShK
KhHSSddSSSSSddSShK
.KSSSWESSSSSEWSSK.
.KSSSSSSSzsSSSSSK.
.KSSSSSSSsSSSSSsK.
..KSSSSzMMzSSSSK..
...KSSSSSSSSSsK...
....KKSSSSSSKK....
......KKKKKK......
""")

SEER_HEAD = check(SHORT_HAIR + """
KhHHHSSHHHHHSSHhhK
KhHHSSSSSSSSSSShhK
KhHSSSSSSSSSSSSShK
KhHSzzzSSSSSzzzShK
.KSSSSSSSzsSSSSSK.
.KSSSSSSSsSSSSSsK.
..KSSSSSSMSSSSSK..
...KSSSSSSSSSsK...
....KKSSSSSSKK....
......KKKKKK......
""")

TWIN_FACE = check("""
....KKKKKKKK....
..KKHiiHHHHHKK..
.KHiHHHHHHHHHhK.
KHiHHHHHHHHHHHhK
KHHHhHHHHHHhHHhK
KhHHSSHHHHSSHhhK
KhHSSSSSSSSSSShK
KhSSWESSSSEWSShK
.KSSSSSSsSSSSSK.
..KSSSSzMzSSSK..
...KSSSSSSSsK...
....KKSSSSKK....
......KKKK......
""")


def long_hair(c, rp, top=8, bottom=30, half=12):
    """Hair falling behind the head and over the shoulders."""
    l, r = 32 - half, 31 + half
    c.poly([(l + 4, top), (r - 4, top), (r, top + 6), (r + 1, bottom - 3), (r - 2, bottom), (34, bottom - 2),
            (29, bottom - 2), (l + 2, bottom), (l - 1, bottom - 3), (l, top + 6)], rp)
    for x in (l + 2, r - 2):
        c.line([(x, top + 10), (x, bottom - 3)], rp['lo'])


def head(c, art, colors, x=23, y=4):
    c.grid(art, x, y, colors)


# ---------------------------------------------------------------- the cast

def grand_maester():
    """Prof. Birch in the intro: a Grand Maester's grey robe, a chain of many metals, a book."""
    c = Canvas()
    robe = ramp((120, 116, 128))
    body(c, SKIN, robe=robe, boots=ramp((80, 60, 50)), right='down', left='chest', wide=1)
    c.poly([(20, 28), (31, 28), (31, 37), (20, 37)], ramp((132, 44, 40)), light=False)
    c.line([(21, 36), (30, 36)], (236, 220, 176))
    c.ellipse((24, 32, 30, 38), SKIN)
    metals = [GOLD, ramp((96, 96, 108)), STEEL, ramp((204, 112, 60))]
    pts = [(24, 21), (25, 24), (27, 26), (29, 27), (31, 28), (33, 27), (35, 26), (37, 24), (38, 21)]
    for i, (x, y) in enumerate(pts):
        m = metals[i % 4]
        c.grid('ab\nbc', x, y, {'a': m['hi'], 'b': m['mid'], 'c': m['line']})
    head(c, MAESTER_HEAD, head_colors(SKIN, ramp((122, 76, 46))), y=2)
    return c


def sword_down(c, x, top, blade=STEEL, hilt=ramp((90, 60, 40)), guard=GOLD):
    """A sword held point-down in front, hands on the grip at about y=top+3."""
    c.rect((x - 1, top + 9, x + 1, 60), blade, light=False)
    c.dot(x, 61, blade['lo'])
    c.rect((x - 5, top + 7, x + 5, top + 8), guard, light=False)
    c.rect((x - 1, top + 1, x + 1, top + 6), hilt, light=False)
    c.ellipse((x - 2, top - 2, x + 2, top + 1), guard, light=False)


def hand_brooch(c, x, y):
    """The Hand of the King's pin: a little gold hand."""
    c.grid("""
.a.a.
.bbb.
abbbb
.bbc.
..c..""", x, y, {'a': GOLD['hi'], 'b': GOLD['mid'], 'c': GOLD['line']})


def hero(female=False):
    """You and your rival (the Hand): leather, a green cloak, a sword, the Hand's gold pin."""
    c = Canvas()
    leather = ramp((112, 70, 44))
    cloak = ramp((40, 84, 64))
    boots = ramp((60, 44, 40))
    if female:
        long_hair(c, ramp((150, 92, 52)), bottom=28, half=11)
        body(c, SKIN, robe=ramp((150, 36, 52)), boots=boots, cloak=cloak, sleeves=leather,
             belt=ramp((64, 44, 36)), right='down', left='down')
    else:
        body(c, SKIN, tunic=leather, legs=ramp((84, 84, 96)), boots=boots, cloak=cloak,
             belt=ramp((64, 44, 36)), right='down', left='down')
    c.poly([(42, 41), (44, 41), (50, 58), (48, 59)], STEEL, light=False)
    c.rect((40, 38, 46, 39), GOLD, light=False)
    c.rect((42, 35, 43, 37), ramp((90, 60, 40)), light=False)
    hand_brooch(c, 34, 25)
    if female:
        head(c, MAY_HEAD, head_colors(SKIN, ramp((150, 92, 52))))
    else:
        head(c, HERO_HEAD, head_colors(SKIN, ramp((58, 46, 50))))
    return c


def kingsguard():
    """Wally, sworn to the Champion: white cloak, plate armor, sword point-down."""
    c = Canvas()
    plate = ramp((176, 184, 198))
    white = ramp((240, 240, 236), 0.5)
    body(c, SKIN, tunic=plate, legs=ramp((140, 148, 164)), boots=ramp((110, 116, 132)),
         cloak=white, belt=ramp((90, 70, 60)), right='chest', left='chest', collar=white,
         gloves=ramp((150, 156, 172)))
    c.ellipse((16, 21, 25, 28), plate)
    c.ellipse((38, 21, 47, 28), plate)
    sword_down(c, 31, 30)
    c.rect((27, 32, 36, 36), ramp((150, 156, 172)), light=False)
    head(c, WALLY_HEAD, head_colors(SKIN, ramp((140, 196, 96))))
    return c


def roxanne():
    """House Rustboro, Keeper of the Crypts: grey robes, bone white, a skull and a candle."""
    c = Canvas()
    hair = ramp((56, 52, 80))
    c.ellipse((16, 0, 25, 9), hair)   # hair buns
    c.ellipse((38, 0, 47, 9), hair)
    hands = body(c, SKIN, robe=ramp((112, 110, 118)), boots=ramp((60, 56, 60)), right='chest', left='out',
                 collar=ramp((226, 218, 196), 0.6), belt=ramp((226, 218, 196), 0.6))
    # A skull held to the chest, the house sigil.
    x0, y0 = hands['right'][0], hands['right'][1]
    c.grid("""
.KKKKK.
KbbbbbK
KbKbKbK
KbbbbbK
.KbKbK.
..KKK..""", x0 - 1, y0 - 5, {'K': (60, 54, 50), 'b': (232, 224, 204)})
    c.ellipse((x0 + 1, y0 + 2, x0 + 6, y0 + 7), SKIN)
    # A tallow candle for the crypts.
    x0, y0 = hands['left'][0] + 2, hands['left'][1]
    c.rect((x0, y0 - 7, x0 + 2, y0 + 1), ramp((236, 226, 196)), light=False)
    c.ellipse((x0 - 1, y0 - 13, x0 + 3, y0 - 7), ramp((255, 196, 80)))
    c.dot(x0 + 1, y0 - 10, (255, 248, 210))
    c.ellipse(hands['left'], SKIN)
    head(c, ROXANNE_HEAD, head_colors(SKIN, hair))
    return c


def brawly():
    """House Dewford, a reaver captain: salt-stained sea-green leathers, black, a boarding axe."""
    c = Canvas()
    hair = ramp((96, 120, 180))
    leather = ramp((52, 110, 96))
    hands = body(c, SKIN, tunic=leather, legs=ramp((44, 44, 52)), boots=ramp((36, 32, 36)),
                 cloak=ramp((40, 40, 48)), belt=ramp((90, 66, 44)), right='out', left='down', wide=2,
                 sleeves=leather)
    c.line([(24, 24), (38, 40)], ramp((90, 66, 44))['mid'], 2)   # baldric
    # The anchor of his house on the belt buckle.
    c.grid("""
.s.
sss
.s.
s.s
.s.""", 31, 39, {'s': STEEL['hi']})
    # A boarding axe, held out.
    x0, y0 = hands['right'][0], hands['right'][1]
    c.rect((x0 + 2, y0 - 14, x0 + 3, y0 + 14), ramp((110, 76, 48)), light=False)
    c.poly([(x0 + 4, y0 - 14), (x0 + 9, y0 - 17), (x0 + 10, y0 - 8), (x0 + 4, y0 - 9)], STEEL)
    c.ellipse(hands['right'], SKIN)
    head(c, BRAWLY_HEAD, head_colors(SKIN, hair, {'R': (52, 110, 96), 'r': (34, 76, 66)}))
    return c


def spymaster():
    """House Wattson, Master of Whispers: black and silver, a deep hood, a raven."""
    c = Canvas()
    hands = body(c, SKIN, robe=ramp((52, 50, 60)), boots=ramp((30, 30, 36)), cloak=ramp((36, 34, 44)),
                 belt=ramp((180, 184, 196)), right='out', left='down', wide=3)
    x0, y0 = hands['right'][0], hands['right'][1]
    c.grid("""
...KKK.....
..KbbbK....
.KbbWbK....
KyKbbbbK...
.K.KbbbbK..
...KbbbbbK.
...KbbbbbbK
....KbbbbKK
.....KKbKK.
......K.K..""", x0 - 2, y0 - 9, {'K': (16, 14, 22), 'b': (52, 52, 70), 'W': (230, 230, 240), 'y': (130, 130, 140)})
    c.ellipse((x0, y0 + 1, x0 + 6, y0 + 6), SKIN)
    hood = ramp((44, 42, 54))
    head(c, THIEF_HEAD, head_colors(SKIN, WHITE, {'O': hood['mid'], 'o': hood['lo'], 'q': (170, 174, 186)}),
         x=22, y=3)
    return c


def flannery():
    """House Lavaridge, priestess of the dream springs: red and white robes, eyes closed in a vision."""
    c = Canvas()
    hair = ramp((214, 72, 56))
    long_hair(c, hair, top=8, bottom=34, half=13)
    red = ramp((176, 36, 44))
    hands = body(c, SKIN, robe=ramp((236, 230, 222), 0.6), boots=ramp((120, 40, 40)), cloak=red, sleeves=red,
                 right='chest', left='chest', belt=red)
    # The open eye of her house, in gold on the robe.
    c.grid("""
.ggg.
gKrKg
.ggg.""", 29, 44, {'g': GOLD['mid'], 'K': (40, 20, 20), 'r': (176, 36, 44)})
    # A small brazier held in both hands.
    c.poly([(26, 31), (37, 31), (35, 37), (28, 37)], GOLD, light=False)
    c.ellipse((28, 25, 35, 32), ramp((255, 150, 40)))
    c.dot(31, 28, (255, 240, 180))
    c.ellipse((23, 32, 29, 38), SKIN)
    c.ellipse((34, 32, 40, 38), SKIN)
    head(c, SEER_HEAD, head_colors(SKIN, hair))
    return c


def faceless_man():
    """House Petalburg, trained by the faceless men: charcoal grey, a blank white mask in hand."""
    c = Canvas()
    grey = ramp((72, 70, 78))
    hands = body(c, SKIN, robe=grey, boots=ramp((40, 36, 44)), cloak=ramp((52, 50, 58)), right='out', left='down',
                 wide=1, belt=ramp((40, 38, 46)))
    c.ellipse((24, 19, 39, 26), ramp((60, 58, 66)))  # cowl
    x0, y0 = hands['right'][0], hands['right'][1]
    c.grid("""
.KKKKKKKK.
KppppppppK
KppppppppK
KpKKppKKpK
KppppppppK
KpppppqppK
KppppppppK
.KppppppK.
..KppppK..
...KKKK...""", x0 - 2, y0 - 9, {'K': (60, 56, 60), 'p': (240, 236, 228), 'q': (206, 200, 192)})
    c.ellipse((x0, y0 + 1, x0 + 6, y0 + 6), SKIN)
    head(c, NORMAN_HEAD, head_colors(SKIN, ramp((52, 52, 70))))
    return c


def dragon_queen():
    """House Fortree, the Mother of Dragons: silver hair, black and red, a young dragon."""
    c = Canvas()
    hair = ramp((226, 220, 240), 0.6)
    long_hair(c, hair, top=8, bottom=40, half=12)
    hands = body(c, SKIN, robe=ramp((44, 40, 50)), boots=ramp((30, 28, 34)), cloak=ramp((150, 30, 36)),
                 right='out', left='down', belt=ramp((150, 30, 36)))
    c.rect((40, 26, 42, 46), hair, light=False)  # braid
    x0, y0 = hands['right'][0], hands['right'][1]
    c.grid("""
.KK...........
KhhK.....KKK..
KRRRK...KwwwK.
KRERRK.KwwwwK.
.KRRRRKwwwwK..
..KRRRRRRwK...
..KRRRRRRRK...
...KRRRRRRK...
...KRKKRRRRKK.
...KK.KKRRRRRK
.........KKKK.""", x0 - 3, y0 - 10, {'K': (40, 14, 14), 'R': (196, 52, 40), 'E': (255, 220, 60),
                                     'h': (240, 210, 150), 'w': (110, 26, 30)})
    c.ellipse(hands['right'], SKIN)
    head(c, WINONA_HEAD, head_colors(SKIN, hair))
    return c


def sword_twins():
    """House Mossdeep, the Sword Twins: steel and blue, each with a blade from their forge,
    in front of the throne of swords their forge made."""
    c = Canvas()
    iron = ramp((96, 100, 112))
    for i, x in enumerate(range(14, 51, 4)):
        top = 2 + abs(x - 32) // 2 + (i % 2) * 3
        c.rect((x, top, x + 2, 50), iron, light=False)
        c.dot(x + 1, top - 1, iron['hi'])
    c.rect((10, 40, 53, 52), ramp((80, 84, 96)))
    hair = ramp((46, 54, 96))
    for x0, cloth, flip in ((4, ramp((60, 90, 150)), False), (32, ramp((130, 140, 156)), True)):
        sub = Canvas(28, 64)
        sub.poly([(8, 30), (19, 30), (22, 33), (24, 60), (4, 60), (6, 33)], cloth)
        sub.rect((11, 26, 16, 31), SKIN, light=False)
        sub.poly([(18, 31), (22, 33), (24, 44), (20, 44), (19, 38)], cloth)
        sub.poly([(9, 31), (5, 33), (3, 44), (7, 44), (8, 38)], cloth)
        sub.rect((9, 46, 18, 48), ramp((90, 66, 44)), light=False)   # smith's belt
        sub.rect((9, 58, 12, 61), ramp((60, 50, 60)))
        sub.rect((15, 58, 18, 61), ramp((60, 50, 60)))
        # A sword held point-down at the side.
        sub.rect((21, 47, 22, 61), STEEL, light=False)
        sub.rect((19, 45, 24, 46), STEEL, light=False)
        sub.ellipse((19, 42, 24, 47), SKIN)
        sub.ellipse((3, 42, 8, 47), SKIN)
        sub.grid(TWIN_FACE, 6, 15, head_colors(SKIN, hair))
        if flip:
            sub.flip()
        for y in range(64):
            for x in range(28):
                if sub.px[y][x] is not None:
                    c.px[y][x + x0] = sub.px[y][x]
    return c


def night_king():
    """House Sootopolis, Lord of the Long Night: icy skin, a crown of ice, black armor, an ice spear."""
    c = Canvas()
    dark = ramp((52, 56, 76))
    cloak = ramp((36, 40, 56))
    hands = body(c, DEAD, tunic=dark, legs=ramp((44, 48, 64)), boots=ramp((30, 32, 44)), cloak=cloak,
                 belt=ramp((70, 60, 70)), right='out', left='down', sleeves=dark)
    for x in range(12, 52, 4):   # ragged cloak hem
        c.dot(x, 61, None)
        c.dot(x + 1, 61, None)
        c.dot(x, 60, None)
    x0, y0 = hands['right'][0], hands['right'][1]
    ice = ramp((170, 220, 250), 0.7)
    c.rect((x0 + 2, 6, x0 + 3, 61), ice, light=False)
    c.poly([(x0 + 2, 6), (x0 + 3, 6), (x0 + 5, 2), (x0 + 2, -4), (x0, 2)], ice)
    c.ellipse(hands['right'], DEAD)
    head(c, ICE_HEAD, head_colors(DEAD, WHITE, {'W': (220, 245, 255), 'b': (110, 170, 230), 'E': (40, 150, 255)}),
         y=2)
    return c


LABELS = {
    'birch_intro': 'Grand Maester (Birch)', 'brendan': 'You / your Hand', 'may': 'You / your Hand',
    'wally': 'Wally, Kingsguard', 'roxanne': 'Roxanne, Keeper of the Crypts', 'brawly': 'Brawly, reaver captain',
    'wattson': 'Wattson, Master of Whispers', 'flannery': 'Flannery, dream priestess', 'norman': 'Norman, faceless',
    'winona': 'Winona, Mother of Dragons', 'tate_and_liza': 'Tate & Liza, Sword Twins',
    'juan': 'Juan, Lord of the Long Night',
}

FRONT = {
    'birch_intro': (grand_maester, 'graphics/birch_speech/birch.png'),
    'brendan': (hero, 'graphics/trainers/front_pics/brendan.png'),
    'may': (lambda: hero(True), 'graphics/trainers/front_pics/may.png'),
    'wally': (kingsguard, 'graphics/trainers/front_pics/wally.png'),
    'roxanne': (roxanne, 'graphics/trainers/front_pics/leader_roxanne.png'),
    'brawly': (brawly, 'graphics/trainers/front_pics/leader_brawly.png'),
    'wattson': (spymaster, 'graphics/trainers/front_pics/leader_wattson.png'),
    'flannery': (flannery, 'graphics/trainers/front_pics/leader_flannery.png'),
    'norman': (faceless_man, 'graphics/trainers/front_pics/leader_norman.png'),
    'winona': (dragon_queen, 'graphics/trainers/front_pics/leader_winona.png'),
    'tate_and_liza': (sword_twins, 'graphics/trainers/front_pics/leader_tate_and_liza.png'),
    'juan': (night_king, 'graphics/trainers/front_pics/leader_juan.png'),
}


def make_front(name):
    fn, _ = FRONT[name]
    c = fn()
    c.outline()
    return to_indexed(c)




# ---------------------------------------------------------------- walking sprites

# Walking sprites keep the base game's frames (so walking still looks right) and get a new
# costume: colors swapped, plus capes, crowns, hoods and chains painted on. Colors are numbers
# in the character's shared NPC palette, so they stay exactly as the game draws them.
PEOPLE = 'graphics/object_events/pics/people/'
DIRS9 = 'DULDDUULL'   # down, up, left (right is the left frames flipped by the game)


def _frames(im):
    n = im.width // 16
    return [(i, DIRS9[i] if n == 9 else 'DUL'[i]) for i in range(n)]


def _span(im, i, y):
    xs = [x for x in range(16) if im.getpixel((i * 16 + x, y))]
    return (xs[0], xs[-1]) if xs else None


def _top(im, i):
    for y in range(im.height):
        if _span(im, i, y):
            return y
    return 0


def _bottom(im, i):
    for y in range(im.height - 1, -1, -1):
        if _span(im, i, y):
            return y
    return 0


def _put(im, i, x, y, v):
    if 0 <= x < 16 and 0 <= y < im.height:
        im.putpixel((i * 16 + x, y), v)


def _get(im, i, x, y):
    if 0 <= x < 16 and 0 <= y < im.height:
        return im.getpixel((i * 16 + x, y))
    return -1


def cape(im, i, d, tones, shoulder):
    """A cloak hanging from the shoulders: peeking out at the sides from the front, covering the
    back from behind, trailing behind when walking sideways. tones = (light, mid, shade, line)."""
    hi, mid, lo, line = tones
    top, bot = _top(im, i), _bottom(im, i)
    y0, y1 = top + shoulder, bot - 1
    for y in range(y0, y1 + 1):
        sp = _span(im, i, y)
        if not sp:
            continue
        xl, xr = sp
        if d == 'D':
            if y > y0:
                for x, v in ((xl - 1, mid), (xl - 2, line), (xr + 1, lo), (xr + 2, line)):
                    if _get(im, i, x, y) == 0:
                        _put(im, i, x, y, v)
        elif d == 'U':
            if y > y1 - 2:
                continue
            for x in range(xl, xr + 1):
                rel = (x - xl) / max(1, xr - xl)
                v = line if x in (xl, xr) else hi if rel < 0.3 else lo if rel > 0.7 else mid
                if (x - xl) in (4, 8) and y > y0 + 2 and v == mid:
                    v = lo
                _put(im, i, x, y, v)
            for x in (xl - 1, xr + 1):
                if y > y0 and _get(im, i, x, y) == 0:
                    _put(im, i, x, y, line)
        else:
            if y > y0:
                for x, v in ((xr + 1, mid), (xr + 2, line)):
                    if _get(im, i, x, y) == 0:
                        _put(im, i, x, y, v)
    if d == 'U':
        sp = _span(im, i, y1 - 2)
        if sp:
            for x in range(sp[0], sp[1] + 1):
                _put(im, i, x, y1 - 1, line)


def paint(im, i, art, x0, y0, colors):
    for y, row in enumerate(art.strip('\n').split('\n')):
        for x, ch in enumerate(row):
            if ch != '.':
                _put(im, i, x0 + x, y0 + y, colors[ch] if ch in colors else int(ch, 16))


def remap(im, i, mapping, rows=None, cols=None):
    top = _top(im, i)
    for y in range(im.height):
        if rows and not (rows[0] <= y - top <= rows[1]):
            continue
        for x in range(16):
            if cols and not (cols[0] <= x <= cols[1]):
                continue
            v = _get(im, i, x, y)
            if v in mapping:
                _put(im, i, x, y, mapping[v])


def _center(im, i):
    top = _top(im, i)
    sp = _span(im, i, top + 3) or (4, 11)
    return (sp[0] + sp[1] + 1) // 2


def ow_maester(im, i, d):
    """Prof. Birch: the white lab coat becomes a Grand Maester's grey robe, with the chain."""
    remap(im, i, {0xe: 5, 5: 6, 6: 7, 8: 6, 9: 6, 0xa: 7}, rows=(10, 99))
    if d == 'D':
        top = _top(im, i)
        paint(im, i, """
e....e
.b..b.
..eb..""", 5, top + 11, {})


def ow_kingsguard(im, i, d):
    """Wally: plate armor and the white cloak of the Kingsguard."""
    remap(im, i, {0xe: 8, 8: 9, 9: 0xa, 0xb: 9, 0xc: 0xa}, rows=(11, 99))
    cape(im, i, d, (0xe, 0xe, 8, 0xa), 11)


def ow_roxanne(im, i, d):
    """Roxanne, Keeper of the Crypts: pale bone-colored robes."""
    remap(im, i, {5: 0xe, 6: 8, 7: 9}, rows=(12, 99))


def ow_brawly(im, i, d):
    """Brawly, reaver captain: a sea-green cloak."""
    cape(im, i, d, (9, 0xa, 0xa, 0xd), 11)


def ow_thief(im, i, d):
    """Wattson, Master of Whispers: a black hood and cloak."""
    remap(im, i, {0xe: 0xd, 4: 0xd, 2: 0xc, 1: 0xc, 3: 0xd, 0xf: 0xd}, rows=(0, 2))
    if d == 'U':
        remap(im, i, {0xe: 0xd, 2: 0xc, 3: 0xd}, rows=(3, 12))
    else:
        remap(im, i, {0xe: 0xd}, rows=(3, 9), cols=(0, 4))
        remap(im, i, {0xe: 0xd}, rows=(3, 9), cols=(11, 15))
    remap(im, i, {5: 0xd, 6: 0xd, 0xb: 0xc}, rows=(14, 99))
    cape(im, i, d, (0xc, 0xd, 0xd, 0xf), 12)


def ow_flannery(im, i, d):
    """Flannery, dream priestess: white robes and a red cloak."""
    remap(im, i, {0xd: 0xe, 0xf: 0xe, 0xc: 8, 0xa: 6, 9: 0xe}, rows=(13, 99))
    cape(im, i, d, (5, 6, 7, 0xa), 13)


def ow_faceless(im, i, d):
    """Norman: charcoal grey from head to toe."""
    remap(im, i, {0xb: 0xd, 0xc: 0xd, 0xe: 0xc}, rows=(10, 99))
    cape(im, i, d, (0xc, 0xd, 7, 7), 10)


def ow_dragon_queen(im, i, d):
    """Winona: silver hair, black dress and a red cloak."""
    remap(im, i, {5: 0xb}, rows=(0, 9))
    remap(im, i, {5: 6, 0xb: 6, 0xc: 7}, rows=(12, 99))
    cape(im, i, d, (8, 9, 0xa, 7), 12)


def ow_twin(im, i, d):
    """Tate and Liza, the Sword Twins: steel-blue cloaks."""
    cape(im, i, d, (8, 9, 0xa, 0xf), 12)


def ow_night_king(im, i, d):
    """Juan: icy skin, an ice crown and a black cloak."""
    remap(im, i, {1: 0xe, 2: 0xb, 3: 5}, rows=(0, 12))
    remap(im, i, {0xb: 0xe, 0xc: 5, 0xd: 6}, rows=(0, 4))
    top, cx = _top(im, i), _center(im, i)
    paint(im, i, """
e..e..e.e
5e.5ee.e5""", cx - 4, top - 2, {})
    remap(im, i, {0xe: 6, 9: 6, 0xa: 7, 0xd: 7}, rows=(12, 99))
    cape(im, i, d, (6, 7, 7, 0xf), 12)


# Which sheet each costume goes on, and its NPC palette (the same one the game already uses).
OW = {
    'prof_birch': (ow_maester, PEOPLE + 'prof_birch.png'),
    'wally': (ow_kingsguard, PEOPLE + 'wally.png'),
    'roxanne': (ow_roxanne, PEOPLE + 'gym_leaders/roxanne.png'),
    'brawly': (ow_brawly, PEOPLE + 'gym_leaders/brawly.png'),
    'wattson': (ow_thief, PEOPLE + 'gym_leaders/wattson.png'),
    'flannery': (ow_flannery, PEOPLE + 'gym_leaders/flannery.png'),
    'norman': (ow_faceless, PEOPLE + 'gym_leaders/norman.png'),
    'winona': (ow_dragon_queen, PEOPLE + 'gym_leaders/winona.png'),
    'tate': (ow_twin, PEOPLE + 'gym_leaders/tate.png'),
    'liza': (ow_twin, PEOPLE + 'gym_leaders/liza.png'),
    'juan': (ow_night_king, PEOPLE + 'gym_leaders/juan.png'),
}


def _base_bytes(rel):
    """The base game's file, even when the Thrones sprites are on (so they are never painted twice)."""
    import subprocess
    try:
        return subprocess.run(['git', 'show', 'HEAD:' + rel], cwd=os.path.join(HERE, '..'), capture_output=True,
                              check=True).stdout
    except Exception:
        with open(os.path.join(HERE, '..', rel), 'rb') as f:
            return f.read()


def make_ow(name):
    from PIL import Image
    fn, src = OW[name]
    im = Image.open(io.BytesIO(_base_bytes(src)))
    im.load()
    im = im.copy()
    for i, d in _frames(im):
        fn(im, i, d)
    return im


# ---------------------------------------------------------------- saving and applying

def targets():
    """(saved png, game file) for every sprite."""
    out = [(name + '.png', path) for name, (_, path) in FRONT.items()]
    out += [('ow_' + name + '.png', path) for name, (_, path) in OW.items()]
    return out


def make_all():
    os.makedirs(OUT, exist_ok=True)
    for name in FRONT:
        make_front(name).save(os.path.join(OUT, name + '.png'), bits=4)
    for name in OW:
        make_ow(name).save(os.path.join(OUT, 'ow_' + name + '.png'), bits=4)


def preview(path, scale=3):
    """One picture of the whole cast: battle pictures on top, walking sprites (before/after) below."""
    from PIL import Image, ImageDraw
    names = list(FRONT)
    cols = 6
    rows = (len(names) + cols - 1) // cols
    cell = 64 * scale + 8
    lab = 14
    ow_h = 32 * scale + 6
    w = cols * cell + 8
    h = rows * (cell + lab) + 8 + 14 + len(OW) * ow_h
    im = Image.new('RGB', (max(w, 2 * 144 * scale + 24), h), (115, 197, 164))
    d = ImageDraw.Draw(im)
    for k, name in enumerate(names):
        pic = Image.open(os.path.join(OUT, name + '.png')).convert('RGB').resize((64 * scale, 64 * scale), 0)
        x, y = 8 + (k % cols) * cell, 8 + (k // cols) * (cell + lab)
        im.paste(pic, (x, y))
        d.text((x, y + 64 * scale + 2), LABELS.get(name, name), fill=(20, 40, 30))
    y = rows * (cell + lab) + 8 + 14
    d.text((8, y - 12), 'walking sprites: before / after', fill=(20, 40, 30))
    for name, (_, src) in OW.items():
        before = Image.open(io.BytesIO(_base_bytes(src))).convert('RGB')
        after = Image.open(os.path.join(OUT, 'ow_' + name + '.png')).convert('RGB')
        for k, pic in enumerate((before, after)):
            pic = pic.resize((pic.width * scale, pic.height * scale), 0)
            im.paste(pic, (8 + k * (144 * scale + 8), y))
        y += ow_h
    im.save(path)
    return path


def apply(ov):
    """Puts the Thrones sprites over the base game's. Returns report lines."""
    for saved, path in targets():
        with open(os.path.join(OUT, saved), 'rb') as f:
            ov.write_bytes(path, f.read())
    return ['New medieval sprites for the Grand Maester (Prof. Birch), you and your Hand, Wally the Kingsguard '
            'and all eight House Gym leaders (battle pictures and walking sprites).']


if __name__ == '__main__':
    make_all()
