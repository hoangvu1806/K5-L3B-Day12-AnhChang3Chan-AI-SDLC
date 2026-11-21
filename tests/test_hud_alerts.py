"""Phase 4 — ngưỡng cảnh báo HUD (hnha02): thủy quái gần, oxy sắp hết, khách sắp giận.

Ngưỡng là dữ liệu trong game.contract.json (tuning.hud_alerts + detect_radius từng loài), chonoi.live gửi
qua meta.alerts cho Godot. Không được đổi JSONL headless (Ticket-04: JSONL theo v1.2).
"""

import json
import unittest

from helpers import Workdir, read_jsonl, run_headless

from chonoi.contract import load_contract
from chonoi.live import LiveGame, hud_alerts


class HudAlerts(unittest.TestCase):
    def setUp(self):
        self.t = load_contract()["tuning"]

    def test_nguong_lay_tu_contract(self):
        a = hud_alerts(self.t)
        cfg = self.t["hud_alerts"]
        self.assertEqual(a["oxygen_low_ratio"], cfg["oxygen_low_ratio"])
        self.assertEqual(a["patience_low_ratio"], cfg["patience_low_ratio"])
        species = self.t["gather"]["monsters"]["species"]
        self.assertEqual(a["monster_near_m"], {k: v["detect_radius"] for k, v in species.items()})
        self.assertEqual(a["monster_near_m"]["ca_sau"], 10.0)

    def test_thieu_khoi_hud_alerts_van_co_mac_dinh(self):
        t = dict(self.t)
        t.pop("hud_alerts", None)
        a = hud_alerts(t)
        self.assertEqual((a["oxygen_low_ratio"], a["patience_low_ratio"], a["time_low_s"]), (0.25, 0.25, 30))

    def test_live_meta_co_alerts_cho_ca_ba_pha(self):
        for mode in ("gather", "quan", "day"):
            g = LiveGame(mode, self.t, {}, 1)
            snap = json.loads(g.state_json())
            self.assertIn("alerts", snap["meta"], mode)
            self.assertIn("monster_near_m", snap["meta"]["alerts"])

    def test_jsonl_headless_khong_doi(self):
        with Workdir() as w:
            for mode in ("gather", "quan"):
                out = w.path(f"{mode}.jsonl")
                code, err = run_headless("--mode", mode, "--seed", "1", "--ticks", "5", "--out", out)
                self.assertEqual(code, 0, err)
                for r in read_jsonl(out):
                    self.assertNotIn("alerts", r)
                    self.assertNotIn("meta", r)


if __name__ == "__main__":
    unittest.main()
