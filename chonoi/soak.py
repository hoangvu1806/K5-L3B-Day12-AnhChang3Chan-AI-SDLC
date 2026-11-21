"""Soak headless (Test Contract v1.3): python3 -m chonoi.soak --seed 7 --days 10 --out soak.json

Chạy N Ngày trong MỘT tiến trình bằng bot tất định (chỉ đọc trạng thái sim, không dùng đồng hồ hay random
toàn cục). Mỗi Ngày đi qua gather -> quan -> shop; kế hoạch D1–D5 lặp ở Ngày 6–10. Tiền, earned, uy tín, cấp
nâng cấp, số Ngày và id cá thể tiếp tục xuyên suốt (cùng một DaySim).

soak.json: {days, days_completed, crashes, results[{day, earned, reputation, score}], duration_s}
`results` chụp lúc Shop đóng. Cùng seed -> mọi trường trừ duration_s giống nhau.
"""

import argparse
import json
import math
import sys
import time
import traceback

from .contract import load_contract
from .errors import BadInput
from .ids import IdAllocator
from .inputs import InputState
from .rng import Streams
from .sim.day import DaySim

MAX_DAYS = 10


class Bot:
    """Chính sách đơn giản, tất định: hái nút gần nhất rồi về bến; tối nấu/bưng/giao; Shop mua oxy rồi đóng."""

    def __init__(self, tuning):
        self.t = tuning
        self.tick = 0

    def _toward(self, pos, target, radius):
        dx, dy = target[0] - pos[0], target[1] - pos[1]
        d = math.hypot(dx, dy)
        if d <= radius * 0.6:
            return (0.0, 0.0), True
        return (dx / d, dy / d), d <= radius

    def _press(self, ok):
        # cạnh lên: chỉ "bấm" ở tick chẵn để tick lẻ nhả nút
        return ok and self.tick % 2 == 0

    def act(self, sim) -> InputState:
        self.tick += 1
        ph = sim.phase
        if ph == "gather":
            return self._gather(sim.cur)
        if ph == "quan":
            return self._quan(sim.cur)
        return self._shop(sim)

    def _gather(self, g):
        t = self.t["gather"]
        pos = g.pos
        cap = t["hold_capacity"]
        late = g.time_left_ticks < 60 * 40
        ready = [n for n in g.nodes if n.get("regrow_ticks", 0) == 0]
        if len(g.hold) < cap - 1 and not late and ready:
            node = min(ready, key=lambda n: (abs(n["pos"][0] - pos[0]), n["id"]))
            move, near = self._toward(pos, node["pos"], t["interact_radius"])
            return InputState(move, {}, {"interact"} if self._press(near) else set())
        move, near = self._toward(pos, t["dock_pos"], t["dock_radius"])
        return InputState(move, {}, {"interact"} if self._press(near) else set())

    def _quan(self, q):
        r = self.t["quan"]["interact_radius"]
        pos = q.pos
        target = None
        if q.hand is not None:
            dish = q.hand.get("dish_id") if isinstance(q.hand, dict) else q.hand
            seated = {c["table_id"] for c in q.customers if c.get("state") == "waiting" and c.get("dish_id") == dish}
            tables = [tb for tb in q.tables if tb["id"] in seated]
            if tables:
                target = min(tables, key=lambda tb: (math.dist(pos, tb["pos"]), tb["id"]))["pos"]
        else:
            ready = [s for s in q.stoves if s["state"] == "ready"]
            idle = [s for s in q.stoves if s["state"] == "idle"]
            if ready:
                target = ready[0]["pos"]
            elif idle and q._next_order() is not None:
                target = idle[0]["pos"]
        if target is None:
            return InputState((0.0, 0.0), {}, set())
        move, near = self._toward(pos, target, r)
        return InputState(move, {}, {"interact"} if self._press(near) else set())

    def _shop(self, day):
        ups = self.t["shop"]["upgrades"]["oxygen"]
        lvl = day.upgrades.get("oxygen", 0)
        if lvl < len(ups) and day.money >= ups[lvl]["price"] and self.tick % 2 == 0:
            return InputState((0.0, 0.0), {}, set(), buy="oxygen")
        return InputState((0.0, 0.0), {}, {"shop_done"} if self._press(True) else set())


def soak(tuning, seed, days):
    """Chạy `days` Ngày; trả dict kết quả (duration_s đo thời gian thực, không vào luật)."""
    start = time.perf_counter()
    results, crashes = [], 0
    sim = None
    try:
        sim = DaySim(tuning, {}, Streams(seed), IdAllocator(), days=days)
        bot = Bot(tuning)
        while not sim.done:
            day = sim.day  # shop_end cùng tick dựng Ngày kế -> ghi số Ngày vừa đóng
            for name, _data, _phase in sim.step(bot.act(sim)):
                if name == "shop_end":
                    mult = tuning["score"]["reputation_multiplier"]
                    results.append({"day": day, "earned": sim.earned, "reputation": sim.reputation,
                                    "score": sim.earned + mult * math.floor(sim.reputation)})
    except Exception:  # crash của luật: ghi nhận, không để tiến trình chết
        crashes += 1
        sys.stderr.write(traceback.format_exc())
    return {"days": days, "days_completed": sim.days_completed if sim else 0, "crashes": crashes,
            "results": results, "duration_s": round(time.perf_counter() - start, 3)}


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="chonoi.soak", description="Soak headless nhiều Ngày (Test Contract v1.3).")
    p.add_argument("--seed", type=int, required=True)
    p.add_argument("--days", type=int, required=True)
    p.add_argument("--out", required=True)
    a = p.parse_args(argv)
    try:
        if not 1 <= a.days <= MAX_DAYS:
            raise BadInput(f"--days phải từ 1 đến {MAX_DAYS}")
        tuning = load_contract()["tuning"]
    except BadInput as e:
        sys.stderr.write(f"đầu vào sai: {e}\n")
        return 2
    res = soak(tuning, a.seed, a.days)
    try:
        with open(a.out, "w", encoding="utf-8", newline="\n") as f:
            json.dump(res, f, ensure_ascii=False, separators=(",", ":"))
            f.write("\n")
    except OSError as e:
        sys.stderr.write(f"lỗi ghi: {e}\n")
        return 1
    return 0 if res["crashes"] == 0 and res["days_completed"] == res["days"] else 1


if __name__ == "__main__":
    sys.exit(main())
