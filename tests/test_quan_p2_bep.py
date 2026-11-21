"""Phase 2 — Lát 4 (hnha02): 2 bếp/4 bàn, 6 món, đơn theo order_tick, boa floor, đóng ca, mở rộng `burn`.

Số liệu chuẩn theo Ticket-02 mục 1.3 / mục 3 (burn); đọc từ game.contract.json, không hard-code.
"""

import copy
import json
import math
import unittest

from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json

from chonoi.ids import IdAllocator
from chonoi.rng import Streams
from chonoi.sim.quan import QuanSim


def contract():
    with open("game.contract.json", encoding="utf-8") as f:
        return json.load(f)


C = contract()
T = C["tuning"]
Q, MENU = T["quan"], T["menu"]
EAT = int(round(Q["eat_s"] * 60))
PAT = int(round(Q["patience_s"] * 60))


def cust(cid, table, dish, **kw):
    c = {"id": cid, "table_id": table, "state": "waiting", "dish_id": dish, "patience_ticks_left": PAT,
         "reserved": dict(MENU[dish]["recipe"])}
    c.update(kw)
    return c


def run(w, scenario, ticks, frames_=(), name="o"):
    sc = write_json(w.path(f"{name}.sc.json"), {"quan": dict(scenario, random_customers=False)})
    inp = write_json(w.path(f"{name}.in.json"), frames(*frames_))
    out = w.path(f"{name}.jsonl")
    code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", str(ticks), "--scenario", sc,
                             "--inputs", inp, "--out", out, "--snapshot-every", "1")
    return code, err, out


def press(t):
    return [{"tick": t, "interact": True}, {"tick": t + 1, "interact": False}]


class Inp:
    def __init__(self, interact=False):
        self.move = (0.0, 0.0)
        self._i = interact

    def pressed(self, name):
        return name == "interact" and self._i


def sim_with(scenario, burn_s=None):
    t = copy.deepcopy(T)
    t["quan"]["burn_s"] = burn_s
    return QuanSim(t, dict(scenario, random_customers=False), Streams(1), IdAllocator())


class LayoutAndMenu(unittest.TestCase):
    def test_hai_bep_bon_ban_sau_mon_theo_ticket(self):
        self.assertEqual([(s["id"], s["pos"]) for s in Q["stoves"]], [("B1", [2, 8]), ("B2", [5, 8])])
        self.assertEqual([(t["id"], t["pos"]) for t in Q["tables"]],
                         [("T1", [9, 2]), ("T2", [13, 2]), ("T3", [9, 6]), ("T4", [13, 6])])
        self.assertEqual(len(MENU), 6)
        self.assertEqual(MENU["lau_mam"]["recipe"],
                         {"ca_linh": 2, "ca_keo": 1, "keo_neo": 1, "bong_dien_dien": 1})
        with Workdir() as w:
            code, err, out = run(w, {}, 0)
            self.assertEqual(code, 0, err)
            s = snapshots(read_jsonl(out))[0]
            self.assertEqual([x["id"] for x in s["stoves"]], ["B1", "B2"])
            self.assertEqual([x["id"] for x in s["tables"]], ["T1", "T2", "T3", "T4"])

    def test_boa_floor_gia_x_ty_le_cho_ca_6_mon(self):
        for dish, m in MENU.items():
            sim = sim_with({"player": {"pos": [10, 2]}, "hand": dish, "customers": [cust("C1", "T1", dish)]})
            ev = sim.step(Inp(interact=True))
            served = [d for n, d in ev if n == "served"]
            self.assertEqual(served[0]["tip"], math.floor(m["price"] * Q["tip_rate"] + 1e-9), dish)


class OrderAndStoves(unittest.TestCase):
    def test_bep_lay_don_reserved_cu_nhat_theo_order_tick_roi_id_ban(self):
        sc = {"player": {"pos": [3.5, 8]},  # cách B1 và B2 đều 1.5 m -> hòa, chọn B1 theo id
              "stock": {"ca_loc": 1, "bong_sung": 2},
              "customers": [cust("C1", "T1", "goi_bong_sung", order_tick=50),
                            cust("C2", "T2", "ca_loc_nuong_trui", order_tick=10)]}
        sim = sim_with(sc)
        ev = sim.step(Inp(interact=True))
        cs = [d for n, d in ev if n == "cook_started"]
        self.assertEqual((cs[0]["stove_id"], cs[0]["dish_id"]), ("B1", "ca_loc_nuong_trui"))
        sim.step(Inp())
        ev = sim.step(Inp(interact=True))
        cs = [d for n, d in ev if n == "cook_started"]
        self.assertEqual((cs[0]["stove_id"], cs[0]["dish_id"]), ("B2", "goi_bong_sung"),
                         "B1 bận -> đơn kế tiếp sang B2")

    def test_hoa_order_tick_thi_id_ban_nho_truoc(self):
        sc = {"player": {"pos": [2, 7]}, "stock": {"ca_loc": 1, "bong_sung": 2},
              "customers": [cust("C1", "T3", "ca_loc_nuong_trui", order_tick=5),
                            cust("C2", "T2", "goi_bong_sung", order_tick=5)]}
        ev = sim_with(sc).step(Inp(interact=True))
        self.assertEqual([d["dish_id"] for n, d in ev if n == "cook_started"], ["goi_bong_sung"])

    def test_khong_nau_don_khong_con_phan_giu(self):
        sc = {"player": {"pos": [2, 7]}, "stock": {"ca_loc": 1},
              "customers": [cust("C1", "T1", "ca_loc_nuong_trui", reserved={})]}
        ev = sim_with(sc).step(Inp(interact=True))
        self.assertEqual([n for n, _ in ev if n == "cook_started"], [])


