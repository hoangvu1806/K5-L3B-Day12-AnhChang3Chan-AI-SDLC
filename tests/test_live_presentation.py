"""Các màn giới thiệu chỉ giữ đồng hồ live, không đổi thứ tự tick mô phỏng."""

import json
import unittest

from chonoi.contract import load_contract
from chonoi.live import INTRO_TICKS, LiveGame


class Presentation(unittest.TestCase):
    def test_player_can_go_from_menu_to_shop_and_next_day(self):
        tuning = load_contract()["tuning"]
        game = LiveGame("day", tuning, {"quan": {"time_left_ticks": 1, "random_reservations": False}},
                        7, days=2, presentation=True)

        def state():
            return json.loads(game.state_json())

        self.assertEqual(state()["presentation"]["name"], "menu")
        game._tick_once()
        self.assertEqual(state()["tick"], 0)
        game.continue_playing()
        self.assertEqual(state()["presentation"]["name"], "day_intro")
        for _ in range(INTRO_TICKS):
            game._tick_once()
        self.assertIsNone(state()["presentation"])
        self.assertEqual(state()["tick"], 0)
        game.set_input({"interact": True})
        game._tick_once()
        self.assertEqual((state()["phase"], state()["presentation"]["name"]), ("quan", "evening_intro"))
        game._tick_once()
        self.assertEqual(state()["phase_tick"], 0)
        game.continue_playing()
        game._tick_once()
        self.assertEqual((state()["phase"], state()["presentation"]["name"]), ("shop", "day_result"))
        self.assertEqual(state()["shift_summary"]["earned"], 0)
        game.continue_playing()
        game.set_input({"shop_done": True})
        game._tick_once()
        self.assertEqual((state()["day"], state()["presentation"]["name"]), (2, "day_intro"))
        game.continue_playing()
        game.set_input({"pause": True})
        game._tick_once()
        self.assertEqual(state()["state"], "paused")
        game.continue_playing()
        game._tick_once()
        self.assertEqual(state()["state"], "playing")
        game.go_to_menu()
        self.assertEqual((state()["day"], state()["tick"], state()["presentation"]["name"]), (1, 0, "menu"))
