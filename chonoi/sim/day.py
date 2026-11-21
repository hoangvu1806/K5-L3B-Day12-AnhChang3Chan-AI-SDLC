"""Vòng ngày (`--mode day`, Test Contract v1.1): gather -> quan -> shop -> Ngày kế (tối đa 5 Ngày).

DaySim điều phối, KHÔNG nhân đôi luật: buổi sáng là GatherSim, buổi tối là QuanSim, Shop ở ShopSim.
- Đổi pha trong cùng tick: event kết thúc mang pha cũ, `phase_start` mang pha mới; pha mới chạy từ bước sau.
- Kho bàn giao trong bộ nhớ theo schema kho đếm v1.0 (hold -> items).
- Tiền, earned, uy tín, cấp đã mua giữ qua Ngày; cấp mua ở Shop chỉ áp dụng khi dựng Ngày mới.
- Pause do Session (runner) xử lý chung cho mọi mode.
"""

import copy

from .gather import GatherSim
from .quan import QuanSim

UPGRADE_FIELD = {"oxygen": "oxygen_max_s", "hp": "hp_max"}


def plan_ingredients(menu, dishes):
    """Tổng công thức nhân số suất, sắp theo id nguyên liệu."""
    out = {}
    for dish_id, n in dishes.items():
        for k, q in menu[dish_id]["recipe"].items():
            out[k] = out.get(k, 0) + q * n
    return {k: out[k] for k in sorted(out)}


class ShopSim:
    mode = "day"
    phase = "shop"

    def __init__(self, day, stock):
        self.day = day
        self.stock = dict(stock)  # kho dư từ ca tối, bỏ sau Shop
        self.time_left_ticks = int(day.tuning["shop"]["max_ticks"])
        self.done = False
        self.reason = None

    def snapshot(self) -> dict:
        return {"stock": {k: self.stock[k] for k in sorted(self.stock) if self.stock[k] > 0}}

    def step(self, inp):
        events = []
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        if inp.buy:  # một buy trước cạnh shop_done, kể cả bước cuối
            self.day.buy(inp.buy, events)
        if inp.pressed("shop_done"):
            self._end("done", events)
        elif self.time_left_ticks <= 0:
            self._end("time", events)
        return events

    def _end(self, reason, events):
        self.done = True
        self.reason = reason
        events.append(("shop_end", {"reason": reason}))


class DaySim:
    mode = "day"

    def __init__(self, tuning, scenario, streams, ids, days=1):
        self.tuning = tuning
        self.rng = streams
        self.ids = ids
        self.days = days
        d = scenario.get("day", {})
        self.gather_tpl = scenario.get("gather", {})
        self.quan_tpl = scenario.get("quan", {})
        self.money = d.get("money", 0)
        self.earned = d.get("earned", 0)
        self.reputation = d.get("reputation", tuning["quan"]["reputation_initial"])
        self.upgrades = dict(d.get("upgrades", {}))  # cấp đã mua
        self.active_upgrades = {}                     # cấp đang áp dụng (chép khi dựng Ngày)
        self.plans = {p["day"]: p for p in tuning["day_plan"]}
        for p in d.get("day_plan", []):  # scenario ghi đè theo số Ngày
            self.plans[p["day"]] = {"day": p["day"], "dishes": dict(p["dishes"]),
                                    "ingredients": plan_ingredients(tuning["menu"], p["dishes"])}
        self.day = 1
        self.days_completed = 0
        self.phase_tick = 0
        self.phase_changed = False
        self.done = False
        self.reason = None
        self.cur = None
        self.phase = None
        self.initial_events = []
        self._start_day(self.initial_events)

    # --- trạng thái chung cho runner --------------------------------------------
    @property
    def time_left_ticks(self):
        return self.cur.time_left_ticks

    @property
    def plan(self):
        return self.plans[self.day]

    def snapshot(self) -> dict:
        s = {"day": self.day, "day_plan": {"dishes": self.plan["dishes"], "ingredients": self.plan["ingredients"]},
             "upgrades": dict(sorted(self.upgrades.items())),
             "active_upgrades": dict(sorted(self.active_upgrades.items()))}
        s.update(self.cur.snapshot())
        return s

    # --- một bước ---------------------------------------------------------------
    def step(self, inp):
        """Trả mảng (name, data, phase)."""
        out = []
        self.phase_tick += 1
        phase = self.phase
        for name, data in self.cur.step(inp):
            out.append((name, data, phase))
        if phase == "quan":
            self.money, self.earned, self.reputation = self.cur.money, self.cur.earned, self.cur.reputation
        if self.cur.done:
            if phase == "gather":
                self._to_quan(out)
            elif phase == "quan":
                self._to_shop(out)
            else:
                self.days_completed += 1
                if self.days_completed >= self.days:
                    self.done = True
                    self.reason = "days_complete"
                else:
                    self.day += 1
                    self._start_day(out)
        return out

    # --- đổi pha ----------------------------------------------------------------
    def _set_phase(self, phase, sim, out):
        self.phase = phase
        self.cur = sim
        self.phase_tick = 0
        self.phase_changed = True
        out.append(("phase_start", {}, phase))

    def _start_day(self, out):
        self.active_upgrades = dict(self.upgrades)
        out.append(("day_start", {}, "gather"))
        out.append(("day_plan", {"dishes": self.plan["dishes"], "ingredients": self.plan["ingredients"]}, "gather"))
        t = copy.deepcopy(self.tuning)
        shop = self.tuning["shop"]["upgrades"]
        for kind, field in UPGRADE_FIELD.items():
            lvl = self.active_upgrades.get(kind, 0)
            if lvl > 0:
                t["gather"][field] = shop[kind][lvl - 1][field]
        sim = GatherSim(t, self.gather_tpl, self.rng, self.ids)
        sim.money, sim.earned, sim.reputation = self.money, self.earned, self.reputation
        self._set_phase("gather", sim, out)

    def _to_quan(self, out):
        items = self.cur.inventory_items()  # ngất: giỏ đã rỗng
        sim = QuanSim(self.tuning, self.quan_tpl, self.rng, self.ids, inventory=items)
        sim.money, sim.earned, sim.reputation = self.money, self.earned, self.reputation
        sim.menu_filter = set(self.plan["dishes"])  # khách chọn trong kế hoạch Ngày
        self._set_phase("quan", sim, out)

    def _to_shop(self, out):
        self._set_phase("shop", ShopSim(self, self.cur.stock), out)

    # --- Shop -------------------------------------------------------------------
    def buy(self, action, events):
        table = self.tuning["shop"]["upgrades"].get(action) if action in UPGRADE_FIELD else None
        if table is None:
            events.append(("buy_failed", {"action": action, "reason": "unknown"}))
            return
        lvl = self.upgrades.get(action, 0)
        if lvl >= len(table):
            events.append(("buy_failed", {"action": action, "reason": "max_level"}))
            return
        price = table[lvl]["price"]
        if self.money < price:
            events.append(("buy_failed", {"action": action, "reason": "funds"}))
            return
        self.money -= price
        self.upgrades[action] = lvl + 1
        events.append(("bought", {"upgrade": action, "level": lvl + 1, "price": price, "money": self.money}))
