"""Test Lát 4 (quán: bếp, bưng, phục vụ, tiền) — HỘP ĐEN qua headless_cmd.

Số liệu đọc từ game.contract.json, không hard-code. Giả định chưa rõ trong PRD ghi ở docs/clarify.md.
"""

import json
import math
import unittest

from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json


def tuning():
    with open("game.contract.json", encoding="utf-8") as f:
        return json.load(f)["tuning"]


T = tuning()
Q, MENU = T["quan"], T["menu"]
STOVE = Q["stoves"][0]
TABLE = Q["tables"][0]
DISH = "ca_loc_nuong_trui"
PRICE = MENU[DISH]["price"]
COOK_TICKS = int(round(MENU[DISH]["cook_s"] * 60))
EAT_TICKS = int(round(Q["eat_s"] * 60))
PATIENCE_TICKS = int(round(Q["patience_s"] * 60))
NEAR_STOVE = [STOVE["pos"][0] + 1, STOVE["pos"][1]]
NEAR_TABLE = [TABLE["pos"][0] + 1, TABLE["pos"][1]]


def customer(**kw):
    c = {"id": "C1", "table_id": TABLE["id"], "state": "waiting", "dish_id": DISH,
         "patience_ticks_left": PATIENCE_TICKS}
    c.update(kw)
    return c


def run(w, scenario, ticks, presses=(), name="o"):
    sc = write_json(w.path(f"{name}.sc.json"), {"quan": scenario})
    fr = []
    for t in presses:
        fr += [{"tick": t, "interact": True}, {"tick": t + 1, "interact": False}]
    inp = write_json(w.path(f"{name}.in.json"), frames(*fr))
    out = w.path(f"{name}.jsonl")
    code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", str(ticks), "--scenario", sc,
                             "--inputs", inp, "--out", out, "--snapshot-every", "1")
    return code, err, out


