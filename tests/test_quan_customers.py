"""Lát 3 (Quán): khách theo lịch, giữ chỗ nguyên liệu, kiên nhẫn, customer_left, no_dish."""

import json
import unittest

from chonoi.ids import IdAllocator
from chonoi.inputs import InputState
from chonoi.rng import Streams
from chonoi.sim.quan import QuanSim

with open("game.contract.json", encoding="utf-8") as f:
    TUNING = json.load(f)["tuning"]
Q = TUNING["quan"]


def sim(scenario=None, seed=1):
    return QuanSim(TUNING, scenario or {}, Streams(seed), IdAllocator())


def run(s, n):
    ev = []
    for _ in range(n):
        ev += s.step(InputState((0.0, 0.0), frozenset(), frozenset()))
    return ev


def names(ev):
    return [e[0] for e in ev]


class Spawn(unittest.TestCase):
    def test_khach_den_dung_first_customer_tick(self):
        s = sim({"stock": {"ca_loc": 1}})
        self.assertEqual(run(s, Q["first_customer_tick"] - 1), [])
        ev = run(s, 1)
        self.assertEqual(names(ev), ["customer_arrived"])
        self.assertEqual(ev[0][1], {"customer_id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui"})
        self.assertEqual(s.customers[0]["reserved"], {"ca_loc": 1})

    def test_kho_khong_du_mon_nao_thi_no_dish(self):
        s = sim({"stock": {}})
        self.assertEqual(names(run(s, Q["first_customer_tick"])), ["no_dish"])
        self.assertEqual(s.customers, [])

    def test_giu_cho_khong_cho_khach_sau_dung_lai_nguyen_lieu(self):
        tables = [{"id": "T2", "pos": [12, 2]}]
        s = QuanSim(dict(TUNING, quan=dict(Q, tables=Q["tables"] + tables)), {"stock": {"ca_loc": 1}},
                    Streams(1), IdAllocator())
        ev = run(s, Q["first_customer_tick"] + int(Q["customer_interval_s"] * 60))
        self.assertEqual(names(ev), ["customer_arrived", "no_dish"])
        self.assertEqual(s.available().get("ca_loc"), 0)

    def test_random_customers_false_tat_khach_moi(self):
        s = sim({"stock": {"ca_loc": 5}, "random_customers": False})
        self.assertEqual(run(s, Q["first_customer_tick"] * 3), [])

    def test_cung_seed_cung_mon(self):
        stock = {"ca_loc": 9, "bong_sung": 9, "ca_linh": 9, "bong_dien_dien": 9}
        a, b = sim({"stock": stock}, seed=7), sim({"stock": stock}, seed=7)
        self.assertEqual(run(a, 200), run(b, 200))


class Patience(unittest.TestCase):
    def test_het_kien_nhan_bo_di_tra_cho_tru_uy_tin(self):
        sc = {"stock": {"ca_loc": 1}, "random_customers": False,
              "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "patience_ticks_left": 3}]}
        s = sim(sc)
        self.assertEqual(s.available().get("ca_loc"), 0)
        ev = run(s, 3)
        self.assertEqual(names(ev), ["customer_left"])
        self.assertEqual(s.customers, [])
        self.assertEqual(s.available().get("ca_loc"), 1)
        self.assertEqual(s.reputation, Q["reputation_initial"] + Q["left_reputation_delta"])

    def test_khach_moi_sau_khach_scenario_cap_id_tiep(self):
        sc = {"stock": {"ca_loc": 1}, "random_customers": True,
              "customers": [{"id": "C4", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "patience_ticks_left": 1}]}
        s = sim(sc)
        ev = run(s, Q["first_customer_tick"])
        self.assertEqual(names(ev), ["customer_left", "customer_arrived"])
        self.assertEqual(ev[1][1]["customer_id"], "C5")


if __name__ == "__main__":
    unittest.main()
