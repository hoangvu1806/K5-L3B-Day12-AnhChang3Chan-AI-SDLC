"""Vòng tick (Contract B, mô hình tick). KHUNG — thường không cần sửa.

Thứ tự ghi: snapshot tick 0 -> với mỗi bước: sự kiện (theo thứ tự xử lý) rồi snapshot (nếu tới lượt
hoặc buổi kết thúc) -> dòng 'end'. Mỗi tick tối đa một snapshot.

`Session` là API bước tick gọn dùng chung cho headless (`run`) và cửa sổ chơi trực tiếp (`chonoi.live`):
cả hai chạy CÙNG một lớp sim, không nhân đôi logic.
"""

import math

from .ids import IdAllocator
from .inputs import InputPlayer
from .inventory import write_inventory
from .jsonl import JsonlWriter
from .rng import Streams
from .sim.gather import GatherSim
from .sim.day import DaySim
from .sim.quan import QuanSim


def build_sim(mode, tuning, scenario, seed, inventory, days=1):
    streams, ids = Streams(seed), IdAllocator()
    if mode == "day":
        return DaySim(tuning, scenario, streams, ids, days=days)
    if mode == "gather":
        return GatherSim(tuning, scenario, streams, ids)
    return QuanSim(tuning, scenario, streams, ids, inventory=inventory)


def _common(sim, tick, sim_tick, phase_tick, tuning, state):
    mult = tuning["score"]["reputation_multiplier"]
    return {
        "type": "snapshot", "tick": tick, "sim_tick": sim_tick, "mode": sim.mode, "phase": sim.phase,
        "phase_tick": phase_tick, "state": state, "time_left_ticks": sim.time_left_ticks,
        "money": sim.money, "earned": sim.earned, "reputation": sim.reputation,
        "score": sim.earned + mult * math.floor(sim.reputation),
    }


class Session:
    """Một lượt chơi: dựng sim, bước từng tick, lấy snapshot / dòng end."""

    def __init__(self, mode, tuning, scenario, seed, inventory=None, days=1):
        self.mode = mode
        self.tuning = tuning
        self.sim = build_sim(mode, tuning, scenario, seed, inventory, days)
        self.tick = 0       # tick ngoài: tăng cả khi pause
        self.sim_tick = 0   # bước gameplay đã chạy: đứng yên khi pause
        self.paused = False

    @property
    def phase_tick(self):
        return getattr(self.sim, "phase_tick", self.sim_tick)

    def _event(self, name, data, phase=None):
        row = {"type": "event", "tick": self.tick, "phase": phase or self.sim.phase}
        if self.mode == "day":
            row["day"] = self.sim.day
        row["name"] = name
        row["data"] = data
        return row

    def initial_events(self) -> list:
        """Event tick 0 của day (day_start, day_plan, phase_start) — ghi trước snapshot tick 0."""
        return [self._event(n, d, ph) for n, d, ph in getattr(self.sim, "initial_events", [])]

    def consume_phase_change(self) -> bool:
        changed = getattr(self.sim, "phase_changed", False)
        if changed:
            self.sim.phase_changed = False
        return changed

    def _state(self):
        if self.sim.done:
            return "finished"
        return "paused" if self.paused else "playing"

    @property
    def done(self) -> bool:
        return self.sim.done

    def snapshot(self) -> dict:
        s = _common(self.sim, self.tick, self.sim_tick, self.phase_tick, self.tuning, self._state())
        s.update(self.sim.snapshot())
        return s

    def step(self, inp) -> list:
        """Chạy một bước với `inp` (chonoi.inputs.InputState); trả các dòng event (tick = k + 1)."""
        self.tick += 1
        rows = []
        if inp.pressed("pause"):  # xét cạnh pause trước
            self.paused = not self.paused
            if self.paused:
                return [self._event("paused", {})]
            rows.append(self._event("resumed", {}))  # bước tiếp tục chạy gameplay ngay
        elif self.paused:
            return rows  # chỉ tăng tick ngoài; timer, lịch, sim_tick đứng yên
        events = self.sim.step(inp)
        self.sim_tick += 1
        for e in events:
            rows.append(self._event(*e))
        return rows

    def end_row(self) -> dict:
        sim = self.sim
        score = _common(sim, self.tick, self.tick, self.tick, self.tuning, "")["score"]
        row = {"type": "end", "ticks": self.tick, "sim_tick": self.sim_tick, "mode": sim.mode,
               "state": "finished" if sim.done else "playing",
               "reason": sim.reason if sim.done else "tick_limit",
               "money": sim.money, "earned": sim.earned, "reputation": sim.reputation, "score": score}
        if self.mode == "day":
            row["days_completed"] = sim.days_completed
        return row

    def write_inventory_if_done(self, inventory_out):
        """File kho: ghi MỘT lần khi có gather_end; chưa kết thúc thì giữ nguyên file đích."""
        if self.mode == "gather" and self.sim.done and inventory_out:
            write_inventory(inventory_out, self.sim.inventory_items())


def run(mode, tuning, scenario, seed, frames, ticks, out_path, snapshot_every, inventory=None, inventory_out=None,
        days=1):
    sess = Session(mode, tuning, scenario, seed, inventory, days)
    player = InputPlayer(frames)
    w = JsonlWriter(out_path)
    try:
        for row in sess.initial_events():  # day: day_start, day_plan, phase_start(gather) ở tick 0
            w.write(row)
        sess.consume_phase_change()
        w.write(sess.snapshot())  # tick 0: sau khi dựng scenario, trước mọi input
        last_snapped = 0
        while sess.tick < ticks and not sess.done:
            inp = player.advance(sess.tick)  # bước k đọc input có tick == k
            for row in sess.step(inp):
                w.write(row)
            changed = sess.consume_phase_change()  # snapshot đổi pha: pha mới, phase_tick 0
            if sess.tick % snapshot_every == 0 or sess.done or changed:
                w.write(sess.snapshot())
                last_snapped = sess.tick
        if last_snapped != sess.tick:
            w.write(sess.snapshot())
        w.write(sess.end_row())
    finally:
        w.close()
    sess.write_inventory_if_done(inventory_out)
    return sess.sim