class CloseShift(unittest.TestCase):
    def test_dong_ca_khach_an_tra_ngay_khach_cho_roi_khong_tru_uy_tin(self):
        dish = "ca_loc_nuong_trui"
        price = MENU[dish]["price"]
        tip = math.floor(price * Q["tip_rate"] + 1e-9)
        sc = {"time_left_ticks": 3, "stock": {"ca_loc": 1},
              "customers": [cust("C1", "T1", dish, state="eating", price=price, tip=tip, eat_ticks_left=EAT,
                                 reserved={}),
                            cust("C2", "T2", dish)]}
        with Workdir() as w:
            code, err, out = run(w, sc, 10)
            self.assertEqual(code, 0, err)
            rows = read_jsonl(out)
            names = [e["name"] for e in events(rows)]
            self.assertEqual(names, ["paid", "customer_left", "quan_end"])
            self.assertEqual(events(rows, "paid")[0]["data"]["money"], price + tip)
            end = rows[-1]
            self.assertEqual(end["reason"], "time")
            self.assertEqual(end["earned"], price + tip)
            self.assertAlmostEqual(end["reputation"], Q["reputation_initial"] + Q["tip_reputation"], places=3)
            last = snapshots(rows)[-1]
            self.assertEqual(last["customers"], [])
            self.assertTrue(all(t["customer_id"] is None for t in last["tables"]))

    def test_dong_ca_don_mon_tren_bep_va_tren_tay(self):
        sc = {"time_left_ticks": 1, "hand": "goi_bong_sung",
              "stoves": [{"id": "B1", "state": "cooking", "dish": "ca_loc_nuong_trui", "cook_ticks_left": 100}]}
        with Workdir() as w:
            code, err, out = run(w, sc, 5)
            self.assertEqual(code, 0, err)
            last = snapshots(read_jsonl(out))[-1]
            self.assertIsNone(last["hand"])
            self.assertTrue(all(s["state"] == "idle" and s["dish"] is None for s in last["stoves"]))


class Burn(unittest.TestCase):
    BURN = 20

    def ready_sim(self, ready_ticks, stock, reserve_other=False):
        dish = "ca_loc_nuong_trui"
        sc = {"player": {"pos": [8, 5]}, "stock": stock,
              "stoves": [{"id": "B1", "state": "ready", "dish": dish, "ready_ticks": ready_ticks}],
              "customers": [cust("C1", "T1", dish, reserved={})]}
        if reserve_other:
            sc["customers"].append(cust("C2", "T2", dish))
        sim = sim_with(sc, burn_s=self.BURN)
        sim.stoves[0]["order_id"] = "C1"
        return sim

    def test_dung_1200_tick_van_bung_duoc(self):
        sim = self.ready_sim(int(self.BURN * 60) - 1, {})
        ev = sim.step(Inp())
        self.assertEqual([n for n, _ in ev if n == "dish_burnt"], [])
        self.assertEqual(sim.stoves[0]["ready_ticks"], 1200)
        self.assertEqual(sim.stoves[0]["state"], "ready")

    def test_qua_1200_chay_giu_lai_du_thi_reserved(self):
        sim = self.ready_sim(int(self.BURN * 60), {"ca_loc": 1})
        ev = sim.step(Inp())
        burnt = [d for n, d in ev if n == "dish_burnt"]
        self.assertEqual(burnt, [{"stove_id": "B1", "order_id": "C1", "dish_id": "ca_loc_nuong_trui",
                                  "order_status": "reserved"}])
        self.assertEqual(sim.stoves[0]["state"], "idle")
        self.assertEqual(sim.customers[0]["reserved"], {"ca_loc": 1})

    def test_qua_1200_chay_thieu_thi_unfulfillable_khach_van_cho(self):
        sim = self.ready_sim(int(self.BURN * 60), {"ca_loc": 1}, reserve_other=True)  # ca_loc đã giữ cho C2
        ev = sim.step(Inp())
        burnt = [d for n, d in ev if n == "dish_burnt"]
        self.assertEqual(burnt[0]["order_status"], "unfulfillable")
        c1 = sim._customer("C1")
        self.assertEqual((c1["state"], c1["reserved"]), ("waiting", {}))

    def test_burn_null_trong_loi_khong_bao_gio_chay(self):
        self.assertIsNone(Q["burn_s"])
        sim = sim_with({"stoves": [{"id": "B1", "state": "ready", "dish": "goi_bong_sung", "ready_ticks": 99999}]})
        self.assertEqual([n for n, _ in sim.step(Inp()) if n == "dish_burnt"], [])


if __name__ == "__main__":
    unittest.main()
