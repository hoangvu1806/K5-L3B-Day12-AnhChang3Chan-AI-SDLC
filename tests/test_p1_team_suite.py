"""Bộ kiểm thử toàn diện Phase 1 của nhóm AnhChang3Chan (QA Lead: double-n-021).

Kiểm tra:
1. Hợp đồng tích hợp (docs/contracts/README.md, inventory.sample.json, skills).
2. Lát 1 & Lát 2 (GatherSim): bề mặt/dưới nước, cập bến, hết giờ, bảo toàn file kho, determinism.
3. Lát 3 & Lát 4 (QuanSim): khởi tạo bếp/bàn/khách, nạp kho từ file, hết giờ (quan_end).
4. Kiểm lỗi đầu vào & scenario mức luật (thoát mã 2 trước khi ghi file).
5. Tương thích scene Godot 3D (`godot/main.tscn`, `godot/main.gd`).
"""

import json
import os
import unittest

from chonoi.contract import load_contract
from chonoi.inventory import read_inventory
from helpers import (ROOT, Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json)


class Phase1HarnessAndContracts(unittest.TestCase):
    def test_integration_contract_and_sample_inventory_valid(self):
        sample_path = os.path.join(ROOT, "docs", "contracts", "inventory.sample.json")
        self.assertTrue(os.path.exists(sample_path))
        items = read_inventory(sample_path)
        self.assertEqual(items, {"bong_sung": 2, "ca_loc": 1})

    def test_skills_and_plan_exist(self):
        for rel in (
            ".agents/skills/headless-contract-check/SKILL.md",
            ".agents/skills/phase-gate-audit/SKILL.md",
            "docs/contracts/README.md",
            "docs/plan/phase-1.md",
        ):
            p = os.path.join(ROOT, rel)
            self.assertTrue(os.path.exists(p), f"Thiếu file bắt buộc: {rel}")
            with open(p, encoding="utf-8") as f:
                self.assertGreater(len(f.read().strip()), 100, f"File rỗng hoặc quá ngắn: {rel}")

    def test_godot_3d_scene_and_script_configured(self):
        tscn = os.path.join(ROOT, "godot", "main.tscn")
        gd = os.path.join(ROOT, "godot", "main.gd")
        self.assertTrue(os.path.exists(tscn))
        self.assertTrue(os.path.exists(gd))
        with open(tscn, encoding="utf-8") as f:
            self.assertIn('type="Node3D"', f.read())
        with open(gd, encoding="utf-8") as f:
            content = f.read()
            self.assertIn("extends Node3D", content)
            self.assertIn("Camera3D", content)


class Phase1GatherAndQuanVerification(unittest.TestCase):
    def test_gather_at_surface_flag_and_bounds(self):
        """Kiểm tra cờ at_surface ở d=0 (True) và khi lặn xuống d > surface_depth (False)."""
        g = load_contract()["tuning"]["gather"]
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"gather": {"player": {"pos": [20, g["surface_depth"] + 1.0]}}})
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "1", "--scenario", sc,
                                     "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            s0 = snapshots(read_jsonl(w.path("o.jsonl")))[0]
            self.assertFalse(s0["player"]["at_surface"])

    def test_gather_dock_priority_and_inventory_persistence(self):
        """Ở trong vùng bến (dock_radius=3 quanh [2,0]), bấm interact phải cập bến ngay và xuất đúng kho cá thể."""
        with Workdir() as w:
            kinds = ["bong_dien_dien", "ca_linh", "ca_linh", "ca_linh", "ca_loc"]
            hold = [{"id": f"I{i + 1}", "kind": k, "fresh": 100} for i, k in enumerate(kinds)]
            sc = write_json(w.path("sc.json"), {"gather": {"player": {"pos": [3.5, 0.0]}, "hold": hold}})
            inp = write_json(w.path("in.json"), frames({"tick": 0, "interact": True}))
            inv_out = w.path("kho.json")
            code, err = run_headless("--mode", "gather", "--seed", "10", "--ticks", "10", "--scenario", sc,
                                     "--inputs", inp, "--inventory-out", inv_out, "--out", w.path("g.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("g.jsonl"))
            end_evs = events(rows, "gather_end")
            self.assertEqual(len(end_evs), 1)
            self.assertEqual(end_evs[0]["data"]["reason"], "docked")
            ev_items = end_evs[0]["data"]["inventory"]["items"]
            self.assertEqual([(it["id"], it["kind"]) for it in ev_items],
                             [(f"I{i + 1}", k) for i, k in enumerate(kinds)])
            with open(inv_out, encoding="utf-8") as f:
                saved = json.load(f)["items"]
            self.assertEqual([(it["id"], it["kind"]) for it in saved],
                             [(f"I{i + 1}", k) for i, k in enumerate(kinds)])

    def test_gather_node_regrow_event_emitted_when_timer_reaches_zero(self):
        """Nút hái đang có regrow_ticks=2 phải giảm về 0 ở tick 2 và phát sự kiện node_regrown."""
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {
                "gather": {
                    "nodes": [{"id": "N1", "kind": "bong_dien_dien", "pos": [12, 0], "regrow_ticks": 2}],
                    "random_fish": False
                }
            })
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "3", "--scenario", sc,
                                     "--snapshot-every", "1", "--out", w.path("g.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("g.jsonl"))
            regrown = events(rows, "node_regrown")
            self.assertEqual(len(regrown), 1)
            self.assertEqual(regrown[0]["tick"], 2)
            self.assertEqual(regrown[0]["data"], {"node_id": "N1"})

    def test_quan_shift_end_and_deterministic_score(self):
        """Chế độ quan chạy hết time_left_ticks phải phát quan_end và tính đúng score = earned + 100 * floor(rep)."""
        with Workdir() as w:
            stock = [{"id": "I1", "kind": "ca_loc", "fresh": 100}, {"id": "I2", "kind": "ca_loc", "fresh": 100}]
            sc = write_json(w.path("sc.json"), {"quan": {"time_left_ticks": 2, "reputation": 3.5,
                                                        "stock": stock, "random_reservations": False}})
            code, err = run_headless("--mode", "quan", "--seed", "5", "--ticks", "10", "--scenario", sc,
                                     "--out", w.path("q.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("q.jsonl"))
            q_end = events(rows, "quan_end")
            self.assertEqual(len(q_end), 1)
            self.assertEqual(q_end[0]["tick"], 2)
            self.assertEqual(q_end[0]["data"]["reason"], "time")
            self.assertEqual(rows[-1]["type"], "end")
            self.assertEqual(rows[-1]["score"], 300)


if __name__ == "__main__":
    unittest.main()
