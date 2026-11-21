"""Phase 3 — Quán (hnha02): hao tươi kho quán 0.25/s, spoiled ở kho, chốt base_price theo fresh, boa.

Luật theo Ticket-03 mục 1 "Độ tươi, giữ chỗ và giá". Chạy trực tiếp lớp sim với khối freshness chuẩn
(100, 0.5, 0.25, 30) để không phụ thuộc lúc nhóm bật contract v1.2. Kỳ vọng tính bằng Fraction (chính xác).
"""

import copy
import json
import math
import unittest
from fractions import Fraction

from helpers import Workdir, frames, run_headless, write_json

from chonoi.ids import IdAllocator
from chonoi.rng import Streams
from chonoi.sim.quan import QuanSim

with open("game.contract.json", encoding="utf-8") as f:
    T = json.load(f)["tuning"]
FRESH = {"initial": 100, "gather_decay_per_s": 0.5, "quan_decay_per_s": 0.25, "spoiled_below": 30}
DECAY = Fraction(1, 240)  # 0.25 / 60 mỗi tick
MENU = T["menu"]
PAT = int(round(T["quan"]["patience_s"] * 60))


class Inp:
    def __init__(self, interact=False):
        self.move = (0.0, 0.0)
        self._i = interact

    def pressed(self, name):
        return name == "interact" and self._i


def sim(stock, **sc):
    t = copy.deepcopy(T)
    t["freshness"] = FRESH
    return QuanSim(t, dict(sc, random_customers=False), Streams(1), IdAllocator(), inventory=stock)


def item(i, kind, fresh):
    return {"id": i, "kind": kind, "fresh": fresh}


def cust(cid, table, dish, reserved, **kw):
    c = {"id": cid, "table_id": table, "state": "waiting", "dish_id": dish, "patience_ticks_left": PAT,
         "reserved": reserved}
    c.update(kw)
    return c


def names(ev, n):
    return [d for k, d in ev if k == n]


class Decay(unittest.TestCase):
    def test_hao_025_moi_giay_ke_ca_hang_dang_giu(self):
        s = sim([item("I1", "ca_loc", 100), item("I2", "bong_sung", 50)],
                customers=[cust("C1", "T1", "ca_loc_nuong_trui", ["I1"])])
        for _ in range(240):
            s.step(Inp())
        self.assertEqual({it["id"]: it["fresh"] for it in s.stock}, {"I1": 99.0, "I2": 49.0})
        self.assertEqual(s.customers[0]["reserved"], ["I1"], "hàng đang giữ vẫn hao nhưng không bị nhả")

    def test_kep_day_0(self):
        s = sim([item("I1", "ca_loc", 0.001)])
        s.step(Inp())
        self.assertEqual(s.stock[0]["fresh"], 0.0)

    def test_spoiled_dung_mot_lan_tu_30_xuong_duoi_30(self):
        s = sim([item("I1", "ca_linh", 30)])
        ev = s.step(Inp())
        self.assertEqual(names(ev, "spoiled"), [{"item_id": "I1", "kind": "ca_linh", "location": "stock"}])
        for _ in range(5):
            self.assertEqual(names(s.step(Inp()), "spoiled"), [])
        self.assertEqual(len(s.stock), 1, "hàng ươn vẫn nằm trong kho")

    def test_nhieu_ca_the_cung_uon_phat_theo_id(self):
        s = sim([item("I10", "ca_linh", 30), item("I2", "ca_loc", 30), item("I3", "bong_sung", 31)])
        ev = s.step(Inp())
        self.assertEqual([d["item_id"] for d in names(ev, "spoiled")], ["I2", "I10"])

    def test_spoiled_truoc_khi_xu_ly_giu_cho_bi_uon(self):
        s = sim([item("I1", "ca_loc", 30), item("I2", "ca_loc", 90)],
                customers=[cust("C1", "T1", "ca_loc_nuong_trui", ["I1"])])
        ev = s.step(Inp())
        self.assertEqual(ev[0][0], "spoiled")
        self.assertEqual(s.customers[0]["reserved"], ["I2"], "Vũ: nhả và giữ lại cá thể còn tươi")


