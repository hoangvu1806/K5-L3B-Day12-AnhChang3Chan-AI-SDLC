"""Lát 2 (Từ Huy Bảo) — chuẩn bị Phase 3: mọi lần mất hàng đi qua một helper LIFO `GatherSim._lose_lifo`.

Phase 3 (TICKET-03, v1.2) đổi giỏ từ mã nguyên liệu sang cá thể `{id, kind, fresh}`.
Các test này chốt hành vi LIFO cho cả hai dạng phần tử, để khi đổi schema chỉ cần sửa ở một chỗ.
Chi tiết payload v1.2 chưa có ticket -> xem `docs/clarify.md` (câu 18–20).
"""

import unittest

from chonoi.contract import load_contract
from chonoi.ids import IdAllocator
from chonoi.inputs import InputState
from chonoi.rng import Streams
from chonoi.sim.gather import GatherSim


def _sim(hold, player=None):
    tuning = load_contract()["tuning"]
    scenario = {"hold": hold, "random_fish": False, "fish": [], "monsters": []}
    if player:
        scenario["player"] = player
    return GatherSim(tuning, scenario, Streams(1), IdAllocator())


def _idle():
    return InputState((0.0, 0.0), {}, set())


def _items(*kinds):
    return [{"id": "I%d" % (i + 1), "kind": k, "fresh": 100} for i, k in enumerate(kinds)]


class LoseLifo(unittest.TestCase):
    def test_codes_newest_first(self):
        sim = _sim(["ca_loc", "bong_sung", "ca_linh"])
        self.assertEqual(sim._lose_lifo(2), ["ca_linh", "bong_sung"])
        self.assertEqual(sim.hold, ["ca_loc"])

    def test_items_newest_first_and_copied(self):
        sim = _sim(_items("ca_loc", "bong_sung", "ca_linh"))
        lost = sim._lose_lifo(2)
        self.assertEqual([x["id"] for x in lost], ["I3", "I2"])
        self.assertEqual([x["id"] for x in sim.hold], ["I1"])
        lost[0]["fresh"] = 0  # payload sự kiện là bản sao độc lập
        self.assertEqual(sim._lose_lifo(5)[0]["fresh"], 100)

    def test_zero_and_over_count_are_clamped(self):
        sim = _sim(["ca_loc", "bong_sung"])
        self.assertEqual(sim._lose_lifo(0), [])
        self.assertEqual(sim._lose_lifo(-3), [])
        self.assertEqual(sim._lose_lifo(10), ["bong_sung", "ca_loc"])
        self.assertEqual(sim.hold, [])
        self.assertEqual(sim._lose_lifo(1), [])


class LossEventsUseLifo(unittest.TestCase):
    def test_choke_faint_loses_whole_hold_newest_first(self):
        sim = _sim(_items("ca_loc", "bong_sung", "ca_keo"),
                   player={"pos": [20.0, 10.0], "hp": 1, "oxygen_ticks": 0})
        events = []
        for _ in range(sim.t["choke_interval_ticks"] + 5):
            events = sim.step(_idle())
            if sim.done:
                break
        faint = [d for e, d in events if e == "faint"]
        self.assertEqual(len(faint), 1)
        self.assertEqual([x["id"] for x in faint[0]["lost"]], ["I3", "I2", "I1"])
        self.assertEqual(sim.hold, [])

    def test_monster_hit_loses_floor_half_newest_first(self):
        tuning = load_contract()["tuning"]
        spawn = next(s for s in tuning["gather"]["monsters"]["spawns"] if s["id"] == "M1")
        sim = GatherSim(tuning, {"hold": _items("ca_loc", "bong_sung", "ca_linh", "keo_neo", "ca_keo"),
                                 "random_fish": False, "fish": [], "monsters": [spawn],
                                 "player": {"pos": list(spawn["pos"]), "hp": 3}},
                        Streams(1), IdAllocator())
        events = sim.step(_idle())
        hit = [d for e, d in events if e == "monster_hit"]
        self.assertEqual(len(hit), 1)
        self.assertEqual([x["id"] for x in hit[0]["lost"]], ["I5", "I4"])
        self.assertEqual([x["id"] for x in sim.hold], ["I1", "I2", "I3"])


if __name__ == "__main__":
    unittest.main()
