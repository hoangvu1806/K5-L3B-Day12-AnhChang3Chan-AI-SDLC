"""Kiểm tra mô phỏng Phase 3 trước khi bật adapter schema v1.2."""

import unittest

from chonoi.contract import load_contract
from chonoi.ids import IdAllocator
from chonoi.inputs import InputState
from chonoi.rng import Streams
from chonoi.runner import Session
from chonoi.sim.gather import GatherSim


def gather_session(**scenario):
    tuning = load_contract()["tuning"]
    tuning["freshness"] = {"initial": 100, "gather_decay_per_s": 0.5, "spoiled_below": 30}
    return Session("gather", tuning, {"monsters": [], "random_fish": False, **scenario}, seed=1)


def input_state(*buttons):
    return InputState((0, 0), {}, set(buttons))


class GatherFreshness(unittest.TestCase):
    def test_spoiled_only_on_crossing_without_reordering_hold(self):
        held = [
            {"id": "I10", "kind": "ca_loc", "fresh": 30},
            {"id": "I2", "kind": "ca_linh", "fresh": 30},
        ]
        session = gather_session(hold=held)
        before = session.snapshot()
        events = session.step(input_state())
        self.assertEqual([e["name"] for e in events], ["spoiled", "spoiled"])
        self.assertEqual([e["data"] for e in events], [
            {"item_id": "I2", "kind": "ca_linh", "location": "hold"},
            {"item_id": "I10", "kind": "ca_loc", "location": "hold"},
        ])
        self.assertEqual([i["id"] for i in session.snapshot()["hold"]], ["I10", "I2"])
        self.assertEqual(before["hold"], held)
        self.assertEqual([e["name"] for e in session.step(input_state())], [])
        for _ in range(58):
            session.step(input_state())
        self.assertEqual([i["fresh"] for i in session.snapshot()["hold"]], [29.5, 29.5])

    def test_catch_allocates_new_ids_at_full_freshness(self):
        session = gather_session(
            player={"pos": [15, 5]},
            hold=[{"id": "I9", "kind": "ca_loc", "fresh": 75}],
            fish=[{"id": "F1", "kind": "ca_linh", "pos": [15, 5]}],
        )
        self.assertEqual([e["name"] for e in session.step(input_state("catch"))], ["fish_caught"])
        hold = session.snapshot()["hold"]
        self.assertEqual(hold[0]["id"], "I9")
        self.assertEqual(len(hold) - 1, session.tuning["gather"]["fish_yield"]["ca_linh"])
        for index, item in enumerate(hold[1:], 10):
            self.assertEqual(item, {"id": f"I{index}", "kind": "ca_linh", "fresh": 100})

    def test_pause_does_not_age_hold(self):
        session = gather_session(hold=[{"id": "I1", "kind": "ca_loc", "fresh": 30}])
        session.step(input_state("pause"))
        session.step(input_state())
        self.assertEqual(session.snapshot()["hold"][0]["fresh"], 30)
        self.assertEqual([e["name"] for e in session.step(input_state("pause"))], ["resumed", "spoiled"])

    def test_threshold_uses_unrounded_fixture_value(self):
        session = gather_session(hold=[
            {"id": "I1", "kind": "ca_loc", "fresh": 29.9999},
            {"id": "I2", "kind": "ca_linh", "fresh": 30.0084},
        ])
        self.assertEqual(session.step(input_state()), [])
        self.assertEqual([row["data"]["item_id"] for row in session.step(input_state())], ["I2"])

    def test_faint_reports_aged_items_in_lifo_order(self):
        session = gather_session(
            player={"pos": [10, 5], "oxygen_ticks": 0, "zero_oxy_ticks": 59, "hp": 1},
            hold=[
                {"id": "I1", "kind": "ca_loc", "fresh": 100},
                {"id": "I2", "kind": "ca_linh", "fresh": 30},
            ],
        )
        rows = session.step(input_state())
        self.assertEqual([row["name"] for row in rows], ["spoiled", "choke", "faint", "gather_end"])
        lost = rows[2]["data"]["lost"]
        self.assertEqual([item["id"] for item in lost], ["I2", "I1"])
        self.assertAlmostEqual(lost[0]["fresh"], 30 - 0.5 / 60)

    def test_day_fixtures_keep_first_ids_and_allocate_fresh_ids_later(self):
        tuning = gather_session().tuning
        ids = IdAllocator()
        scenario = {"hold": [{"id": "I9", "kind": "ca_loc", "fresh": 87.5}]}
        morning1 = GatherSim(tuning, scenario, Streams(1), ids)
        self.assertEqual(morning1.hold, scenario["hold"])
        ids.new("I")
        morning2 = GatherSim(tuning, scenario, Streams(1), ids, day=2)
        self.assertEqual(morning2.hold, [{"id": "I11", "kind": "ca_loc", "fresh": 87.5}])
        self.assertEqual(scenario["hold"][0]["id"], "I9")
