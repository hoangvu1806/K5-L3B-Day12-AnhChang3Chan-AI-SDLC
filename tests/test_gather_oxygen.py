import json
import unittest

from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json


class GatherOxygen(unittest.TestCase):
    def test_crossing_surface_updates_oxygen_from_final_depth(self):
        with Workdir() as w:
            scenario = write_json(w.path("scenario.json"), {
                "gather": {"player": {"pos": [10, 0.5], "oxygen_ticks": 1}},
            })
            inputs = write_json(w.path("inputs.json"), frames(
                {"tick": 0, "move": [0, 1]},
                {"tick": 6, "move": [0, -1]},
            ))
            out = w.path("out.jsonl")
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "30", "--scenario", scenario,
                                     "--inputs", inputs, "--snapshot-every", "1", "--out", out)
            self.assertEqual(code, 0, err)
            rows = read_jsonl(out)

        dive, empty, surface = events(rows)
        self.assertEqual([e["name"] for e in (dive, empty, surface)], ["dive", "oxygen_empty", "surface"])
        self.assertEqual(dive["tick"], empty["tick"])
        state = {s["tick"]: s["player"] for s in snapshots(rows)}
        self.assertEqual(state[empty["tick"]]["oxygen_ticks"], 0)
        self.assertEqual(state[surface["tick"] - 1]["oxygen_ticks"], 0)
        self.assertGreater(state[surface["tick"]]["oxygen_ticks"], 0)
        self.assertEqual(state[surface["tick"]]["zero_oxy_ticks"], 0)

    def test_faint_wins_over_timeout_and_writes_empty_inventory(self):
        with Workdir() as w:
            scenario = write_json(w.path("scenario.json"), {
                "gather": {
                    "player": {"pos": [10, 5], "oxygen_ticks": 0, "zero_oxy_ticks": 59, "hp": 1},
                    "hold": ["ca_loc"],
                    "time_left_ticks": 1,
                },
            })
            out = w.path("out.jsonl")
            inventory = w.path("inventory.json")
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "5", "--scenario", scenario,
                                     "--out", out, "--inventory-out", inventory)
            self.assertEqual(code, 0, err)
            rows = read_jsonl(out)
            with open(inventory, encoding="utf-8") as f:
                self.assertEqual(json.load(f)["items"], {})

        self.assertEqual([e["name"] for e in events(rows)], ["choke", "faint", "gather_end"])
        final = snapshots(rows)[-1]
        self.assertEqual(final["player"]["hp"], 0)
        self.assertEqual(final["hold"], [])
        self.assertEqual(rows[-1]["reason"], "fainted")
