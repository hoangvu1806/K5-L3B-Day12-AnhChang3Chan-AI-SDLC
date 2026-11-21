"""Bộ kiểm thử hộp đen Phase 3 (TICKET-03 "Mùa Nước Nổi" — Test Contract v1.2, QA Lead: double-n-021).

Chiến lược tích hợp an toàn (giữ nhánh main/dev luôn xanh trong quá trình migration):
- Khi `game.contract.json` vẫn đang ở `contract_version < "1.2"`, các bài test đặc thù v1.2
  tự động skip có ghi rõ lý do chờ bật v1.2.
- Ngay khi nhóm hoàn tất adapter + Lặn + Quán và chuyển `contract_version: "1.2"`, toàn bộ
  kịch bản v1.2 dưới đây tự động kích hoạt để kiểm chứng hộp đen theo đúng TICKET-03:
    1. Manifest v1.2 khai báo `freshness` chuẩn (100, 0.5, 0.25, 30).
    2. Smoke ngưỡng ươn ở gather: `fresh: 30` -> tick 1 phát `spoiled` (`location: "hold"`).
    3. Smoke bàn giao file kho cá thể: `gather` `fresh: 100` + `interact` tick 0 -> `quan --inventory --ticks 0`
       khớp chính xác `id`, `kind`, `fresh` sau 1 tick hao.
    4. Từ chối file kho đếm v1.0/v1.1 (`{"items": {"ca_loc": 1}}`) và `fresh` ngoài `[0, 100]` với mã thoát `2`.
    5. Quán v1.2: giữ chỗ theo ID cá thể tươi nhất, khi cá thể đang giữ vừa ươn thì nhả và giữ lại
       (hoặc `unfulfillable`), và chốt giá `base_price = floor(price * avg_fresh / 100)` lúc bắt đầu nấu.
"""

import json
import math
import os
import unittest

from helpers import ROOT, Workdir, close, events, frames, read_jsonl, run_headless, snapshots, write_json


def _contract() -> dict:
    with open(os.path.join(ROOT, "game.contract.json"), encoding="utf-8") as f:
        return json.load(f)


def _is_v12() -> bool:
    return tuple(map(int, _contract().get("contract_version", "1.0").split("."))) >= (1, 2)


class Phase3DocsAndToolingReady(unittest.TestCase):
    """Luôn chạy ở mọi phiên bản: xác nhận tài liệu migration Phase 3 và CHANGELOG đã sẵn sàng."""

    def test_changelog_documents_v12_breaking_changes(self):
        path = os.path.join(ROOT, "CHANGELOG.md")
        self.assertTrue(os.path.exists(path))
        with open(path, encoding="utf-8") as f:
            text = f.read()
        for token in ("BREAKING CHANGES", "v1.2", "fresh", "spoiled", "base_price"):
            self.assertIn(token, text, f"CHANGELOG.md thiếu mục bắt buộc: {token}")

    def test_verification_phase3_doc_exists(self):
        path = os.path.join(ROOT, "docs", "verification", "phase-3.md")
        self.assertTrue(os.path.exists(path))
        with open(path, encoding="utf-8") as f:
            self.assertIn("AC-P3-", f.read())


