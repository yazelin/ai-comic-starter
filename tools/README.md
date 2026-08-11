# tools

這裡的三支腳本是從別的 repo 複製過來的，因為 fork 這個樣板的人機器上不會裝那些技能，
而驗收那一段沒有它們跑不了。**上游改了要記得同步。**

| 檔案 | 上游 | 做什麼 |
|---|---|---|
| `build.py` | [cast-lock](https://github.com/yazelin/cast-lock-skill) | 從 `cast.json` 組出 prompt 與參考圖清單 |
| `check.py` | 同上 | 印出這一頁的驗收清單，逐項打勾 |
| `count_limbs.py` | paper-puppet | 機械地數同色末端物件（幾隻腳、幾隻靴） |

用法：

```bash
python3 tools/build.py --cast story/cast.json --chars glitch,blackhole --refs-only
python3 tools/check.py --cast story/cast.json --chars glitch,blackhole
python3 tools/count_limbs.py story/refs/blackhole.png --views 3 --expect 6
```

`count_limbs.py` 回傳 exit code，可以直接接進 CI 或寫成「生到過為止」的迴圈。
