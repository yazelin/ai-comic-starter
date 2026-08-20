#!/usr/bin/env python3
"""樣板的自我檢查。

**這份跟 neko-tensei 的 176 個測試不是同一件事。** 那邊的測試編碼的是那部作品的
產品決定（五隻貓的班底、前世回憶、道具鎖、某個角色專屬的對話框規則），搬過來會有
一大半在測不存在的功能，變成「一堆預期會紅的測試」，那比沒有測試更糟。

這裡只測樣板真的用到的東西，而且**不寫死任何一個角色的名字**：角色鍵一律從
`cast.json` 推導，fork 的人換掉角色之後照樣跑得動。

    python3 scripts/test_pipeline.py
"""
import json
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import next_episode as ne
import prompt

ROOT = pathlib.Path(__file__).parent.parent
CHARS = [k for k in prompt.REF
         if k not in ('style', 'cover_style', 'balloons')
         and k not in prompt.WORLD_KEYS]


class TestCast(unittest.TestCase):
    """cast.json 是這條產線的單一事實來源,壞了什麼都不用談。"""

    def setUp(self):
        self.cast = json.loads((ROOT / 'story' / 'cast.json').read_text('utf-8'))

    def test_至少要有一個角色(self):
        self.assertTrue(self.cast['cast'], 'cast 是空的,產線沒有東西可以鎖')

    def test_每個角色都有設定圖與正反面清單(self):
        for key, c in self.cast['cast'].items():
            self.assertTrue(prompt._sheet_of(c),
                            f'{key} 沒有造型描述(sheet,或 identity+outfit)')
            self.assertTrue(c.get('must'), f'{key} 的 must 是空的')
            # must_not 想不出來,代表還沒想過模型會自己補什麼
            self.assertTrue(c.get('must_not'), f'{key} 的 must_not 是空的')

    def test_每張參考圖都真的存在(self):
        for key, (rel, _desc) in prompt.REF.items():
            self.assertTrue((ROOT / rel).is_file(), f'{key} 指到不存在的檔案: {rel}')

    def test_參考圖不要太大(self):
        """原尺寸 PNG 會讓生圖服務很久都不回,而且看起來像連線壞掉不像檔案太大。
        實測 2 MB 的 PNG 會逾時,縮成 1024px JPEG(150 KB)一次就過。"""
        for key, (rel, _desc) in prompt.REF.items():
            mb = (ROOT / rel).stat().st_size / 1e6
            self.assertLess(mb, 1.0, f'{key} 有 {mb:.1f} MB,送進生圖會逾時')

    def test_每個角色都寫進了驗收規則(self):
        """cast.json 加了角色卻忘了更新 verify.md,驗收就永遠看不到他。"""
        rules = (ROOT / 'story' / 'verify.md').read_text('utf-8')
        for c in self.cast['cast'].values():
            self.assertIn(c['name'], rules, f"{c['name']} 不在 verify.md 的識別特徵裡")


class TestPrompt(unittest.TestCase):
    def test_參考圖清單逐張標明是誰(self):
        p = prompt.build_prompt('01', ['style'] + CHARS[:1], 'x')
        self.assertIn('- image 1: ', p)
        self.assertIn('- image 2: ', p)

    def test_內頁帶對白規則(self):
        p = prompt.build_prompt('01', ['style'] + CHARS[:1], 'PANEL 1: x')
        self.assertIn('BALLOON SHAPES', p)
        self.assertIn('TRADITIONAL CHINESE', p)
        self.assertIn('FINAL CHECK', p)

    def test_角色卡完全無字(self):
        p = prompt.build_prompt(CHARS[0], [CHARS[0]], 'portrait')
        self.assertNotIn('BALLOON SHAPES', p)
        self.assertNotIn('COVER TEXT', p)

    def test_封面有字但沒有對話框(self):
        p = prompt.build_prompt('cover', ['style'] + CHARS[:1], 'a cover')
        self.assertNotIn('BALLOON SHAPES', p)
        self.assertIn('COVER TEXT', p)

    def test_七種框型都在(self):
        for s in prompt.SHAPES:
            self.assertIn(s, prompt.SHAPES_BLOCK, s)

    def test_每個角色的_sheet_都進了設定表(self):
        for c in json.loads((ROOT / 'story' / 'cast.json').read_text('utf-8'))['cast'].values():
            self.assertIn(prompt._sheet_of(c)[:40], prompt.SHEET)

    def test_畫風描述跟這部作品一致(self):
        """BASE 是從 neko-tensei 搬來的,忘了改就會每頁都套上奇幻風。"""
        self.assertNotIn('floating islands', prompt.BASE)
        self.assertIn('cel-shaded', prompt.BASE)


