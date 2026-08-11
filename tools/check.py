#!/usr/bin/env python3
"""印出這一頁的驗收清單,逐項對照生出來的圖。

    python3 check.py --cast story/cast.json --chars uncle,xiaobai

這是整個技能唯一真正擋得住漂移的一關,而且只能用眼睛。
放大到看得清細節再對,縮圖看不出金牌上的字有沒有消失。

只用標準函式庫。
"""
import argparse
import pathlib
import sys

# Windows 主控台預設是地區碼頁(zh-TW 是 cp950),印繁體中文或導向檔案時會
# UnicodeEncodeError。Python 3.7+ 可以直接改。
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding='utf-8')
    except (AttributeError, ValueError):   # 已被接管或不支援就算了
        pass

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from build import load_cast, pick, pick_world   # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser(description='印出出圖後的逐項驗收清單')
    ap.add_argument('--cast', required=True)
    ap.add_argument('--chars', required=True)
    ap.add_argument('--world', default='')
    a = ap.parse_args(argv)

    data, _root = load_cast(a.cast)
    chosen = pick(data, [k.strip() for k in a.chars.split(',') if k.strip()])
    world = pick_world(data, [k.strip() for k in a.world.split(',') if k.strip()])

    print('出圖驗收清單——放大看,縮圖看不出細節\n')
    n = 0
    for _k, w in world:
        print(f"■ {w.get('name') or _k}(場景/道具)")
        for m in w.get('must') or []:
            n += 1
            print(f'  [ ] {m}')
        for x in w.get('must_not') or []:
            n += 1
            print(f'  [ ] 沒有出現：{x}')
        print()
    for _k, c in chosen:
        print(f"■ {c.get('name') or _k}")
        for m in c.get('must') or []:
            n += 1
            print(f'  [ ] {m}')
        for x in c.get('must_not') or []:
            n += 1
            print(f'  [ ] 沒有出現：{x}')
        print()

    rules = data.get('global_rules') or []
    if rules:
        print('■ 全域規則')
        for r in rules:
            n += 1
            print(f'  [ ] {r}')
        print()

    print('■ 最後一項,也是最常漏的')
    print('  [ ] 這張圖有沒有照描述畫？（不是「劇情對不對」——'
          '描述完全正確但圖沒畫出來的情況真的發生過）')
    print(f'\n共 {n + 1} 項。任何一項打不了勾就重生這一張,不要將就。')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
