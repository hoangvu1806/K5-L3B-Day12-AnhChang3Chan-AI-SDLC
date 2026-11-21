"""P3 giữ chỗ theo id (quán, kho cá thể) + bàn giao day; P4 soak (Hoàng Vũ)."""

import json
import os
import unittest

from chonoi.ids import IdAllocator
from chonoi.inputs import InputState
from chonoi.rng import Streams
from chonoi.sim.quan import QuanSim
from chonoi.soak import soak

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = json.load(open(os.path.join(ROOT, "game.contract.json"), encoding="utf-8"))["tuning"]
IDLE = InputState((0.0, 0.0), {}, set())


def it(i, kind, fresh):
    return {"id": i, "kind": kind, "fresh": fresh}


class GiuChoTheoId(unittest.TestCase):
    def test_lay_ca_the_tuoi_nhat_hoa_theo_id_va_tieu_dung_id(self):
        stock = [it("I3", "ca_loc", 80), it("I1", "ca_loc", 90), it("I2", "ca_loc", 90), it("I4", "ca_loc", 20)]
        q = QuanSim(T, {"stock": stock, "random_customers": False,
                        "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui"}]},
                    Streams(1), IdAllocator())
        self.assertEqual(q.customers[0]["reserved"], ["I1"])          # 90 tươi nhất, hòa -> id nhỏ; I4 ươn bỏ qua
        self.assertEqual(q.available(), {"ca_loc": 2})
        used = q._consume(q.customers[0])
        self.assertEqual([u["id"] for u in used], ["I1"])
        self.assertEqual([s["id"] for s in q.stock], ["I3", "I2", "I4"])

    def test_vua_uon_thi_nha_va_giu_lai_mot_lan(self):
        stock = [it("I1", "ca_loc", 50), it("I2", "ca_loc", 40)]
        q = QuanSim(T, {"stock": stock, "random_customers": False,
                        "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "order_tick": 0},
                                      {"id": "C2", "table_id": "T2", "dish_id": "ca_loc_nuong_trui", "order_tick": 5}]},
                    Streams(1), IdAllocator())
        self.assertEqual([c["reserved"] for c in q.customers], [["I1"], ["I2"]])
        q._item("I1")["fresh"] = 29.9  # giả lập hao tươi (lát Hà Anh)
        q.recheck_spoiled([])
        c1, c2 = q.customers
        self.assertEqual((c1["reserved"], c1["order_status"]), ([], "unfulfillable"))
        self.assertEqual(c2["reserved"], ["I2"])

    def test_snapshot_kho_ca_the_sap_theo_id(self):
        q = QuanSim(T, {"stock": [it("I10", "ca_loc", 100), it("I2", "bong_sung", 100)], "random_customers": False},
                    Streams(1), IdAllocator())
        self.assertEqual([s["id"] for s in q.snapshot()["stock"]], ["I2", "I10"])


class Soak(unittest.TestCase):
    def test_soak_10_ngay_tat_dinh_khong_crash(self):
        a, b = soak(T, 7, 10), soak(T, 7, 10)
        self.assertEqual((a["days_completed"], a["crashes"], len(a["results"])), (10, 0, 10))
        self.assertEqual([r["day"] for r in a["results"]], list(range(1, 11)))
        self.assertEqual(set(a["results"][0]), {"day", "earned", "reputation", "score"})
        self.assertEqual({k: v for k, v in a.items() if k != "duration_s"},
                         {k: v for k, v in b.items() if k != "duration_s"})


if __name__ == "__main__":
    unittest.main()
