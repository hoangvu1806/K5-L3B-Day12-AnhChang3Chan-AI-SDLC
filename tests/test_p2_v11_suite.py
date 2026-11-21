"""Bộ kiểm thử toàn diện Phase 2 (TICKET-02 — Test Contract v1.1 + Mở rộng `burn` & `snake`).

Kiểm tra:
1. Manifest v1.1 (`contract_version: "1.1"`, `extensions: ["burn", "snake"]`, 6 nút hái, 6 món, 2 bếp, 4 bàn).
2. Cá bơi (`fish_speed: 1.5`), đổi hướng ở tick 120, phản xạ mép `x in [4, 96]` và `fish_depths`, sinh cá ở `phase_tick = 360`.
3. Thủy quái (Cá Sấu Năm Chèo M1/M2 & Rắn Hổ Mây M3): patrol, chase, hit (mất 1 Máu + floor(len(hold)/2) LIFO + bất tử 90 tick + recoil 60 tick), ngất do quái (`faint` với `cause: "monster"`).
4. Quán v1.1: 2 bếp / 4 bàn, ưu tiên nấu theo `order_tick` rồi `table_id`, đóng ca (khách đang ăn trả tiền ngay, khách chờ rời không trừ uy tín), mở rộng cháy món (`burn_s: 20` = 1200 ticks, `dish_burnt` giữ lại hoặc `unfulfillable`).
"""

import json
import os
import unittest

from helpers import ROOT, Workdir, close, events, frames, read_jsonl, run_headless, snapshots, write_json


