#!/usr/bin/env python3
"""生圖 prompt 的單一來源。pipeline 與人工重跑共用同一份,別各寫一份。

規則的完整說明在 story/README.md。這裡是那些規則的可執行版本。

**設定資料本身不寫在這裡,一律讀 story/cast.json。** 這個檔只負責組裝。
分成兩份手寫的下場已經發生過一次:cast.json 寫「樹在爪上」,這裡的 SHEET
跟著寫成別的東西,而正典上根本不是那樣——模型很聽話
地照錯的描述畫,通行證就漂成了掛著繩子的金懷錶。
"""
import json
import pathlib

CAST_PATH = pathlib.Path(__file__).parent.parent / 'story' / 'cast.json'
_CAST = json.loads(CAST_PATH.read_text('utf-8'))

# cast.json 的圖片路徑以 root 為基準(root 相對於 cast.json 自己的位置),
# 這個專案裡等於 repo 根目錄,跟 REF 一直以來的慣例相同。
_BASE = (CAST_PATH.parent / _CAST.get('root', '.')).resolve()

# 參考圖。image 1 永遠是第一話成品頁,鎖畫風、上墨感與手寫黑體字;
# 之後接這一格要鎖的道具/場景,再接出場角色的設定圖。光靠文字描述會漂——
# 只寫「圓形金牌」模型會自己決定上面刻什麼,所以設定圖一定要傳。
REF = {'style': (_CAST['style_ref']['path'], _CAST['style_ref']['desc']),
       'balloons': (_CAST['balloon_ref']['path'], _CAST['balloon_ref']['desc'])}
# cover_ref 是「已經定案的封面版型」,第一話出來之前沒有那種東西,剛 fork 的人
# 也不會有。沒有就退回用 style_ref 當封面的畫風錨,不要讓整條線在這裡炸掉。
_cover = _CAST.get('cover_ref') or _CAST['style_ref']
REF['cover_style'] = (_cover['path'], _cover['desc'])
for _k, _v in list(_CAST['cast'].items()) + list(_CAST.get('world', {}).items()):
    REF[_k] = (_v['ref'], _v['desc'])

# 哪些 key 是道具/場景(而不是角色)。page_refs 與道具段都靠這個分流。
WORLD_KEYS = tuple(_CAST.get('world', {}))

SHAPES = {'SHOUT', 'OVAL', 'WEAK', 'TREMBLE', 'THOUGHT', 'DEMON', 'CAPTION'}

BASE = """Same art style as reference image 1: flat cel-shaded anime, clean confident line art, flat colour blocks with minimal gradients, cool night lighting from screens and neon. No painterly texture, no 3D render look. Vertical manga page, THREE horizontal panels stacked top to bottom, separated by thin white gutters, portrait aspect ratio 2:3."""

def _sheet_of(c):
    """角色的完整造型描述。

    格莉奇有兩套衣服,所以她的描述拆成 identity(不隨服裝變)加 outfit(這部作品
    用哪一套);identity 那段跟 ai-brain-site 的 persona.json 逐字相同,由
    ai-brain-site 的 scripts/check_character_sync.py 把關。黑洞先生只有一套,還是單一個 sheet。
    """
    if c.get('identity'):
        return f"{c['identity']}\n{c.get('outfit', '')}".rstrip()
    return c.get('sheet', '')


SHEET = "\n".join(
    ["CHARACTER SHEET - the model sheets provided as reference images are the authority."
     " Copy every listed feature; a character is wrong if any of these is missing."]
    + [f"- {t}" for t in (_sheet_of(v) for v in _CAST['cast'].values()) if t])

# 「回憶／前世」那類需要另一套畫風的區塊。整段從 cast.json 的 past_block 讀,
# 沒設就是空的。這是每部作品自己的東西,不該寫死在程式裡。
PAST = _CAST.get('past_block', '')

SHAPES_BLOCK = """BALLOON SHAPES - each line below names its own balloon shape. Draw that exact shape; do NOT default every balloon to a rounded rectangle. Hand-inked manga feel, slightly irregular outlines, never a perfect geometric shape.
One of the reference images is a chart of these seven shapes drawn EMPTY on white - copy the silhouettes from that chart, it is the authority for what each shape looks like. Do NOT draw the chart itself into the page, and do NOT copy its empty balloons as extra balloons; use it only as the shape reference for the balloons listed below.
- SHOUT BALLOON: spiky explosion burst with sharp jagged points all around, thick black outline, large bold text.
- OVAL BALLOON: soft hand-drawn organic oval, thin black outline, with a short curved tail pointing at the speaker.
- WEAK BALLOON: small squashed oval with a thin wobbly or dashed outline, small text, deflated feeling.
- TREMBLE BALLOON: oval whose outline shivers in a wavy zigzag, for shock or fear.
- THOUGHT BALLOON: fluffy cloud shape with scalloped edges, tail made of three shrinking circles.
- DEMON BALLOON: black-filled balloon with white text and a ragged spiked edge, heavy and oppressive.
- CAPTION BOX: plain straight-cornered rectangle, the only right-angled box on the page."""

