"""Phase 2 (v1.1) — `--mode day`: vòng ngày, kế hoạch, Shop, nâng cấp, pause (hộp đen qua headless)."""

import json
import os
import unittest

from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json

with open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "game.contract.json"),
          encoding="utf-8") as f:
    T = json.load(f)["tuning"]
SHOP = T["shop"]["max_ticks"]
DOCK = {"tick": 0, "interact": True}  # tương tác ở bến -> đóng ca sáng ngay


def day(w, scenario=None, inputs=(), days=1, ticks=60000, every=100000):
    args = ["--mode", "day", "--seed", "1", "--days", str(days), "--ticks", str(ticks),
            "--snapshot-every", str(every), "--out", w.path("o.jsonl")]
    if scenario is not None:
        args += ["--scenario", write_json(w.path("sc.json"), scenario)]
    if inputs:
        args += ["--inputs", write_json(w.path("in.json"), frames(*inputs))]
    code, err = run_headless(*args)
    return code, err, (read_jsonl(w.path("o.jsonl")) if code == 0 else [])


def names(rows):
    return [r["name"] for r in events(rows)]


class DayLoop(unittest.TestCase):
    def test_mo_dau_ngay_va_doi_pha(self):
        with Workdir() as w:
            code, err, rows = day(w, inputs=[DOCK])
            self.assertEqual(code, 0, err)
            first = [(r["tick"], r["phase"], r["day"], r["name"]) for r in events(rows)[:5]]
            self.assertEqual(first, [(0, "gather", 1, "day_start"), (0, "gather", 1, "day_plan"),
                                     (0, "gather", 1, "phase_start"), (1, "gather", 1, "gather_end"),
                                     (1, "quan", 1, "phase_start")])
            plan = events(rows, "day_plan")[0]["data"]
            self.assertEqual(plan, {"dishes": T["day_plan"][0]["dishes"], "ingredients": T["day_plan"][0]["ingredients"]})
            snap = [s for s in snapshots(rows) if s["tick"] == 1]
            self.assertEqual((snap[0]["phase"], snap[0]["phase_tick"]), ("quan", 0), "snapshot đổi pha: pha mới, phase_tick 0")
            end = rows[-1]
            self.assertEqual((end["reason"], end["days_completed"]), ("days_complete", 1))

    def test_shop_tu_dong_sau_max_ticks(self):
        with Workdir() as w:
            _, err, rows = day(w, inputs=[DOCK])
            start = [e for e in events(rows, "phase_start") if e["phase"] == "shop"][0]["tick"]
            end = events(rows, "shop_end")[0]
            self.assertEqual((end["tick"] - start, end["data"]), (SHOP, {"reason": "time"}))

    def test_ke_hoach_ngay_2_va_ban_giao_kho(self):
        with Workdir() as w:
            code, err, rows = day(w, scenario={"gather": {"hold": ["ca_loc", "bong_sung", "bong_sung"]}},
                                  inputs=[DOCK], days=2)
            self.assertEqual(code, 0, err)
            plans = events(rows, "day_plan")
            self.assertEqual([p["day"] for p in plans], [1, 2])
            self.assertEqual(plans[1]["data"]["dishes"], T["day_plan"][1]["dishes"])
            q0 = [s for s in snapshots(rows) if s["phase"] == "quan" and s["phase_tick"] == 0][0]
            self.assertEqual(q0["stock"], {"bong_sung": 2, "ca_loc": 1})
            arrived = {e["data"]["dish_id"] for e in events(rows, "customer_arrived")}
            self.assertTrue(arrived and arrived <= set(T["day_plan"][0]["dishes"]) | set(T["day_plan"][1]["dishes"]))