class Lat4(unittest.TestCase):
    def ok(self, w, scenario, ticks, presses=()):
        code, err, out = run(w, scenario, ticks, presses)
        self.assertEqual(code, 0, err)
        return read_jsonl(out)

    def test_cook_started_then_dish_ready(self):
        with Workdir() as w:
            stock = [{"id": "I1", "kind": "ca_loc", "fresh": 100}, {"id": "I2", "kind": "ca_loc", "fresh": 100}]
            sc = {"player": {"pos": NEAR_STOVE}, "stock": stock,
                  "customers": [customer(reserved=["I1"])]}
            rows = self.ok(w, sc, COOK_TICKS + 5, presses=[0])
            cs = events(rows, "cook_started")
            self.assertEqual(len(cs), 1)
            self.assertEqual(cs[0]["data"]["dish_id"], DISH)
            snap1 = [s for s in snapshots(rows) if s["tick"] == 1][0]
            self.assertEqual(snap1["stoves"][0]["state"], "cooking")
            self.assertEqual([it["id"] for it in snap1["stock"]], ["I2"], "trừ kho đúng cá thể công thức")
            self.assertEqual(snap1["customers"][0]["reserved"], [], "đã dùng phần giữ chỗ")
            dr = events(rows, "dish_ready")
            self.assertEqual(len(dr), 1)
            self.assertEqual(dr[0]["tick"], COOK_TICKS + 1)
            self.assertEqual(snapshots(rows)[-1]["stoves"][0]["state"], "ready")

    def test_no_cook_without_stock_or_customer(self):
        with Workdir() as w:
            stock = [{"id": "I1", "kind": "ca_loc", "fresh": 100}, {"id": "I2", "kind": "ca_loc", "fresh": 100}]
            rows = self.ok(w, {"player": {"pos": NEAR_STOVE}, "stock": stock}, 5, presses=[0])
            self.assertEqual(events(rows, "cook_started"), [], "không có khách thì không nấu")
            rows = self.ok(w, {"player": {"pos": NEAR_STOVE}, "customers": [customer()]}, 5, presses=[0])
            self.assertEqual(events(rows, "cook_started"), [], "thiếu nguyên liệu thì không nấu")

    def test_one_dish_per_waiting_customer(self):
        with Workdir() as w:
            stock = [{"id": "I1", "kind": "ca_loc", "fresh": 100}, {"id": "I2", "kind": "ca_loc", "fresh": 100}]
            sc = {"player": {"pos": NEAR_STOVE}, "stock": stock, "hand": DISH,
                  "customers": [customer()]}
            rows = self.ok(w, sc, 5, presses=[0])
            self.assertEqual(events(rows, "cook_started"), [], "món cho khách đã có trên tay -> không nấu thêm")

    def test_pick_up_ready_dish(self):
        with Workdir() as w:
            sc = {"player": {"pos": NEAR_STOVE},
                  "stoves": [{"id": STOVE["id"], "state": "ready", "dish": DISH}]}
            rows = self.ok(w, sc, 3, presses=[0])
            self.assertEqual(len(events(rows, "dish_picked")), 1)
            last = snapshots(rows)[-1]
            self.assertEqual(last["hand"], DISH)
            self.assertEqual(last["stoves"][0]["state"], "idle")

    def test_carry_limit_hand_full(self):
        with Workdir() as w:
            sc = {"player": {"pos": NEAR_STOVE}, "hand": "goi_bong_sung",
                  "stoves": [{"id": STOVE["id"], "state": "ready", "dish": DISH}]}
            rows = self.ok(w, sc, 3, presses=[0])
            self.assertEqual(events(rows, "dish_picked"), [])
            self.assertEqual(snapshots(rows)[-1]["hand"], "goi_bong_sung")

    def test_serve_then_paid_with_tip(self):
        with Workdir() as w:
            sc = {"player": {"pos": NEAR_TABLE}, "hand": DISH, "customers": [customer()]}
            rows = self.ok(w, sc, EAT_TICKS + 5, presses=[0])
            tip = math.floor(PRICE * Q["tip_rate"] + 0.5)
            sv = events(rows, "served")
            self.assertEqual(len(sv), 1)
            self.assertEqual((sv[0]["data"]["price"], sv[0]["data"]["tip"]), (PRICE, tip))
            paid = events(rows, "paid")
            self.assertEqual(len(paid), 1)
            self.assertEqual(paid[0]["tick"], 1 + EAT_TICKS)
            end = rows[-1]
            self.assertEqual(end["money"], PRICE + tip)
            self.assertEqual(end["earned"], PRICE + tip)
            self.assertAlmostEqual(end["reputation"], Q["reputation_initial"] + Q["tip_reputation"], places=3)
            last = snapshots(rows)[-1]
            self.assertEqual(last["customers"], [])
            self.assertIsNone(last["tables"][0]["customer_id"], "trả tiền xong thì bàn trống")

    def test_no_tip_when_patience_low(self):
        with Workdir() as w:
            low = int(PATIENCE_TICKS * Q["tip_min_patience_ratio"]) - 1
            sc = {"player": {"pos": NEAR_TABLE}, "hand": DISH, "customers": [customer(patience_ticks_left=low)]}
            rows = self.ok(w, sc, EAT_TICKS + 5, presses=[0])
            self.assertEqual(events(rows, "served")[0]["data"]["tip"], 0)
            self.assertEqual(rows[-1]["money"], PRICE)
            self.assertEqual(rows[-1]["reputation"], Q["reputation_initial"])

    def test_wrong_dish_not_served(self):
        with Workdir() as w:
            sc = {"player": {"pos": NEAR_TABLE}, "hand": "goi_bong_sung", "customers": [customer()]}
            rows = self.ok(w, sc, 3, presses=[0])
            self.assertEqual(events(rows, "served"), [])

    def test_reputation_clamped_at_max(self):
        with Workdir() as w:
            sc = {"player": {"pos": NEAR_TABLE}, "hand": DISH, "reputation": Q["reputation_max"],
                  "customers": [customer()]}
            rows = self.ok(w, sc, EAT_TICKS + 5, presses=[0])
            self.assertEqual(rows[-1]["reputation"], Q["reputation_max"])

    def test_full_loop_deterministic(self):
        with Workdir() as w:
            sc = {"player": {"pos": NEAR_STOVE}, "stock": [{"id": "I1", "kind": "ca_loc", "fresh": 100}],
                  "customers": [customer()], "random_reservations": False}
            outs = []
            for i in (1, 2):
                code, err, out = run(w, sc, COOK_TICKS + 20, presses=[0, COOK_TICKS + 5], name=f"d{i}")
                self.assertEqual(code, 0, err)
                with open(out, "rb") as f:
                    outs.append(f.read())
            self.assertEqual(outs[0], outs[1])
            names = [e["name"] for e in events(read_jsonl(out)) if e["name"] != "no_dish"]
            self.assertEqual(names, ["cook_started", "dish_ready", "dish_picked"])

    def test_bad_scenario_exit_2(self):
        bad = [
            {"hand": "pho_bo"},
            {"stoves": [{"id": STOVE["id"], "state": "cooking"}]},
            {"stoves": [{"id": STOVE["id"], "state": "idle", "dish": DISH}]},
            {"customers": [customer(state="eating")]},
            {"customers": [customer(dish_id="pho_bo")]},
        ]
        with Workdir() as w:
            for i, sc in enumerate(bad):
                code, err, _ = run(w, sc, 1, name=f"b{i}")
                self.assertEqual(code, 2, f"{sc} phải bị từ chối (mã 2); stderr={err}")


if __name__ == "__main__":
    unittest.main()
