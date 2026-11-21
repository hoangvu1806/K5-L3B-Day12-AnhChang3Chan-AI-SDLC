"""Kiểm tra lịch và lực dòng lũ của Gather theo TICKET-03."""

import unittest

from chonoi.contract import load_contract
from chonoi.errors import BadInput
from chonoi.inputs import InputState
from chonoi.runner import Session
from chonoi.scenario import _check_block


IDLE = InputState((0, 0), {}, set())
CURRENT = {"interval_ticks": 1800, "duration_ticks": 480, "warning_ticks": 120, "min_depth": 10, "speed": 1.5}


def make_session(pos, **overrides):
    tuning = load_contract()["tuning"]
    tuning["gather"]["current"] = CURRENT
    tuning["gather"]["oxygen_max_s"] = 60
    scenario = {
        "player": {"pos": pos}, "monsters": [], "random_fish": False,
        "current_direction": 1, **overrides,
    }
    return Session("gather", tuning, _check_block(scenario, "gather", tuning), seed=1)


def advance(session, ticks):
    return [row for _ in range(ticks) for row in session.step(IDLE)]


class GatherCurrent(unittest.TestCase):
    def test_schedule_and_snapshot_include_first_and_last_active_ticks(self):
        session = make_session([20, 10])
        for _ in range(1679):
            session.step(IDLE)
        self.assertIsNone(session.snapshot()["current"])
        rows = advance(session, 121)
        self.assertEqual([(r["tick"], r["name"], r["data"]) for r in rows], [
            (1680, "current_warning", {"starts_at_phase_tick": 1800}),
            (1800, "current_start", {"direction": 1, "duration_ticks": 480}),
        ])
        self.assertEqual(session.snapshot()["current"], {"direction": 1, "ticks_left": 480})
        self.assertAlmostEqual(session.snapshot()["player"]["pos"][0], 20.025)
        self.assertEqual(session.snapshot()["player"]["vel"], [0, 0])
        advance(session, 479)
        self.assertEqual(session.snapshot()["current"]["ticks_left"], 1)
        self.assertAlmostEqual(session.snapshot()["player"]["pos"][0], 32)
        self.assertEqual(session.snapshot()["player"]["vel"], [0, 0])
        row, = session.step(IDLE)
        self.assertEqual((row["tick"], row["name"], row["data"]),
                         (2280, "current_end", {"direction": 1, "reason": "elapsed"}))
        self.assertIsNone(session.snapshot()["current"])
        self.assertAlmostEqual(session.snapshot()["player"]["pos"][0], 32)

    def test_shallow_start_depth_and_disabled_schedule(self):
        shallow = make_session([20, 9.999])
        advance(shallow, 1799)
        shallow.step(InputState((0, 1), {}, set()))
        self.assertGreater(shallow.snapshot()["player"]["pos"][1], 10)
        self.assertEqual(shallow.snapshot()["player"]["pos"][0], 20)
        shallow.step(IDLE)
        self.assertAlmostEqual(shallow.snapshot()["player"]["pos"][0], 20.025)
        disabled = make_session([20, 10], random_current=False)
        self.assertEqual(advance(disabled, 1800), [])
        self.assertIsNone(disabled.snapshot()["current"])

    def test_last_tick_applies_current_and_ends_it_before_gather_end(self):
        session = make_session([0.01, 10], current_direction=-1, time_left_ticks=1800)
        advance(session, 1799)
        self.assertEqual([e["name"] for e in session.step(IDLE)],
                         ["current_start", "current_end", "gather_end"])
        self.assertEqual(session.snapshot()["player"]["pos"][0], 0)
        self.assertIsNone(session.snapshot()["current"])

    def test_oxygen_faint_ends_current_before_faint_event(self):
        session = make_session([20, 10])
        advance(session, 1800)
        session.sim.oxygen_ticks = 0
        session.sim.zero_oxy_ticks = session.sim.t["choke_interval_ticks"] - 1
        session.sim.hp = 1
        self.assertEqual([e["name"] for e in session.step(IDLE)],
                         ["choke", "current_end", "faint", "gather_end"])

    def test_direction_requires_signed_integer(self):
        with self.assertRaises(BadInput):
            make_session([20, 10], current_direction=True)