class Price(unittest.TestCase):
    def test_chot_base_price_theo_trung_binh_fresh_luc_nau(self):
        dish = "lau_ca_linh_dien_dien"
        stock = [item("I1", "ca_linh", 80), item("I2", "ca_linh", 70), item("I3", "ca_linh", 60),
                 item("I4", "bong_dien_dien", 50)]
        s = sim(stock, player={"pos": [2, 7]}, customers=[cust("C1", "T1", dish, ["I1", "I2", "I3", "I4"])])
        ev = s.step(Inp(interact=True))
        cs = names(ev, "cook_started")[0]
        self.assertEqual([it["id"] for it in cs["items"]], ["I4", "I1", "I2", "I3"], "sắp theo kind rồi id")
        avg = (Fraction(80 + 70 + 60 + 50) - 4 * DECAY) / 4  # hao một tick trước tương tác
        expect = math.floor(MENU[dish]["price"] * avg / 100)
        self.assertEqual(s.stoves[0]["base_price"], expect)
        self.assertEqual(expect, 77)

    def test_floor_sat_bien(self):
        s = sim([item("I1", "ca_loc", 75)], player={"pos": [2, 7]},
                customers=[cust("C1", "T1", "ca_loc_nuong_trui", ["I1"])])
        s.step(Inp(interact=True))
        # 60 × (75 − 1/240) / 100 = 44.9975 -> 44 (không làm tròn lên 45)
        self.assertEqual(s.stoves[0]["base_price"], 44)

    def test_mon_chin_khong_hao_va_gia_chot_theo_mon_len_tay_toi_khach(self):
        dish = "ca_loc_nuong_trui"
        s = sim([item("I1", "ca_loc", 50)], player={"pos": [2, 7]},
                customers=[cust("C1", "T1", dish, ["I1"])])
        s.step(Inp(interact=True))
        base = s.stoves[0]["base_price"]
        for _ in range(int(MENU[dish]["cook_s"] * 60) + 300):
            s.step(Inp())
        self.assertEqual(s.stoves[0]["state"], "ready")
        self.assertEqual(s.stoves[0]["base_price"], base)
        s.step(Inp(interact=True))
        self.assertEqual(s.hand, dish)
        s.pos = [10.0, 2.0]
        sv = names(s.step(Inp(interact=True)), "served")[0]
        self.assertEqual(sv["price"], base)
        self.assertEqual(sv["tip"], math.floor(base * T["quan"]["tip_rate"]))

    def test_boa_tren_gia_da_chot_va_paid_dung_gia_chot(self):
        dish = "lau_mam"
        s = sim([], player={"pos": [10, 2]}, hand={"dish_id": dish, "base_price": 133},
                customers=[cust("C1", "T1", dish, [])])
        sv = names(s.step(Inp(interact=True)), "served")[0]
        self.assertEqual((sv["price"], sv["tip"]), (133, 26))
        for _ in range(int(T["quan"]["eat_s"] * 60)):
            ev = s.step(Inp())
        paid = names(ev, "paid")[0]
        self.assertEqual((paid["price"], paid["tip"], paid["money"]), (133, 26, 159))

    def test_kho_dem_khong_doi_gia(self):
        t = copy.deepcopy(T)
        s = QuanSim(t, {"random_customers": False, "player": {"pos": [2, 7]}, "stock": {"ca_loc": 1},
                        "customers": [cust("C1", "T1", "ca_loc_nuong_trui", {"ca_loc": 1})]},
                    Streams(1), IdAllocator())
        s.step(Inp(interact=True))
        self.assertEqual(s.stoves[0]["base_price"], MENU["ca_loc_nuong_trui"]["price"])


class Scenario(unittest.TestCase):
    def test_hand_object_sai_thi_ma_2(self):
        bad = [{"hand": {"dish_id": "pho_bo", "base_price": 10}},
               {"hand": {"dish_id": "lau_mam", "base_price": -1}},
               {"hand": {"dish_id": "lau_mam", "gia": 1}}]
        with Workdir() as w:
            for i, sc in enumerate(bad):
                p = write_json(w.path(f"s{i}.json"), {"quan": sc})
                inp = write_json(w.path("in.json"), frames())
                code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", "1", "--scenario", p,
                                         "--inputs", inp, "--out", w.path("o.jsonl"))
                self.assertEqual(code, 2, f"{sc}: {err}")


if __name__ == "__main__":
    unittest.main()
