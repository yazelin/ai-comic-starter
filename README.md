# ai-comic-starter

用 AI 自動出漫畫的產線樣板。目標是 fork 下來、填幾個 secret、按一次 Run workflow
就出一頁，**產線那半還在搬，現在還不能一鍵出圖**（見下一節）。

這是 [neko-tensei](https://github.com/yazelin/neko-tensei) 那條產線的入門版：角色與世界觀
換成一組現成可用的，讓「跑通產線」跟「創作自己的角色」變成兩件事。

想知道為什麼這樣設計、每一步踩過什麼雷，讀 [PLAN.md](PLAN.md)。

## 現在能用到哪裡

> **產線還沒接上。** 角色設定、世界觀、驗收工具都好了，但 `scripts/` 與
> `.github/workflows/` 還沒從 neko-tensei 搬過來，所以現在**還不能按一鍵出圖**。
> 進度看 [PLAN.md](PLAN.md)。

已經能用的是設定與驗收那一半：

```bash
python3 tools/build.py --cast story/cast.json --chars glitch,blackhole --refs-only
python3 tools/check.py --cast story/cast.json --chars glitch,blackhole
python3 tools/count_limbs.py story/refs/blackhole.png --views 3 --expect 6
```

產線接上之後的流程會是：Fork、填下面那幾個 secret、Actions 按 Run workflow。

## 要填的 secret

| 名稱 | 值 | 說明 |
|---|---|---|
| `GEMINI_API_KEY` | 你的 Gemini 金鑰 | 企劃（寫劇本）用 |
| `GEMINI_WEB_BASE_URL` | `https://generativelanguage.googleapis.com` | **一定要填**，見下方 |
| `IMAGE_PROVIDER` | `gemini` | **一定要填**，見下方 |
| `GEMINI_IMAGE_KEY` | 你的 Gemini 金鑰 | 出圖用，可以跟上面同一把 |

### 兩個你一定會踩的坑

**`GEMINI_WEB_BASE_URL` 不填會打到別人的私有中繼站。** 這個變數的預設值指向原作者
自架的服務，你沒有那把鑰匙，會直接失敗而且錯誤訊息看起來像金鑰壞了。填上官方端點
`https://generativelanguage.googleapis.com` 就好，腳本組出來的路徑本來就是官方那個形狀。

**`IMAGE_PROVIDER` 預設是 `codex`，那也是私有服務。** 一定要改成 `gemini`。

還有一個比較隱蔽的：如果你把企劃換成 OpenAI 相容的端點（Groq、Ollama、OpenRouter 都可以），
`OPENAI_MAX_TOKENS` 預設是 32768，模型吃不下就會回空的，而且不會告訴你原因。

## 換成你自己的角色

改三個檔案，`scripts/` 和 workflow 都不用動：

| 檔案 | 放什麼 |
|---|---|
| `story/cast.json` | 每個角色的設定圖路徑、`must`（一定要有的特徵）、`must_not`（一定不能有的） |
| `story/README.md` | 世界觀、連載前提、笑點模板、不要出現的東西 |
| `episodes.json` | 每一話的骨架 |

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
