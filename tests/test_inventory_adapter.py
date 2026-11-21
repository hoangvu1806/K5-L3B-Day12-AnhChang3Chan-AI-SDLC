"""P3 — adapter kho: chọn schema theo contract_version (kho đếm v1.1 / kho cá thể v1.2)."""

import json
import unittest

from chonoi.errors import BadInput
from chonoi.ids import IdAllocator
from chonoi.inventory import (counts_of, items_from_counts, read_inventory, uses_item_schema,
                              validate_item_list, write_inventory)
from helpers import Workdir, write_json

ITEMS = [{"id": "I2", "kind": "ca_loc", "fresh": 97.5}, {"id": "I1", "kind": "ca_linh", "fresh": 100}]


class Version(unittest.TestCase):
    def test_chon_schema_theo_phien_ban(self):
        self.assertEqual([uses_item_schema(v) for v in ("1.0", "1.1", "1.2", "1.3", "2.0")],
                         [False, False, True, True, True])


class ReadV12(unittest.TestCase):
    def test_doc_kho_ca_the_va_kho_rong(self):
        with Workdir() as w:
            self.assertEqual(read_inventory(write_json(w.path("a.json"), {"items": ITEMS}), version="1.2"), ITEMS)
            self.assertEqual(read_inventory(write_json(w.path("b.json"), {"items": []}), version="1.2"), [])

    def test_v12_tu_choi_kho_dem_va_sai_schema(self):
        bad = [
            {"items": {"ca_loc": 1}},                                          # kho đếm
            {"items": [{"id": "I1", "kind": "ca_loc"}]},                       # thiếu fresh
            {"items": [{"id": "", "kind": "ca_loc", "fresh": 1}]},             # id rỗng
            {"items": [{"id": "I1", "kind": "ca_loc", "fresh": 1}] * 2},       # id trùng
            {"items": [{"id": "I1", "kind": "pho", "fresh": 1}]},              # kind lạ
            {"items": [{"id": "I1", "kind": "ca_loc", "fresh": 100.5}]},       # fresh ngoài miền
            {"items": [{"id": "I1", "kind": "ca_loc", "fresh": True}]},        # fresh bool
            {"items": [{"id": "I1", "kind": "ca_loc", "fresh": 1, "x": 0}]},   # khóa lạ
            {"items": [], "extra": 1},
        ]
        with Workdir() as w:
            for i, data in enumerate(bad):
                with self.assertRaises(BadInput, msg=data):
                    read_inventory(write_json(w.path(f"b{i}.json"), data), version="1.2")

    def test_v11_van_doc_kho_dem(self):
        with Workdir() as w:
            self.assertEqual(read_inventory(write_json(w.path("a.json"), {"items": {"ca_loc": 2}}), version="1.1"),
                             {"ca_loc": 2})
            with self.assertRaises(BadInput):
                read_inventory(write_json(w.path("b.json"), {"items": ITEMS}), version="1.1")


class WriteV12(unittest.TestCase):
    def test_ghi_theo_id_va_doc_lai_giu_nguyen_quanh_nguong_30(self):
        tricky = [{"id": "I10", "kind": "ca_keo", "fresh": 30 + 1 / 240},
                  {"id": "I2", "kind": "bong_sung", "fresh": 30 - 1 / 240},
                  {"id": "I1", "kind": "ca_linh", "fresh": 30}]
        with Workdir() as w:
            p = w.path("kho.json")
            write_inventory(p, tricky)
            data = json.load(open(p, encoding="utf-8"))
            self.assertEqual([it["id"] for it in data["items"]], ["I1", "I2", "I10"])
            back = read_inventory(p, version="1.2")
            self.assertEqual({it["id"]: it["fresh"] for it in back}, {it["id"]: it["fresh"] for it in tricky})
            self.assertEqual([it["fresh"] < 30 for it in back], [False, True, False])

    def test_ghi_kho_rong(self):
        with Workdir() as w:
            p = w.path("kho.json")
            write_inventory(p, [])
            self.assertEqual(json.load(open(p, encoding="utf-8")), {"items": []})


class Adapter(unittest.TestCase):
    def test_dem_sang_ca_the_va_nguoc_lai(self):
        ids = IdAllocator()
        ids.reserve("I4")
        items = items_from_counts({"ca_loc": 1, "bong_sung": 2}, ids)
        self.assertEqual(items, [{"id": "I5", "kind": "bong_sung", "fresh": 100},
                                 {"id": "I6", "kind": "bong_sung", "fresh": 100},
                                 {"id": "I7", "kind": "ca_loc", "fresh": 100}])
        self.assertEqual(counts_of(items), {"bong_sung": 2, "ca_loc": 1})
        self.assertEqual(validate_item_list(items), items)


if __name__ == "__main__":
    unittest.main()
