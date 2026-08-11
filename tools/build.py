#!/usr/bin/env python3
"""從專案的 cast.json 組出生圖 prompt,或印出要傳的參考圖路徑。

    python3 build.py --cast story/cast.json --chars uncle,xiaobai --body panel.txt
    python3 build.py --cast story/cast.json --chars uncle,xiaobai --refs-only

參考圖第一張永遠是畫風錨(style_ref),之後才接該頁出場角色的設定圖。
順序有意義——prompt 裡的 REFERENCE IMAGES 清單是按這個順序標號的,
模型靠標號對上「image 2 是誰」。

只用標準函式庫。
"""
import argparse
import json
import pathlib
import sys

# Windows 主控台預設是地區碼頁(zh-TW 是 cp950),印繁體中文或導向檔案時會
# UnicodeEncodeError。Python 3.7+ 可以直接改。
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding='utf-8')
    except (AttributeError, ValueError):   # 已被接管或不支援就算了
        pass


def load_cast(path):
    """讀 cast.json,回 (資料, 圖片路徑的基準目錄)。

    基準目錄預設是 cast.json 自己的所在目錄;要指到別處就在 cast.json 裡加
    "root": "..",相對於 cast.json 的位置解析。**不要用目錄名猜**——猜錯會
    組出一份路徑全錯的 prompt,而錯誤訊息看起來像是圖不見了。
    """
    p = pathlib.Path(path)
    data = json.loads(p.read_text('utf-8'))
    root = (p.parent / data.get('root', '.')).resolve()
    return data, root


def resolve(root, rel):
    """cast.json 裡的路徑相對於專案根目錄。回絕對路徑,不存在就大聲說。"""
    f = (root / rel).resolve()
    if not f.is_file():
        sys.exit(f'參考圖不存在:{rel}（找的是 {f}）')
    return f


def pick(data, keys):
    """挑出要用的角色,順序照使用者給的。不認識的 key 直接停下來。"""
    cast = data.get('cast') or {}
    out = []
    for k in keys:
        if k not in cast:
            sys.exit(f'cast.json 裡沒有這個角色:{k}（有的是 {", ".join(sorted(cast))}）')
        out.append((k, cast[k]))
    return out


def pick_world(data, keys):
    """挑出這一格要用的場景/道具。跟 pick() 同樣不認識就停下來。"""
    world = data.get('world') or {}
    out = []
    for k in keys:
        if k not in world:
            sys.exit(f'cast.json 裡沒有這個場景/道具:{k}（有的是 {", ".join(sorted(world))}）')
        out.append((k, world[k]))
    return out


def ref_paths(data, root, chosen, world=()):
    """順序寫死:畫風錨 → 場景/道具 → 角色。

    場景排在角色前面,是因為場景決定這一格長什麼樣;角色是放進去的東西。
    參考圖張數有上限時,先被擠掉的應該是表情/動作那類補充圖,不是場景鎖或立繪。
    """
    style = data.get('style_ref')
    paths = [resolve(root, style['path'])] if style else []
    paths += [resolve(root, w['ref']) for _k, w in world]
    return paths + [resolve(root, c['ref']) for _k, c in chosen]


def build(data, chosen, body, world=()):
    style = data.get('style_ref')
    lines = []

    lines.append('REFERENCE IMAGES:')
    i = 1
    if style:
        lines.append(f"- image {i}: {style.get('desc', 'style anchor')}")
        i += 1
    for _k, w in world:
        lines.append(f"- image {i}: {w.get('desc') or w.get('name') or 'scene/prop reference'}")
        i += 1
    for _k, c in chosen:
        lines.append(f"- image {i}: {c.get('desc') or c.get('name') or 'character model sheet'}")
        i += 1

    if world:
        lines.append('')
        lines.append('SCENE / PROP SHEET — 場景與道具照參考圖畫,不要每一格重新想一次。')
        for _k, w in world:
            lines.append(f"- {w.get('name') or _k}:")
            for m in w.get('must') or []:
                lines.append(f'  - {m}')
            for n in w.get('must_not') or []:
                lines.append(f'  - 【不可以】{n}')

    lines.append('')
    lines.append('CHARACTER SHEET — 參考圖裡的設定圖是準的。下面每一項都要照做,'
                 '少一項就是畫錯了。')
    for _k, c in chosen:
        name = c.get('name') or _k
        lines.append(f'- {name}:')
        for m in c.get('must') or []:
            lines.append(f'  - {m}')
        for n in c.get('must_not') or []:
            # 「沒有什麼」要跟「有什麼」一樣明講,否則模型會自己補上去
            lines.append(f'  - 【不可以】{n}')

    rules = data.get('global_rules') or []
    if rules:
        lines.append('')
        lines.append('GLOBAL RULES:')
        lines += [f'- {r}' for r in rules]

    if body:
        lines.append('')
        lines.append(body.rstrip())
    return '\n'.join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description='組生圖 prompt / 印參考圖路徑')
    ap.add_argument('--cast', required=True, help='專案的 cast.json')
    ap.add_argument('--chars', required=True, help='這一頁出場的角色,逗號分隔')
    ap.add_argument('--world', default='', help='這一格的場景/道具,逗號分隔(cast.json 的 world 區塊)')
    ap.add_argument('--body', help='畫面描述的檔案;省略就只出設定區塊')
    ap.add_argument('--refs-only', action='store_true',
                    help='只印參考圖路徑,一行一個,餵給生圖工具用')
    a = ap.parse_args(argv)

    data, root = load_cast(a.cast)
    keys = [k.strip() for k in a.chars.split(',') if k.strip()]
    if not keys:
        sys.exit('--chars 是空的')
    chosen = pick(data, keys)
    world = pick_world(data, [k.strip() for k in a.world.split(',') if k.strip()])

    if a.refs_only:
        # 一行一個。不要用空白分隔——Windows 路徑常有空白,Linux 上也一樣會壞。
        # 未加引號的 $(...) 仍然會逐行拆成獨立參數,原本的用法不受影響。
        for f in ref_paths(data, root, chosen, world):
            print(f)
        return 0

    paths = ref_paths(data, root, chosen, world)   # 先驗檔案都在,不然組出來的 prompt 是廢的
    body = pathlib.Path(a.body).read_text('utf-8') if a.body else ''
    print(build(data, chosen, body, world))

    # 印到 stderr:prompt 本身用 $(...) 取仍然乾淨,但人一定看得到這段。
    # 只把 prompt 貼進純文字生圖工具是這套方法最常見的失敗方式——
    # 參考圖沒傳,角色照樣漂,而使用者以為自己照做了。
    print('', file=sys.stderr)
    print('這段 prompt 本身不夠。你必須同時把下面這幾張圖當參考圖傳給生圖工具,',
          file=sys.stderr)
    print('順序不能變(image 1 是畫風錨,之後依序對應 prompt 裡的 REFERENCE IMAGES):',
          file=sys.stderr)
    for i, f in enumerate(paths, 1):
        print(f'  image {i}: {f}', file=sys.stderr)
    print('', file=sys.stderr)
    print('後端必須支援多參考圖的 image-edit。純文字生圖用不了這套方法。',
          file=sys.stderr)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