class Shop(unittest.TestCase):
    def _to_shop_tick(self, w, sc):
        _, _, rows = day(w, scenario=sc, inputs=[DOCK])
        return [e for e in events(rows, "phase_start") if e["phase"] == "shop"][0]["tick"]

    def test_mua_that_bai_va_nang_cap_ap_dung_tu_ngay_ke(self):
        sc = {"day": {"money": 600, "earned": 600}}
        with Workdir() as w:
            t = self._to_shop_tick(w, sc)
            code, err, rows = day(w, scenario=sc, days=2, every=1, ticks=t + 10, inputs=[
                DOCK, {"tick": t, "buy": "oxygen"}, {"tick": t + 1, "buy": "oxygen"},
                {"tick": t + 2, "buy": "oxygen"}, {"tick": t + 3, "buy": "lao"},
                {"tick": t + 4, "shop_done": True}])
            self.assertEqual(code, 0, err)
            got = [(e["name"], e["data"]) for e in events(rows) if e["name"] in ("bought", "buy_failed")]
            self.assertEqual(got, [
                ("bought", {"upgrade": "oxygen", "level": 1, "price": 200, "money": 400}),
                ("bought", {"upgrade": "oxygen", "level": 2, "price": 400, "money": 0}),
                ("buy_failed", {"action": "oxygen", "reason": "max_level"}),
                ("buy_failed", {"action": "lao", "reason": "unknown"})])
            self.assertEqual(events(rows, "shop_end")[0]["data"], {"reason": "done"})
            s = snapshots(rows)
            in_shop = [x for x in s if x["phase"] == "shop"][-1]
            self.assertEqual((in_shop["upgrades"], in_shop["active_upgrades"]), ({"oxygen": 2}, {}))
            day2 = [x for x in s if x.get("day") == 2][0]
            self.assertEqual(day2["active_upgrades"], {"oxygen": 2})
            self.assertEqual(day2["player"]["oxygen_max_ticks"], T["shop"]["upgrades"]["oxygen"][1]["oxygen_max_s"] * 60)
            self.assertEqual(day2["money"], 0)

    def test_khong_du_tien(self):
        with Workdir() as w:
            t = self._to_shop_tick(w, None)
            _, err, rows = day(w, inputs=[DOCK, {"tick": t, "buy": "hp", "shop_done": True}])
            self.assertEqual([(e["name"], e["data"]) for e in events(rows) if e["name"] in ("buy_failed", "shop_end")],
                             [("buy_failed", {"action": "hp", "reason": "funds"}), ("shop_end", {"reason": "done"})])


class Pause(unittest.TestCase):
    def test_pause_dung_dong_ho_va_sim_tick(self):
        with Workdir() as w:
            _, err, rows = day(w, every=1, ticks=20, inputs=[{"tick": 5, "pause": True}, {"tick": 6, "pause": False},
                                                             {"tick": 10, "pause": True}])
            self.assertEqual([(e["tick"], e["name"]) for e in events(rows) if e["name"] in ("paused", "resumed")],
                             [(6, "paused"), (11, "resumed")])
            s = {x["tick"]: x for x in snapshots(rows)}
            self.assertEqual((s[8]["state"], s[8]["sim_tick"], s[8]["time_left_ticks"]),
                             ("paused", 5, s[5]["time_left_ticks"]))
            self.assertEqual((s[11]["state"], s[11]["sim_tick"]), ("playing", 6))
            self.assertEqual(rows[-1]["sim_tick"], 15)

    def test_pause_trong_gather_doc_lap(self):
        with Workdir() as w:
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "10", "--out", w.path("o.jsonl"),
                                     "--inputs", write_json(w.path("i.json"), frames({"tick": 2, "pause": True})))
            self.assertEqual(code, 0, err)
            self.assertEqual(read_jsonl(w.path("o.jsonl"))[-1]["sim_tick"], 2)


class DayInputErrors(unittest.TestCase):
    def test_tham_so_va_scenario_sai_exit_2(self):
        with Workdir() as w:
            out = w.path("o.jsonl")
            for days in ("0", "6"):
                self.assertEqual(run_headless("--mode", "day", "--seed", "1", "--days", days, "--ticks", "1", "--out", out)[0], 2)
            self.assertEqual(run_headless("--mode", "gather", "--seed", "1", "--days", "2", "--ticks", "1", "--out", out)[0], 2)
            for sc in ({"day": {"money": 100, "earned": 50}}, {"quan": {"stock": {}}}, {"quan": {"reputation": 3}},
                       {"day": {"upgrades": {"oxygen": 3}}}, {"day": {"day_plan": [{"day": 1, "dishes": {"pho": 1}}]}},
                       {"day": {"day_plan": [{"day": 1, "dishes": {"goi_bong_sung": 1}, "ingredients": {"bong_sung": 3}}]}}):
                code = run_headless("--mode", "day", "--seed", "1", "--ticks", "1", "--out", out,
                                    "--scenario", write_json(w.path("sc.json"), sc))[0]
                self.assertEqual(code, 2, sc)
            self.assertFalse(os.path.exists(out))

    def test_day_plan_ghi_de(self):
        with Workdir() as w:
            code, err, rows = day(w, scenario={"day": {"day_plan": [{"day": 1, "dishes": {"goi_bong_sung": 1}}]}},
                                  ticks=1)
            self.assertEqual(code, 0, err)
            self.assertEqual(events(rows, "day_plan")[0]["data"],
                             {"dishes": {"goi_bong_sung": 1}, "ingredients": {"bong_sung": 2}})

    def test_tat_dinh(self):
        with Workdir() as w:
            a = day(w, inputs=[DOCK], days=2)[2]
        with Workdir() as w:
            b = day(w, inputs=[DOCK], days=2)[2]
        self.assertEqual(a, b)


if __name__ == "__main__":
    unittest.main()