class TestPlanValidation(unittest.TestCase):
    """企劃是 LLM 產的,一定要驗過才落檔。"""

    def _plan(self, **over):
        # 內頁固定六頁,頁碼 01~06 各一次。說話者一定要出現在該格的畫面描述裡,
        # 不然驗證會擋下來(那條規則是為了避免對白框指向畫面上不存在的人)。
        # 畫面描述要用英文代號點名說話者(產線從 cast.json 的 desc 算出來),
        # 不能用中文名——生圖端讀的是 scene 那段英文。
        tag = ne.CHAR_TAGS[CHARS[0]]
        pages = [{'n': f'{i:02d}', 'chars': CHARS[:1],
                  'panels': [{'pos': 'top',
                              'scene': f'{tag} stands in a room, facing left',
                              'lines': [{'speaker': CHARS[0], 'shape': 'OVAL',
                                         'text': '測試'}]}]}
                 for i in range(1, 7)]
        plan = {'n': 1, 'title': '測試話', 'desc': '一句話簡介',
                'beats': ['開場', '搞砸', '收回原點'],
                'fantasy': '一個奇幻的點子', 'pages': pages}
        plan.update(over)
        return plan

    def test_好的企劃通過(self):
        self.assertEqual(ne.validate_plan(self._plan(), 1, []), [])

    def test_next_n_目前不影響驗證結果(self):
        """validate_plan 收 next_n 但刻意不用它(見該函式的 docstring):頁碼是用
        固定的 01~06 驗的,不需要依賴話數。把這件事寫成測試,免得有人以為它會擋
        話數不對的企劃。"""
        self.assertEqual(ne.validate_plan(self._plan(), 2, []), [])

    def test_標題重複會被擋(self):
        self.assertTrue(ne.validate_plan(self._plan(), 1, ['測試話']))

    def test_不認得的框型會被擋(self):
        p = self._plan()
        p['pages'][0]['panels'][0]['lines'][0]['shape'] = '圓角矩形'
        self.assertTrue(ne.validate_plan(p, 1, []))

    def test_不認得的角色會被擋(self):
        p = self._plan()
        p['pages'][0]['chars'] = ['不存在的角色']
        self.assertTrue(ne.validate_plan(p, 1, []))

    def test_簡體字會被擋(self):
        self.assertTrue(ne.has_simplified('这是简体'))
        self.assertFalse(ne.has_simplified('這是正體'))


class TestColdStart(unittest.TestCase):
    """樣板一定會經過「還沒有任何一話」的狀態,不能在這裡炸掉。"""

    def test_冷啟動不會炸而且下一話是第一話(self):
        c = ne.load_canon()
        if not c['episodes']:
            self.assertEqual(c['next_n'], 1)
            self.assertEqual(c['recent'], '')
        else:
            self.assertEqual(c['next_n'], c['episodes'][-1]['n'] + 1)

    def test_創作規範有被讀進來(self):
        self.assertIn('不要給任何角色創傷背景', ne.load_canon()['rules'])


class TestForkability(unittest.TestCase):
    """樣板跟本體最大的差別:fork 的人不必改任何一行程式。"""

    def test_repo_slug_推導得出來(self):
        self.assertIn('/', ne.REPO_SLUG)
        self.assertNotIn('neko-tensei', ne.REPO_SLUG)

    def test_預設端點不是私有服務(self):
        """neko-tensei 的預設值指向作者自架的中繼,fork 的人不改就會失敗。
        樣板不該有那種陷阱。"""
        self.assertNotIn('ching-tech', ne.GEMINI_BASE)
        self.assertEqual(ne.IMAGE_PROVIDER, 'gemini')

    def test_UA_帶得出本_repo(self):
        self.assertIn(ne.REPO_NAME, ne.UA)


if __name__ == '__main__':
    unittest.main(verbosity=1)
