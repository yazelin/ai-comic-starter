#!/usr/bin/env python3
"""數設定圖上有幾隻腳（或任何一組同色、排成一列的末端物件）。

    python3 count_limbs.py sheet.png --expect 6
    python3 count_limbs.py sheet.png --expect 6 --views 3   # 三視圖,每個視圖各數

為什麼要有這支：細長、重疊、深色的東西用眼睛數不準。同一份設定圖我數過三次，
錯了兩次，兩次都是別人看出來的。可數的東西要用機械的方式數。

作法不是數「靴子」這個整體（靴子會互相接觸，連通塊會黏成一坨），而是沿著一條
水平掃描線數「深色線段」。掃描線放在靴筒的高度：那裡各隻腿還沒併攏，而且已經
在靴子上，不會把褲管跟裸腿算成不同東西。

只適用於淺色背景的設定圖。實拍或暗場景的分鏡格請改用 vision 驗收。
"""
import argparse

import numpy as np
from PIL import Image


def dark_runs(row, min_len):
    """回傳這一列裡連續為 True 的線段 (起, 迄)，短於 min_len 的忽略。"""
    runs, start = [], None
    for i, v in enumerate(row):
        if v and start is None:
            start = i
        elif not v and start is not None:
            if i - start >= min_len:
                runs.append((start, i))
            start = None
    if start is not None and len(row) - start >= min_len:
        runs.append((start, len(row)))
    return runs


def count_in_band(mask, y0, y1, min_len):
    """在 y0..y1 之間逐列數線段，取出現最多次的那個數字。

    取眾數而不是取某一列，是因為單一列可能剛好切在兩隻腿交疊的位置。
    """
    counts = {}
    for y in range(y0, y1):
        n = len(dark_runs(mask[y], min_len))
        counts[n] = counts.get(n, 0) + 1
    if not counts:
        return 0, {}
    best = max(counts.items(), key=lambda kv: (kv[1], kv[0]))[0]
    return best, counts


def analyse(path, views=1, dark=0.35, expect=None):
    im = Image.open(path).convert("RGB")
    a = np.asarray(im).astype(int)
    h, w, _ = a.shape
    mask = a.sum(2) < 765 * dark          # 明顯的深色（靴子、深色布料）
    ys = np.where(mask.any(1))[0]
    if len(ys) == 0:
        raise SystemExit("整張圖找不到深色物件")
    top, bot = int(ys.min()), int(ys.max())

    results = []
    for v in range(views):
        x0, x1 = int(w * v / views), int(w * (v + 1) / views)
        sub = mask[:, x0:x1]
        sy = np.where(sub.any(1))[0]
        if len(sy) == 0:
            results.append((0, {}))
            continue
        # 掃描帶放在最底部往上 6% 到 14% 的位置：靴筒高度
        b = int(sy.max())
        band = (max(0, b - int((b - sy.min()) * 0.14)), max(1, b - int((b - sy.min()) * 0.06)))
        n, hist = count_in_band(sub, band[0], band[1], min_len=max(4, (x1 - x0) // 60))
        results.append((n, hist))

    print(f"{path}  {w}x{h}  深色範圍 y {top}-{bot}")
    ok = True
    for i, (n, hist) in enumerate(results):
        label = f"視圖 {i + 1}" if views > 1 else "整張"
        spread = " ".join(f"{k}×{v}" for k, v in sorted(hist.items()))
        flag = ""
        if expect is not None:
            good = n == expect
            ok &= good
            flag = "  OK" if good else f"  <== 預期 {expect}"
        print(f"  {label}: {n}{flag}    (逐列分佈 {spread})")
    return ok


def main():
    p = argparse.ArgumentParser()
    p.add_argument("image")
    p.add_argument("--expect", type=int, help="每個視圖應該有幾隻")
    p.add_argument("--views", type=int, default=1, help="橫向切成幾個視圖各自數")
    p.add_argument("--dark", type=float, default=0.35, help="深色門檻 0-1,越大抓越多")
    a = p.parse_args()
    ok = analyse(a.image, a.views, a.dark, a.expect)
    raise SystemExit(0 if ok else 1)


def demo():
    """自我檢查:白底畫六根黑柱,底部兩根互相接觸。
    連通塊會把接觸的兩根算成一個,掃描線法必須仍然數出六根。"""
    a = np.full((200, 300, 3), 255, np.uint8)
    xs = [20, 60, 100, 145, 190, 235]
    for i, x in enumerate(xs):
        w = 26 if i < 4 else 30
        a[120:190, x:x + w] = 20
    a[185:190, 190:265] = 20          # 讓最後兩根在最底部黏在一起
    Image.fromarray(a).save("/tmp/_count_demo.png")
    mask = a.sum(2) < 765 * 0.35
    n, hist = count_in_band(mask, 150, 180, min_len=5)
    assert n == 6, (n, hist)
    # 底部那條黏合帶會讓數字掉到 4,證明掃描線位置很重要
    n2, _ = count_in_band(mask, 186, 189, min_len=5)
    assert n2 < 6, n2
    print(f"demo ok:靴筒高度數出 6 根;貼地那一列因為黏在一起只數到 {n2},"
          f"所以掃描帶不能放在最底部")


if __name__ == "__main__":
    import sys
    if "--demo" in sys.argv:
        demo()
    else:
        main()
