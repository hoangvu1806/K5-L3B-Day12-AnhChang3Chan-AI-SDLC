"""TICKET-03, kiểm đặt trước qua Session và CLI."""

import unittest

from chonoi.contract import load_contract
from chonoi.inputs import InputState
from chonoi.runner import Session
from helpers import Workdir, events, read_jsonl, run_headless, snapshots, write_json


TUNING = load_contract()["tuning"]
DISH = "ca_loc_nuong_trui"


def order(id="R1", table="T1", tick=1):
    return {"id": id, "table_id": table, "dish_id": DISH, "arrival_tick": tick}


def fish(id="I1", fresh=100):
    return {"id": id, "kind": "ca_loc", "fresh": fresh}


def step(session, *buttons):
    return session.step(InputState((0, 0), {}, set(buttons)))


def quan(orders=None, **state):
    return Session("quan", TUNING, {"reservations": [order()] if orders is None else orders,
                                   "random_customers": False, **state}, 42)


class Reservations(unittest.TestCase):
    def test_day_announces_once_after_phase_start_and_reuses_schedule(self):
        session = Session("day", TUNING, {}, 42)
        initial = session.initial_events()
        self.assertEqual([row["name"] for row in initial],
                         ["day_start", "day_plan", "phase_start", "reservation_announced", "reservation_announced"])
        orders = session.snapshot()["reservations"]
        self.assertEqual([r["id"] for r in orders], ["R1", "R2"])
        self.assertNotEqual(orders[0]["table_id"], orders[1]["table_id"])
        for reservation in orders:
            self.assertIn(reservation["dish_id"], session.snapshot()["day_plan"]["dishes"])
            self.assertIn(reservation["arrival_tick"], range(1800, 10800))
        self.assertEqual([row["name"] for row in step(session, "interact")], ["gather_end", "phase_start"])
        actual = session.snapshot()["reservations"]
        self.assertEqual([r["arrival_tick"] for r in actual], [r["arrival_tick"] for r in orders])
        self.assertEqual(actual, Session("day", TUNING, {}, 42).snapshot()["reservations"])

    def test_tables_held_at_zero_arrive_by_id_and_take_freshest_before_ordinary(self):
        session = quan([order("R2", "T2", 120), order("R1", "T1", 120)],
                       stock=[fish("I1", 90), fish("I2", 95)], random_customers=True)
        self.assertEqual([r["state"] for r in session.snapshot()["reservations"]], ["holding", "holding"])
        self.assertEqual([t["reservation_id"] for t in session.snapshot()["tables"]], ["R1", "R2", None, None])
        for _ in range(119):
            step(session)
        rows = step(session)
        self.assertEqual([r["name"] for r in rows],
                         ["reservation_arrived", "customer_arrived", "reservation_arrived", "customer_arrived", "no_dish"])
        self.assertEqual(rows[-1]["data"]["table_id"], "T3")
        customers = session.snapshot()["customers"]
        self.assertEqual([(c["reservation_id"], c["reserved"]) for c in customers], [("R1", ["I2"]), ("R2", ["I1"])])
        self.assertEqual(customers[0]["patience_ticks_left"], 3600)

    def test_occupied_and_stock_fail_once_in_order(self):
        session = quan([order("R2", "T2"), order("R1", "T1")],
                       customers=[{"id": "C7", "table_id": "T1", "dish_id": DISH, "reserved": []}],
                       time_left_ticks=2)
        rows = step(session)
        self.assertEqual([r["data"] for r in rows], [
            {"reservation_id": "R1", "reason": "occupied", "reputation": 2.0},
            {"reservation_id": "R2", "reason": "stock", "reputation": 1.0},
        ])
        self.assertEqual([r["name"] for r in step(session)], ["customer_left", "quan_end"])
        self.assertEqual([t["reservation_id"] for t in session.snapshot()["tables"]], [None] * 4)

    def test_spoils_before_failing_and_patience_failure_clears_meal(self):
        session = quan(stock=[fish(fresh=30.005)])
        step(session)
        rows = step(session)
        self.assertEqual([r["name"] for r in rows], ["spoiled", "reservation_failed"])
        self.assertEqual(rows[-1]["data"]["reason"], "stock")
        self.assertEqual(session.snapshot()["customers"], [])

        session = quan(stock=[fish()], player={"pos": [2, 8]})
        step(session)
        step(session, "interact")
        session.sim.customers[0]["patience_ticks_left"] = 1
        rows = step(session)
        self.assertEqual([r["name"] for r in rows], ["reservation_failed"])
        self.assertEqual(rows[0]["data"]["reason"], "patience")
        self.assertEqual(session.snapshot()["stoves"][0]["state"], "idle")

    def test_burn_order_and_closed_shift_delivery_pay_fresh_multiplier(self):
        session = quan(stock=[fish()], player={"pos": [2, 8]})
        step(session)
        step(session, "interact")
        session.sim.stoves[0].update(state="ready", ready_ticks=1200)
        rows = step(session)
        self.assertEqual([r["name"] for r in rows], ["dish_burnt", "reservation_failed"])
        self.assertEqual(rows[0]["data"]["order_status"], "failed")
        self.assertEqual(rows[1]["data"]["reason"], "burnt")

        session = quan(stock=[fish(fresh=100)], player={"pos": [2, 8]})
        step(session)
        rows = step(session, "interact")
        self.assertEqual(rows[0]["data"]["items"][0]["id"], "I1")
        self.assertEqual(session.sim.stoves[0]["base_price"], 59)
        session.sim.stoves[0].update(state="ready")
        step(session, "interact")
        session.sim.pos = [9, 2]
        session.sim.time_left_ticks = 1
        session.sim.customers[0]["patience_ticks_left"] = 1
        rows = step(session, "interact")
        self.assertEqual([r["name"] for r in rows], ["served", "reservation_served", "paid", "quan_end"])
        self.assertEqual(rows[1]["data"]["base_price"], 88)
        self.assertEqual(rows[2]["data"]["tip"], 0)
        self.assertEqual(session.end_row()["money"], 88)

    def test_explicit_cli_arrival_after_short_shift_and_rejects_bad_fixtures(self):
        with Workdir() as w:
            sc = w.path("scenario.json")
            out = w.path("result.jsonl")
            args = ("--mode", "quan", "--seed", "7", "--ticks", "2", "--scenario", sc, "--out", out)
            for malformed in ([order(tick=True)], [order(tick=10800)], [order(), order("R2")],
                              [dict(order(), dish_id="khong_co")]):
                write_json(sc, {"quan": {"reservations": malformed}})
                self.assertEqual(run_headless(*args)[0], 2)
            write_json(sc, {"quan": {"time_left_ticks": 1, "reservations": [order(tick=99)]}})
            code, stderr = run_headless(*args)
            self.assertEqual(code, 0, stderr)
            rows = read_jsonl(out)
            self.assertEqual(snapshots(rows)[0]["reservations"][0]["state"], "holding")
            self.assertEqual([(r["tick"], r["data"]["reason"]) for r in events(rows, "reservation_failed")],
                             [(1, "closing")])