RULES = """DIALOGUE RULES - the most important part, follow exactly:
- All text is TRADITIONAL CHINESE (zh-TW, Taiwan). Copy each string CHARACTER BY CHARACTER exactly as given. Never simplify a character, never substitute a similar-looking character, never invent extra characters, never leave a character out.
- The text allowed in the whole image is exactly these three things: (1) the dialogue listed below; (2) lettering that belongs to a character's own design as described in the CHARACTER SHEET above (a badge, a patch, a screen they wear); (3) in-world English UI text that a PANEL description explicitly asks for - screens, holographic displays, progress bars, banners, signboards. Draw (3) exactly as the panel description spells it, in plain Latin letters, as part of the scenery.
- Nothing else: no sound effects, no signature, no watermark, no page numbers, and never an English translation or transcription of the Chinese dialogue.
- Keep balloons clear of the characters' faces.
- EVERY balloon is labelled "from <name>". Place that balloon next to THAT character and point its tail at THAT character. Readers work out who is speaking from where the balloon sits, so a balloon floating above the wrong character re-assigns the line to someone else - the page then reads as if a different character said it, even though every character is drawn correctly.
- When a line comes from a character marked "speaks from off-panel", put that balloon at the panel edge on the side that character would be standing on, with its tail pointing off the panel - never at one of the visible characters.
- If two characters speak in one panel, keep their balloons on their own sides; do not stack both balloons over the same character."""

REMINDER = ("FINAL CHECK before you draw: (1) the balloons on this page must NOT all be the same shape. "
            "Each balloon above is labelled SHOUT / OVAL / WEAK / TREMBLE / THOUGHT / DEMON / CAPTION - "
            "draw exactly that shape for each one. A page where every balloon is a rounded rectangle is wrong. "
            "(2) walk the balloons one by one and check each one sits beside the character named in its "
            "\"from <name>\" label, with the tail pointing at that character.")


COVER_RULES = """COVER TEXT RULES - the cover carries lettering, follow exactly:
- All text is TRADITIONAL CHINESE (zh-TW, Taiwan). Copy each string CHARACTER BY CHARACTER exactly as given. Never simplify a character, never substitute a similar-looking character, never invent extra characters, never leave a character out.
- The ONLY text on the cover is the title lockup, the character name tags and the bottom episode band described below, plus any lettering that belongs to a character's own design (see the CHARACTER SHEET). No tagline, no author name, no watermark, no signature, no English.
- Lettering style follows reference image 2 and the layout description in the panel body."""


# 角色卡完全沒有文字。封面有文字,但沒有對話框——那是兩件事,別混在一起。
# 從 cast.json 推導,不寫死任何一個角色的名字:name 只要是班底裡的鍵,
# 就代表這次在畫角色卡。fork 的人換角色之後不用回來改這裡。
NO_TEXT = frozenset(_CAST['cast'])
NO_BALLOONS = NO_TEXT | {'cover'}


def world_block(keys):
    """這一格要鎖的道具/場景。沒有就回 None。

    順序上排在 CHARACTER SHEET 之前:場景與道具決定這一格長什麼樣,角色是
    放進去的東西(照 comic-studio 的 world 庫慣例)。
    """
    items = [_CAST['world'][k]['sheet'] for k in keys if k in WORLD_KEYS]
    if not items:
        return None
    return ("PROPS AND PLACES - the reference images are the authority for these."
            " Copy them exactly; they must look the same in every panel and every episode.\n"
            + "\n".join(f"- {s}" for s in items))


def build_prompt(name, keys, body):
    """組一頁的完整 prompt。name 在 NO_TEXT 裡的頁面沒有對白也沒有對話框。"""
    manifest = "REFERENCE IMAGES:\n" + "\n".join(
        f"- image {i + 1}: {REF[k][1]}" for i, k in enumerate(keys))
    sheet = SHEET + PAST if 'past' in keys else SHEET
    parts = [BASE, manifest]
    world = world_block(keys)
    if world:
        parts.append(world)
    parts.append(sheet)
    if name not in NO_BALLOONS:
        parts += [SHAPES_BLOCK, RULES]
    elif name not in NO_TEXT:
        parts.append(COVER_RULES)          # 有字、沒有對話框
    out = "\n\n".join(parts) + "\n\n" + body
    if name not in NO_BALLOONS:
        out += "\n\n" + REMINDER
    return out
