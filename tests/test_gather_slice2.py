"""Kiểm chứng lát hái, bắt cá và bàn giao kho qua headless contract."""
import json
import unittest

from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json


class GatherSlice2(unittest.TestCase):
    def run_case(self, block, inputs, ticks=1, inventory=False):
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"gather": block})
            inp = write_json(w.path("in.json"), frames(*inputs))
            out = w.path("out.jsonl")
            inv = w.path("inv.json")
            args = ["--mode", "gather", "--seed", "1", "--ticks", str(ticks),
                    "--scenario", sc, "--inputs", inp, "--out", out, "--snapshot-every", "1"]
            if inventory:
                args += ["--inventory-out", inv]
            code, err = run_headless(*args)
            self.assertEqual(code, 0, err)
            rows = read_jsonl(out)
            if inventory:
                with open(inv, encoding="utf-8") as f:
                    return rows, json.load(f)
            return rows

    def test_harvest_tie_and_regrowth_on_last_tick(self):
        rows, inv = self.run_case({"player": {"pos": [20, 0]}, "time_left_ticks": 1,
                                   "nodes": [{"id": "N10", "kind": "bong_sung", "pos": [22, 0]},
                                             {"id": "N2", "kind": "bong_dien_dien", "pos": [18, 0], "regrow_ticks": 1}]},
                                  [{"tick": 0, "interact": True}], inventory=True)
        self.assertEqual([e["name"] for e in events(rows)], ["node_regrown", "gather", "gather_end"])
        self.assertEqual(events(rows, "gather")[0]["data"]["node_id"], "N2")
        self.assertEqual(inv, {"items": {"bong_dien_dien": 1}})

    def test_catch_requires_full_yield_and_does_not_try_other_fish(self):
        fish = [{"id": "F1", "kind": "ca_linh", "pos": [20, 5]},
                {"id": "F2", "kind": "ca_loc", "pos": [21, 5]}]
        rows = self.run_case({"player": {"pos": [20, 5]}, "hold": ["ca_loc"] * 10, "fish": fish},
                             [{"tick": 0, "catch": True}])
        self.assertEqual(events(rows, "hold_full")[0]["data"],
                         {"action": "catch", "fish_id": "F1", "required": 3, "free": 2})
        self.assertEqual(len(snapshots(rows)[-1]["fish"]), 2)
        self.assertEqual(snapshots(rows)[-1]["player"]["catch_cd_ticks"], 0)

    def test_catch_then_dock_transfers_items(self):
        rows, inv = self.run_case({"player": {"pos": [20, 5]}, "time_left_ticks": 1,
                                   "fish": [{"id": "F1", "kind": "ca_linh", "pos": [22, 5]}]},
                                  [{"tick": 0, "catch": True}], inventory=True)
        self.assertEqual(events(rows, "fish_caught")[0]["data"]["yield"], 3)
        self.assertEqual(inv, {"items": {"ca_linh": 3}})
        rows, inv = self.run_case({"hold": ["ca_loc"]}, [{"tick": 0, "interact": True}], inventory=True)
        self.assertEqual(events(rows, "gather_end")[0]["data"]["reason"], "docked")
        self.assertEqual(inv, {"items": {"ca_loc": 1}})


if __name__ == "__main__":
    unittest.main()
