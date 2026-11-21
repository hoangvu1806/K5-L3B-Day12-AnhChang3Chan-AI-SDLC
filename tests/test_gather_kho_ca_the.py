"""Lát 2 (Từ Huy Bảo) — Phase 3 / TICKET-03 mục 1: kho cá thể bàn giao khi `gather_end`.

- v1.1 giữ kho đếm theo loại (regression).
- v1.2: mảng cá thể `{id, kind, fresh}` sắp theo id (I2 trước I10), gồm cả hàng ươn, là bản sao.
- `gather_end.data.inventory` theo cùng schema; ngất -> `{"items": []}`.
"""

import copy
import json
import os
import tempfile
import unittest

from chonoi.contract import load_contract
from chonoi.errors import BadInput
from chonoi.ids import IdAllocator
from chonoi.inputs import InputState
from chonoi.rng import Streams
from chonoi.scenario import load_scenario
from chonoi.sim.gather import GatherSim

FRESHNESS = {"initial": 100, "gather_decay_per_s": 0.5, "quan_decay_per_s": 0.25, "spoiled_below": 30}


def _tuning(v12=False):
    tuning = copy.deepcopy(load_contract()["tuning"])
    if v12:
        tuning["freshness"] = dict(FRESHNESS)  # TICKET-03: contract v1.2 thêm freshness
    else:
        tuning.pop("freshness", None)
    return tuning


def _sim(hold, player=None, v12=False):
    tuning = _tuning(v12)
    scenario = {"hold": hold, "random_fish": False, "fish": [], "monsters": []}
    if player:
        scenario["player"] = player
    return GatherSim(tuning, scenario, Streams(1), IdAllocator())


def _inp(*pressed):
    return InputState((0.0, 0.0), {}, set(pressed))


def _end(events):
    return [d for e, d in events if e == "gather_end"]


class InventoryItemsSchema(unittest.TestCase):
    def test_v11_counts_unchanged(self):
        sim = _sim(["ca_loc", "bong_sung", "ca_loc"])
        self.assertEqual(sim.inventory_items(), {"bong_sung": 1, "ca_loc": 2})

    def test_v12_items_sorted_by_id_and_copied(self):
        hold = [{"id": "I10", "kind": "ca_loc", "fresh": 99.5},
                {"id": "I2", "kind": "ca_linh", "fresh": 12.25},   # ươn vẫn bàn giao
                {"id": "I9", "kind": "bong_sung", "fresh": 100}]
        sim = _sim(hold, v12=True)
        items = sim.inventory_items()
        self.assertEqual([it["id"] for it in items], ["I2", "I9", "I10"])
        self.assertEqual(items[0], {"id": "I2", "kind": "ca_linh", "fresh": 12.25})
        items[0]["fresh"] = 0
        self.assertEqual(sim.hold[1]["fresh"], 12.25)
        self.assertEqual([it["id"] for it in sim.hold], ["I10", "I2", "I9"])  # giỏ giữ thứ tự vào giỏ

    def test_v12_empty_hold_is_empty_list(self):
        sim = _sim([], v12=True)
        self.assertEqual(sim.inventory_items(), [])


class GatherEndInventory(unittest.TestCase):
    def test_docked_gather_end_carries_item_schema(self):
        tuning = load_contract()["tuning"]
        sim = _sim([{"id": "I3", "kind": "ca_loc", "fresh": 80},
                    {"id": "I1", "kind": "ca_linh", "fresh": 100}],
                   player={"pos": list(tuning["gather"]["dock_pos"])}, v12=True)
        end = _end(sim.step(_inp("interact")))
        self.assertEqual(len(end), 1)
        self.assertEqual(end[0]["reason"], "docked")
        self.assertEqual([it["id"] for it in end[0]["inventory"]["items"]], ["I1", "I3"])
        self.assertEqual(end[0]["inventory"]["items"], sim.inventory_items())

    def test_v12_faint_hands_over_empty_items(self):
        sim = _sim([{"id": "I1", "kind": "ca_linh", "fresh": 100}],
                   player={"pos": [20.0, 10.0], "hp": 1, "oxygen_ticks": 0}, v12=True)
        events = []
        for _ in range(sim.t["choke_interval_ticks"] + 5):
            events = sim.step(_inp())
            if sim.done:
                break
        end = _end(events)
        self.assertEqual(end[0]["reason"], "fainted")
        self.assertEqual(end[0]["inventory"], {"items": []})


class ScenarioItemHold(unittest.TestCase):
    """TICKET-03: `gather.hold` là mảng cá thể ở v1.2; sai hoặc mâu thuẫn -> BadInput (mã 2)."""

    def _load(self, hold, v12=True):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "sc.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump({"gather": {"hold": hold, "random_fish": False, "monsters": []}}, f)
            return load_scenario(path, "gather", _tuning(v12))

    def test_v12_accepts_ticket_threshold_fixture(self):
        sc = self._load([{"id": "I1", "kind": "ca_linh", "fresh": 30}])
        self.assertEqual(sc["hold"], [{"id": "I1", "kind": "ca_linh", "fresh": 30}])

    def test_v12_rejects_bad_holds(self):
        bad = [
            ["ca_linh"],                                                       # kho dạng mã (v1.1)
            [{"id": "I1", "kind": "ca_linh"}],                                 # thiếu fresh
            [{"id": "I1", "kind": "ca_linh", "fresh": 50, "x": 1}],            # khóa lạ
            [{"id": "", "kind": "ca_linh", "fresh": 50}],                      # id rỗng
            [{"id": "I1", "kind": "ca_linh", "fresh": 50},
             {"id": "I1", "kind": "ca_loc", "fresh": 50}],                     # id trùng
            [{"id": "I1", "kind": "ca_map", "fresh": 50}],                     # kind lạ
            [{"id": "I1", "kind": "ca_linh", "fresh": 100.5}],                 # ngoài miền
            [{"id": "I1", "kind": "ca_linh", "fresh": -1}],
            [{"id": "I1", "kind": "ca_linh", "fresh": True}],
            {"I1": 1},
        ]
        for hold in bad:
            with self.subTest(hold=hold), self.assertRaises(BadInput):
                self._load(hold)

    def test_v12_capacity_still_applies(self):
        cap = _tuning(True)["gather"]["hold_capacity"]
        with self.assertRaises(BadInput):
            self._load([{"id": "I%d" % i, "kind": "ca_linh", "fresh": 100} for i in range(1, cap + 2)])

    def test_v11_still_uses_kind_codes(self):
        self.assertEqual(self._load(["ca_linh"], v12=False)["hold"], ["ca_linh"])
        with self.assertRaises(BadInput):
            self._load([{"id": "I1", "kind": "ca_linh", "fresh": 30}], v12=False)


if __name__ == "__main__":
    unittest.main()
