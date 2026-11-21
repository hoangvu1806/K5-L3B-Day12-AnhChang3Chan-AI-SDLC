"""Bảng xếp hạng v1.3 qua lệnh đã khai trong manifest."""

import json
import os
import shlex
import subprocess
import unittest
from pathlib import Path
from types import SimpleNamespace

from chonoi.contract import load_contract
from chonoi.leaderboard import read_entries, record_completed
from helpers import ROOT, Workdir, frames, read_jsonl, run_headless, write_json

CONTRACT = load_contract()
TUNING = CONTRACT["tuning"]


class Leaderboard(unittest.TestCase):
    def test_top_ten_unicode_and_stable_ties_after_reopen(self):
        with Workdir() as w:
            store = w.path("store.json")
            for seed in range(12):
                sim = SimpleNamespace(mode="day", reason="days_complete", days_completed=5,
                                      earned=seed % 2, reputation=3)
                record_completed(store, f"Út Sen {seed}", seed, sim, TUNING)
            out = w.path("top.json")
            cmd = [*shlex.split(CONTRACT["run_cmd"]), "--export-leaderboard", out, "--leaderboard", store]
            result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            highest = json.loads(Path(out).read_text(encoding="utf-8"))["entries"]
            self.assertEqual([e["seed"] for e in highest], [1, 3, 5, 7, 9, 11, 0, 2, 4, 6])
            self.assertEqual(highest[0], {"name": "Út Sen 1", "score": 301, "days_completed": 5, "seed": 1})

    def test_qualified_cli_run_records_once_without_changing_jsonl(self):
        with Workdir() as w:
            store = w.path("store.json")
            # Cập bến ngay đầu mỗi Ngày, để hết ca Quán, rồi đóng Shop ngay.
            quan_ticks = TUNING["quan"]["duration_s"] * TUNING["tick_hz"]
            day_ticks = quan_ticks + 2
            inputs = []
            for day in range(5):
                start = day * day_ticks
                inputs.extend([{"tick": start, "interact": True, "shop_done": False},
                               {"tick": start + 1, "interact": False},
                               {"tick": start + day_ticks - 1, "shop_done": True}])
            script = write_json(w.path("inputs.json"), frames(*inputs))
            args = ("--mode", "day", "--seed", "42", "--days", "5", "--ticks", str(5 * day_ticks),
                    "--inputs", script, "--snapshot-every", "200000")
            plain, ranked = w.path("plain.jsonl"), w.path("ranked.jsonl")
            code, err = run_headless(*args, "--out", plain)
            self.assertEqual(code, 0, err)
            code, err = run_headless(*args, "--out", ranked, "--leaderboard", store, "--player-name", "Út Sen")
            self.assertEqual(code, 0, err)
            self.assertEqual(Path(ranked).read_bytes(), Path(plain).read_bytes())
            end = read_jsonl(ranked)[-1]
            self.assertEqual(end["reason"], "days_complete")
            self.assertEqual(read_entries(store), [
                {"name": "Út Sen", "score": end["score"], "days_completed": 5, "seed": 42},
            ])
            scenario = write_json(w.path("scenario.json"), {})
            code, err = run_headless(*args, "--out", ranked, "--leaderboard", store, "--player-name", "Khác",
                                     "--scenario", scenario)
            self.assertEqual(code, 0, err)
            self.assertEqual(len(read_entries(store)), 1)

    def test_invalid_flag_pair_mode_and_name_and_a_truncated_run(self):
        with Workdir() as w:
            out, store = w.path("o.jsonl"), w.path("store.json")
            base = ("--seed", "7", "--ticks", "0", "--out", out)
            pair = ("--leaderboard", store)
            for mode, flags in (("day", pair), ("day", ("--player-name", "Ut")),
                                ("gather", (*pair, "--player-name", "Ut")), ("day", (*pair, "--player-name", " "))):
                self.assertEqual(run_headless(*base, "--mode", mode, *flags)[0], 2)
            self.assertFalse(os.path.exists(out))
            code, err = run_headless(*base, "--mode", "day", "--days", "5", *pair, "--player-name", "Út Sen")
            self.assertEqual(code, 0, err)
            self.assertFalse(os.path.exists(store))