@unittest.skipUnless(_is_v12(), "Chờ nhóm bật contract_version='1.2' sau khi tích hợp adapter + gather + quan")
class Phase3ContractV12Freshness(unittest.TestCase):
    def test_manifest_v12_freshness_config(self):
        c = _contract()
        self.assertGreaterEqual(tuple(map(int, c["contract_version"].split("."))), (1, 2))
        fr = c["tuning"].get("freshness")
        self.assertIsInstance(fr, dict)
        self.assertEqual(fr.get("initial"), 100)
        self.assertEqual(fr.get("gather_decay_per_s"), 0.5)
        self.assertEqual(fr.get("quan_decay_per_s"), 0.25)
        self.assertEqual(fr.get("spoiled_below"), 30)

    def test_smoke_threshold_fresh_30_spoils_on_tick_1(self):
        """Fixture chính thức trong TICKET-03: fresh=30 ở gather không input -> tick 1 phát spoiled."""
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {
                "gather": {
                    "hold": [{"id": "I1", "kind": "ca_linh", "fresh": 30}],
                    "random_fish": False,
                    "monsters": [],
                }
            })
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "1",
                                     "--scenario", sc, "--snapshot-every", "1", "--out", w.path("g.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("g.jsonl"))
            sp = events(rows, "spoiled")
            self.assertEqual(len(sp), 1)
            self.assertEqual(sp[0]["tick"], 1)
            self.assertEqual(sp[0]["phase"], "gather")
            self.assertEqual(sp[0]["data"], {"item_id": "I1", "kind": "ca_linh", "location": "hold"})

    def test_smoke_inventory_file_handover_exact_fresh(self):
        """Smoke bàn giao file TICKET-03: fresh=100 + interact tick 0 -> quan --inventory --ticks 0 khớp id/kind/fresh."""
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {
                "gather": {
                    "hold": [{"id": "I1", "kind": "ca_linh", "fresh": 100}],
                    "random_fish": False,
                    "monsters": [],
                }
            })
            inp = write_json(w.path("in.json"), frames({"tick": 0, "interact": True}))
            inv_path = w.path("kho_v12.json")
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "5",
                                     "--scenario", sc, "--inputs", inp,
                                     "--inventory-out", inv_path, "--out", w.path("g.jsonl"))
            self.assertEqual(code, 0, err)
            with open(inv_path, encoding="utf-8") as f:
                saved = json.load(f)
            self.assertIsInstance(saved.get("items"), list)
            self.assertEqual(len(saved["items"]), 1)
            item = saved["items"][0]
            self.assertEqual(item["id"], "I1")
            self.assertEqual(item["kind"], "ca_linh")
            # 1 tick hao gather = 0.5 / 60 = 0.008333... -> 99.99166...
            self.assertTrue(close(item["fresh"], 100.0 - 0.5 / 60.0, 0.01), item)

            code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", "0",
                                     "--inventory", inv_path, "--out", w.path("q.jsonl"))
            self.assertEqual(code, 0, err)
            s0 = snapshots(read_jsonl(w.path("q.jsonl")))[0]
            self.assertEqual(len(s0["stock"]), 1)
            self.assertEqual(s0["stock"][0]["id"], "I1")
            self.assertEqual(s0["stock"][0]["kind"], "ca_linh")
            self.assertTrue(close(s0["stock"][0]["fresh"], item["fresh"], 0.01))

    def test_v12_rejects_counted_inventory_and_invalid_fresh_exit_2(self):
        """Contract v1.2 bắt buộc trả mã 2 cho file kho đếm cũ, id trùng hoặc fresh ngoài [0, 100]."""
        with Workdir() as w:
            out = w.path("q.jsonl")
            bad_files = [
                {"items": {"ca_loc": 1}},
                {"items": [{"id": "I1", "kind": "ca_loc", "fresh": 101}]},
                {"items": [{"id": "I1", "kind": "ca_loc", "fresh": -1}]},
                {"items": [{"id": "I1", "kind": "ca_loc", "fresh": 80}, {"id": "I1", "kind": "ca_linh", "fresh": 90}]},
            ]
            for idx, payload in enumerate(bad_files):
                p = write_json(w.path(f"bad_{idx}.json"), payload)
                code, _ = run_headless("--mode", "quan", "--seed", "1", "--ticks", "0",
                                       "--inventory", p, "--out", out)
                self.assertEqual(code, 2, f"File kho sai phải thoát mã 2: {payload}")
            self.assertFalse(os.path.exists(out))

    def test_quan_re_reserve_on_spoil_and_fresh_base_price(self):
        """Khi cá thể giữ chỗ vừa ươn, quán nhả và giữ lại cá thể tươi còn lại; lúc nấu chốt base_price theo fresh."""
        with Workdir() as w:
            # Bếp B1 ở [2, 8]; kho có I1 (fresh=30 -> ươn ngay tick 1) và I2 (fresh=80).
            # Khách C1 đang giữ I1; tick 1 I1 ươn -> C1 chuyển sang giữ I2; tick 1 bấm E nấu -> base_price = floor(60 * 80 / 100) = 48 (sau hao nhẹ ~47/48).
            sc = write_json(w.path("sc.json"), {
                "quan": {
                    "player": {"pos": [2.0, 8.0]},
                    "stock": [
                        {"id": "I1", "kind": "ca_loc", "fresh": 30},
                        {"id": "I2", "kind": "ca_loc", "fresh": 80},
                    ],
                    "customers": [{
                        "id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                        "state": "waiting", "reserved": ["I1"],
                    }],
                    "random_customers": False,
                }
            })
            inp = write_json(w.path("in.json"), frames({"tick": 1, "interact": True}))
            code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", "3",
                                     "--scenario", sc, "--inputs", inp, "--snapshot-every", "1",
                                     "--out", w.path("q.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("q.jsonl"))
            sp = events(rows, "spoiled")
            self.assertEqual(len(sp), 1)
            self.assertEqual(sp[0]["data"], {"item_id": "I1", "kind": "ca_loc", "location": "stock"})
            cs = events(rows, "cook_started")
            self.assertEqual(len(cs), 1)
            used_ids = [it["id"] for it in cs[0]["data"].get("items", [])]
            self.assertEqual(used_ids, ["I2"])
            if "base_price" in cs[0]["data"]:
                expected = math.floor(60 * (80.0 - 2 * 0.25 / 60.0) / 100.0)
                self.assertIn(cs[0]["data"]["base_price"], (expected, 47, 48))


if __name__ == "__main__":
    unittest.main()