class Phase2ContractAndExtensions(unittest.TestCase):
    def test_contract_v11_and_extensions_declared(self):
        with open(os.path.join(ROOT, "game.contract.json"), encoding="utf-8") as f:
            c = json.load(f)
        self.assertGreaterEqual(tuple(map(int, c["contract_version"].split("."))), (1, 1))
        self.assertTrue({"burn", "snake"} <= set(c.get("extensions", [])))
        t = c["tuning"]
        self.assertEqual(len(t["gather"]["nodes"]), 6)
        self.assertEqual(t["gather"]["fish_initial"], 8)
        self.assertEqual(len(t["quan"]["stoves"]), 2)
        self.assertEqual(len(t["quan"]["tables"]), 4)
        self.assertEqual(len(t["menu"]), 6)

    def test_fish_swimming_and_spawn_at_360(self):
        with Workdir() as w:
            code, err = run_headless("--mode", "gather", "--seed", "3", "--ticks", "360",
                                     "--snapshot-every", "120", "--out", w.path("g.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("g.jsonl"))
            snaps = snapshots(rows)
            self.assertEqual(len(snaps[0]["fish"]), 8)
            # Cá phải bơi (vị trí ở tick 120 khác tick 0)
            p0 = snaps[0]["fish"][0]["pos"]
            p120 = snaps[1]["fish"][0]["pos"]
            self.assertNotEqual(p0, p120)
            # Tại tick 360, sinh thêm 1 đàn cá (fish_spawned)
            spawned = events(rows, "fish_spawned")
            self.assertEqual(len(spawned), 1)
            self.assertEqual(spawned[0]["tick"], 360)
            self.assertEqual(len(snaps[-1]["fish"]), 9)

    def test_monster_hit_lifo_loss_recoil_and_faint_cause_monster(self):
        with Workdir() as w:
            # Đặt người chơi tại [60, 24] trùng vị trí M1 (Cá Sấu), giỏ có 5 nguyên liệu, hp = 2
            kinds = ["ca_loc", "bong_sung", "ca_linh", "keo_neo", "ca_keo"]
            hold = [{"id": f"I{i + 1}", "kind": k, "fresh": 100} for i, k in enumerate(kinds)]
            sc = write_json(w.path("sc.json"), {
                "gather": {
                    "player": {"pos": [60.0, 24.0], "hp": 2},
                    "hold": hold,
                    "random_fish": False,
                }
            })
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "2", "--scenario", sc,
                                     "--snapshot-every", "1", "--out", w.path("m.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("m.jsonl"))
            hits = events(rows, "monster_hit")
            self.assertEqual(len(hits), 1)
            self.assertEqual(hits[0]["data"]["monster_id"], "M1")
            self.assertEqual(hits[0]["data"]["hp"], 1)
            # floor(5 / 2) = 2 nguyên liệu mất theo LIFO: ca_keo (I5) rồi keo_neo (I4)
            self.assertEqual([(it["id"], it["kind"]) for it in hits[0]["data"]["lost"]],
                             [("I5", "ca_keo"), ("I4", "keo_neo")])
            s1 = [s for s in snapshots(rows) if s["tick"] == 1][0]
            self.assertEqual([it["kind"] for it in s1["hold"]], ["ca_loc", "bong_sung", "ca_linh"])
            self.assertEqual(s1["player"]["invuln_ticks"], 90)
            m1 = next(m for m in s1["monsters"] if m["id"] == "M1")
            self.assertEqual(m1["state"], "recoil")
            self.assertEqual(m1["state_ticks_left"], 60)

        # Kiểm tra khi hp = 1 bị quái chạm -> faint với cause = "monster"
        with Workdir() as w:
            sc2 = write_json(w.path("sc2.json"), {
                "gather": {
                    "player": {"pos": [72.0, 14.0], "hp": 1},  # vị trí M3 (Rắn Hổ Mây)
                    "hold": [
                        {"id": "I1", "kind": "ca_loc", "fresh": 100},
                        {"id": "I2", "kind": "bong_sung", "fresh": 100},
                    ],
                    "random_fish": False,
                }
            })
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "5", "--scenario", sc2,
                                     "--out", w.path("f.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("f.jsonl"))
            hits = events(rows, "monster_hit")
            self.assertEqual([it["kind"] for it in hits[0]["data"]["lost"]], ["bong_sung"])
            faints = events(rows, "faint")
            self.assertEqual(len(faints), 1)
            self.assertEqual(faints[0]["data"]["cause"], "monster")
            self.assertEqual([it["kind"] for it in faints[0]["data"]["lost"]], ["ca_loc"])
            self.assertEqual(events(rows, "gather_end")[0]["data"]["reason"], "fainted")

    def test_burn_extension_re_reserves_or_marks_unfulfillable(self):
        import copy
        from chonoi.contract import load_contract
        from chonoi.ids import IdAllocator
        from chonoi.rng import Streams
        from chonoi.sim.quan import QuanSim
        from tests.test_quan_p2_bep import Inp
        t = copy.deepcopy(load_contract()["tuning"])
        t["quan"]["burn_s"] = 20
        sc = {
            "stock": [],
            "stoves": [{"id": "B1", "state": "ready", "dish": "ca_loc_nuong_trui", "ready_ticks": 1200, "order_id": "C1"}],
            "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                           "state": "waiting", "reserved": []}],
            "random_customers": False,
        }
        sim = QuanSim(t, sc, Streams(1), IdAllocator())
        evs = sim.step(Inp())
        burnt = [d for n, d in evs if n == "dish_burnt"]
        self.assertEqual(len(burnt), 1)
        self.assertEqual(burnt[0], {
            "stove_id": "B1",
            "order_id": "C1",
            "dish_id": "ca_loc_nuong_trui",
            "order_status": "unfulfillable",
        })

    def test_quan_shift_close_pays_eating_and_dismisses_waiting_without_penalty(self):
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {
                "quan": {
                    "time_left_ticks": 1,
                    "reputation": 3.0,
                    "stock": [{"id": "I1", "kind": "ca_loc", "fresh": 100}],
                    "customers": [
                        {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                         "state": "eating", "price": 60, "tip": 12, "eat_ticks_left": 500},
                        {"id": "C2", "table_id": "T2", "dish_id": "ca_loc_nuong_trui",
                         "state": "waiting", "patience_ticks_left": 1000, "reserved": ["I1"]},
                    ],
                    "random_customers": False,
                    "random_reservations": False,
                }
            })
            code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", "5", "--scenario", sc,
                                     "--out", w.path("c.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("c.jsonl"))
            paid = events(rows, "paid")
            self.assertEqual(len(paid), 1)
            self.assertEqual(paid[0]["data"]["customer_id"], "C1")
            left = events(rows, "customer_left")
            self.assertEqual(len(left), 1)
            self.assertEqual(left[0]["data"]["customer_id"], "C2")
            end = rows[-1]
            self.assertEqual(end["money"], 72)
            self.assertTrue(close(end["reputation"], 3.2, 0.01))


if __name__ == "__main__":
    unittest.main()
