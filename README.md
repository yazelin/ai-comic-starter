# ai-comic-starter

用 AI 自動出漫畫的產線樣板。目標是 fork 下來、填幾個 secret、按一次 Run workflow
就出一頁，**產線那半還在搬，現在還不能一鍵出圖**（見下一節）。

這是 [neko-tensei](https://github.com/yazelin/neko-tensei) 那條產線的入門版：角色與世界觀
換成一組現成可用的，讓「跑通產線」跟「創作自己的角色」變成兩件事。

想知道為什麼這樣設計、每一步踩過什麼雷，讀 [PLAN.md](PLAN.md)。

## 現在能用到哪裡

> **還差網站與 workflow。** 角色設定、世界觀、產線本體、驗收工具都好了，
> 還沒有網站產生器與 GitHub Actions 的 workflow，所以現在**還不能按一鍵出圖**。
> 進度看 [PLAN.md](PLAN.md)。

已經能用的：

```bash
python3 scripts/test_pipeline.py        # 樣板自我檢查(23 項)
python3 scripts/test_verify_pages.py    # 驗收規則的檢查(8 項)
python3 tools/check.py --cast story/cast.json --chars glitch,blackhole
python3 tools/count_limbs.py story/refs/blackhole.png --views 3 --expect 6
```

`scripts/` 的產線本體已經搬過來並參數化了（角色、repo 名稱、端點預設值全部不寫死），
還差網站產生器與 workflow 才能一鍵出圖。

產線接上之後的流程會是：Fork、填下面那幾個 secret、Actions 按 Run workflow。

## 要填的 secret

**只要兩個，而且是同一把金鑰。**

| 名稱 | 值 |
|---|---|
| `GEMINI_API_KEY` | 你的 Gemini 金鑰（企劃／寫劇本用） |
| `GEMINI_IMAGE_KEY` | 同一把就行（出圖用） |

預設就是 Google 官方端點與官方影像模型，不用另外設 base url 也不用選 provider。

> neko-tensei 那邊的預設值指向作者自架的私有服務，fork 的人不改就會失敗，而且錯誤
> 訊息看起來像金鑰壞了。樣板刻意把預設值翻轉過來，就是為了讓那個陷阱不存在。

想換別的後端才需要動這些：`PLANNER_PROVIDER=openai` 加 `OPENAI_BASE_URL`
（Groq、Ollama、OpenRouter 都是 OpenAI 相容的）。走那條的話注意
`OPENAI_MAX_TOKENS` 預設 32768，模型吃不下就會回空的，而且不會告訴你原因。

## 怎麼開始

這個 repo 是 **template**，按綠色的 **Use this template** 建一個你自己的 repo，
不要用 Fork。

差別是實質的：template 產出的是一個乾淨的獨立 repo（單一 commit、沒有上游關聯），
fork 出來的 repo 頁面上會永遠掛著「forked from」，而且你在自己 repo 下
`gh pr create` 時預設會指向這裡，那個誤觸很難查。

## 換成你自己的角色

改三個檔案，`scripts/` 和 workflow 都不用動：

| 檔案 | 放什麼 |
|---|---|
| `story/cast.json` | 每個角色的設定圖路徑、造型描述、`must`（一定要有的特徵）、`must_not`（一定不能有的）。造型描述有兩種寫法：只有一套衣服的角色用 `sheet`；有多套衣服的用 `identity`（不隨服裝變的特徵）加 `outfit`（這部作品用哪一套）|
| `story/README.md` | 世界觀、連載前提、笑點模板、不要出現的東西 |
| `episodes.json` | 每一話的骨架 |

同一個角色如果還會被別的專案拿去生圖（網站、桌寵、遊戲），把 `identity` 那段在兩邊寫成**逐字相同**的字串，不要各寫各的。樣板附的格莉奇就同時被 [ai-brain-site](https://github.com/yazelin/ai-brain-site) 的 `persona.json` 用著，兩邊漂掉過一次，結果是網站的立繪跟漫畫成品穿的不是同一套衣服。那個 repo 有一支 `scripts/check_character_sync.py` 做逐字比對。

還要放你自己的設定圖到 `story/refs/`。**這一步是整條線最花時間的地方**，不是操作問題，
是創作問題。樣板附了一組現成的角色就是為了讓你先跳過它、把產線跑通一次再回頭做。

## 讓角色不跑偏的三條規矩

這條產線的成敗幾乎都在這裡。完整版看 [cast-lock](https://github.com/yazelin/cast-lock-skill)，
這裡只摘最要緊的三條：

**一、設定圖一定要當參考圖傳進去。** 只給文字描述，角色一定會漂。而且參考圖要先縮到
1024px 的 JPEG，丟原尺寸 PNG 進去的下場是伺服器很久都不回，看起來像連線壞掉。

**二、特徵要寫到字面，不能只寫類別。** 「圓形金牌」會被畫成肉球圖案，「刻著一個貓字
的圓形金牌」才鎖得住。

**三、「沒有什麼」跟「有什麼」一樣要寫死。** 模型會自己補東西。角色沒有的特徵要明文
禁止，例如「頭上是空的，沒有頭帶也沒有任何帽子」。

## 驗收

出圖之後不要只看縮圖就說好。放大到看得清細節，拿 `check.py` 印出來的清單逐項打勾：

```bash
python3 tools/check.py --cast story/cast.json --chars glitch,blackhole
```

**可以數的東西不要用眼睛數。** 幾隻腳、幾個扣子、幾個人，人眼在細長或重疊的物件上很
不可靠。`count_limbs.py` 回傳 exit code，可以寫成「生到過為止」的迴圈：

```bash
python3 tools/count_limbs.py story/refs/blackhole.png --views 3 --expect 6
```

其他工具與用法看 [tools/README.md](tools/README.md)。

## 授權

程式碼 MIT。**角色素材（格莉奇、黑洞先生）是 CC BY-NC**，可以拿去學、拿去改、
拿去跑產線，不可以商用。你 fork 之後換成自己的角色，那些就是你的。
