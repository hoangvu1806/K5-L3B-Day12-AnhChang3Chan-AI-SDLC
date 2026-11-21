"""Buổi tối — Mở Quán. KHUNG: đi lại, chặn biên, đồng hồ, kho nạp từ file/scenario.

Nhóm viết tiếp (PRD-0 mục F, Quán):
  TODO(nhóm, lát 3): khách đến theo lịch, chọn món nấu được, giữ chỗ nguyên liệu, kiên nhẫn,
                     bỏ đi (customer_left), no_dish, vòng đời khách.
  Lát 4 (đã làm — xem các hàm _tick_stoves/_tick_eating/_interact và docs/clarify.md cho giả định):
    interact tại bếp/bàn (cook_started, dish_ready, dish_picked, served),
    ăn xong trả tiền (paid), boa, uy tín, hết ca (quan_end).

Hợp đồng khách giữa Lát 3 và Lát 4 (dict trong self.customers):
  id, table_id, dish_id, state ("waiting" | "eating"), patience_ticks_left, reserved {nguyên liệu: số}
  Khi "eating" Lát 4 thêm: price, tip, eat_ticks_left. Lát 3 chỉ giảm kiên nhẫn của khách "waiting".
  `reserved` được tính là VẪN NẰM TRONG stock (giữ chỗ, chưa trừ); Lát 4 trừ stock lúc bắt đầu nấu.
"""

import math

from ..ids import sort_by_id
from .ramp import ramp_velocity

TICK = 60.0


class QuanSim:
    mode = "quan"
    phase = "quan"

    def __init__(self, tuning, scenario, streams, ids, inventory=None):
        t = tuning["quan"]
        self.t = t
        self.menu = tuning["menu"]
        self.rng = streams
        self.ids = ids
        p = scenario.get("player", {})
        self.pos = list(p.get("pos", t["start_pos"]))
        self.vel = [float(c) for c in p.get("vel", [0.0, 0.0])]
        self._tgt = None
        self._ramp_left = 0
        # kho: --inventory HOẶC scenario.stock (cả hai -> cli đã báo mã 2)
        self.stock = dict(inventory if inventory is not None else scenario.get("stock", {}))
        self.hand = scenario.get("hand")
        self.time_left_ticks = scenario.get("time_left_ticks", int(round(t["duration_s"] * 60)))
        self.reputation = scenario.get("reputation", t["reputation_initial"])
        self.stoves = [dict(s, state=s.get("state", "idle"), dish=s.get("dish"),
                            cook_ticks_left=s.get("cook_ticks_left", 0), ready_ticks=s.get("ready_ticks", 0))
                       for s in self._merge(t["stoves"], scenario.get("stoves", []))]
        self.tables = self._merge(t["tables"], scenario.get("tables", []))
        # Lát 3: khách dựng sẵn từ scenario; khách chưa có món thì suy ra giữ chỗ từ công thức.
        self.patience_ticks = int(round(t["patience_s"] * 60))
        self.customers = [self._load_customer(c) for c in scenario.get("customers", [])]
        for e in self.customers:
            ids.reserve(e["id"])
        self.random_customers = scenario.get("random_customers", True)
        self.menu_filter = None  # v1.1 day: chỉ các món trong kế hoạch Ngày (DaySim gán)
        self.elapsed = 0
        self.next_customer_tick = int(t["first_customer_tick"])
        self.customer_interval_ticks = max(1, int(round(t["customer_interval_s"] * 60)))
        self._hand_order = None  # lát 4: đơn của món đang cầm (nội bộ)
        self.money = 0
        self.earned = 0
        self.shift_earned = 0
        self.done = False
        self.reason = None

    def _load_customer(self, c):
        c = dict(c)
        c.setdefault("state", "waiting")
        c.setdefault("patience_ticks_left", self.patience_ticks)
        if "reserved" not in c:
            dish = self.menu.get(c.get("dish_id"))
            c["reserved"] = dict(dish["recipe"]) if dish and c["state"] == "waiting" else {}
        return c

    # ---- Lát 3: giữ chỗ nguyên liệu (Lát 4 dùng available()/release() khi nấu) ----
    def reserved_total(self) -> dict:
        tot = {}
        for c in self.customers:
            for k, n in c.get("reserved", {}).items():
                tot[k] = tot.get(k, 0) + n
        return tot

    def available(self) -> dict:
        """Kho còn dùng được = kho - phần đã giữ chỗ cho khách."""
        res = self.reserved_total()
        return {k: self.stock.get(k, 0) - res.get(k, 0) for k in set(self.stock) | set(res)}

    def cookable_dishes(self) -> list:
        avail = self.available()
        return sorted(d for d, m in self.menu.items()
                      if (self.menu_filter is None or d in self.menu_filter) and all(avail.get(k, 0) >= n for k, n in m["recipe"].items()))

    def release(self, customer):
        customer["reserved"] = {}

    def _free_table(self):
        taken = {c["table_id"] for c in self.customers}
        for tb in self.tables:  # đã sắp theo id
            if tb["id"] not in taken:
                return tb["id"]
        return None

    def _tick_patience(self, events):
        for c in sort_by_id(list(self.customers)):
            if c["state"] != "waiting":
                continue
            c["patience_ticks_left"] = max(0, c["patience_ticks_left"] - 1)
            if c["patience_ticks_left"] == 0:
                self.release(c)
                self.customers.remove(c)
                q = self.t
                self.reputation = min(q["reputation_max"],
                                      max(q["reputation_min"], self.reputation + q["left_reputation_delta"]))
                events.append(("customer_left", {"customer_id": c["id"], "table_id": c["table_id"],
                                                 "dish_id": c.get("dish_id"), "reputation": self.reputation}))

    def _spawn_customer(self, events):
        if not self.random_customers or self.elapsed < self.next_customer_tick:
            return
        self.next_customer_tick += self.customer_interval_ticks
        table_id = self._free_table()
        if table_id is None:
            return
        dishes = self.cookable_dishes()
        if not dishes:
            events.append(("no_dish", {"table_id": table_id}))
            return
        dish_id = self.rng.get("customer_dish").choice(dishes)
        c = {"id": self.ids.new("C"), "table_id": table_id, "dish_id": dish_id, "state": "waiting",
             "patience_ticks_left": self.patience_ticks, "reserved": dict(self.menu[dish_id]["recipe"])}
        self.customers.append(c)
        events.append(("customer_arrived", {"customer_id": c["id"], "table_id": table_id, "dish_id": dish_id}))

    @staticmethod
    def _merge(defaults, updates):
        by_id = {d["id"]: dict(d) for d in defaults}
        for u in updates:
            if u["id"] not in by_id:
                from ..errors import BadInput
                raise BadInput(f"id bếp/bàn không tồn tại: {u['id']}")
            by_id[u["id"]].update(u)
        return sort_by_id(list(by_id.values()))

    def snapshot(self) -> dict:
        occupied = {c["table_id"]: c["id"] for c in self.customers}
        return {
            "player": {"pos": self.pos},
            "stock": {k: self.stock[k] for k in sorted(self.stock) if self.stock[k] > 0},
            "hand": self.hand,
            "stoves": [{k: s.get(k) for k in ("id", "pos", "state", "dish", "cook_ticks_left", "ready_ticks")}
                       for s in self.stoves],
            "tables": [{"id": tb["id"], "pos": tb["pos"], "customer_id": occupied.get(tb["id"])} for tb in self.tables],
            "customers": sort_by_id(self.customers),
        }

    def step(self, inp):
        events = []
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        self.elapsed += 1
        self._tick_stoves(events)     # lát 4: nấu -> chín (dish_ready)
        self._tick_eating(events)     # lát 4: ăn xong -> trả tiền (paid)
        self._tick_patience(events)   # lát 3: giảm kiên nhẫn khách "waiting", bỏ đi (customer_left)
        self._move(inp)
        if inp.pressed("interact"):
            self._interact(events)    # lát 4: tối đa MỘT interact
        self._spawn_customer(events)  # lát 3: khách mới theo lịch, no_dish
        if self.time_left_ticks <= 0:
            self._close_shift(events)  # lát 4 / P2: đóng ca trước quan_end
            self.done = True
            self.reason = "time"
            events.append(("quan_end", {"reason": "time", "money": self.money, "earned": self.earned,
                                        "shift_earned": self.shift_earned, "reputation": self.reputation}))
        return events

    # ------------------------------------------------------------------ lát 4 (Ticket-02 mục 1.3 + burn)
    # Đơn = khách (order_id = id khách). Bếp/tay nhớ đơn đang nấu: stove["order_id"], self._hand_order
    # (nội bộ, không ghi ra snapshot). Bếp chỉ nhận đơn "reserved": khách chờ có phần giữ đủ công thức.
    @staticmethod
    def _ticks(seconds):
        return int(round(seconds * TICK))

    def _hand_dish(self):
        h = self.hand
        return h.get("dish_id") if isinstance(h, dict) else h

    def _customer(self, cid):
        return next((c for c in self.customers if c["id"] == cid), None)

    def _burn_ticks(self):
        b = self.t.get("burn_s")
        return None if b is None else self._ticks(b)

    def _tick_stoves(self, events):
        burn = self._burn_ticks()  # mở rộng `burn`: null (lõi) -> món chín không cháy
        for s in self.stoves:  # theo id bếp
            if s["state"] == "cooking":
                s["cook_ticks_left"] = max(0, s["cook_ticks_left"] - 1)
                if s["cook_ticks_left"] == 0:
                    s["state"], s["ready_ticks"] = "ready", 0
                    events.append(("dish_ready", {"stove_id": s["id"], "dish_id": s["dish"]}))
            elif s["state"] == "ready":
                s["ready_ticks"] += 1
                if burn is not None and s["ready_ticks"] > burn:  # đúng burn tick vẫn bưng được
                    self._burn(s, events)

    def _burn(self, s, events):
        """Bỏ món, nguyên liệu mất, bếp rảnh; thử giữ lại ngay cho đơn: reserved / unfulfillable."""
        dish, oid = s["dish"], s.get("order_id")
        s.update(state="idle", dish=None, cook_ticks_left=0, ready_ticks=0, order_id=None)
        c = self._customer(oid) if oid else None
        status = None
        if c is not None and c.get("state") == "waiting":
            recipe = self.menu[c["dish_id"]]["recipe"]
            avail = self.available()
            if all(avail.get(k, 0) >= n for k, n in recipe.items()):
                c["reserved"] = dict(recipe)
                status = "reserved"
            else:
                c["reserved"] = {}
                status = "unfulfillable"
        events.append(("dish_burnt", {"stove_id": s["id"], "order_id": oid, "dish_id": dish,
                                      "order_status": status}))

    def _pay(self, c, events):
        """Khách trả tiền món + boa; boa > 0 thì cộng uy tín (kẹp min/max)."""
        q = self.t
        price, tip = c.get("price", 0), c.get("tip", 0)
        total = price + tip
        self.money += total
        self.earned += total
        self.shift_earned += total
        if tip > 0:
            self.reputation = round(min(q["reputation_max"],
                                        max(q["reputation_min"], self.reputation + q["tip_reputation"])), 3)
        self.customers.remove(c)
        events.append(("paid", {"customer_id": c["id"], "table_id": c["table_id"], "dish_id": c.get("dish_id"),
                                "price": price, "tip": tip, "money": self.money,
                                "reputation": self.reputation}))

    def _tick_eating(self, events):
        for c in sort_by_id(list(self.customers)):
            if c.get("state") != "eating":
                continue
            c["eat_ticks_left"] = max(0, c.get("eat_ticks_left", 0) - 1)
            if c["eat_ticks_left"] == 0:
                self._pay(c, events)

    def _close_shift(self, events):
        """Đóng ca: khách còn ăn trả ngay; khách còn chờ rời, KHÔNG trừ uy tín; dọn món và phần giữ."""
        for c in sort_by_id(list(self.customers)):
            if c.get("state") == "eating":
                self._pay(c, events)
        for c in sort_by_id(list(self.customers)):
            self.release(c)
            self.customers.remove(c)
            events.append(("customer_left", {"customer_id": c["id"], "table_id": c["table_id"],
                                             "dish_id": c.get("dish_id"), "reputation": self.reputation}))
        for s in self.stoves:
            s.update(state="idle", dish=None, cook_ticks_left=0, ready_ticks=0, order_id=None)
        self.hand, self._hand_order = None, None

    @staticmethod
    def _order_key(c):
        return (c.get("order_tick", 0), c["table_id"])

    def _next_order(self):
        """Đơn reserved cũ nhất theo order_tick rồi id bàn, kho thực còn đủ công thức."""
        for c in sorted((c for c in self.customers if c.get("state") == "waiting"), key=self._order_key):
            m = self.menu.get(c.get("dish_id"))
            if m is None:
                continue
            recipe = m["recipe"]
            if (all(c.get("reserved", {}).get(k, 0) >= n for k, n in recipe.items())
                    and all(self.stock.get(k, 0) >= n for k, n in recipe.items())):
                return c
        return None

    def _stove_ok(self, s):
        if self.hand is not None:  # carry_limit = 1
            return False
        if s["state"] == "idle":
            return self._next_order() is not None
        return s["state"] == "ready"

    def _table_customer(self, tb):
        return next((c for c in self.customers if c.get("table_id") == tb["id"]), None)

    def _table_ok(self, tb):
        c = self._table_customer(tb)
        hd = self._hand_dish()
        return bool(hd) and c is not None and c.get("state") == "waiting" and c.get("dish_id") == hd

    def _interact(self, events):
        r = self.t["interact_radius"]
        cands = []
        for s in self.stoves:
            d = math.dist(self.pos, s["pos"])
            if d <= r and self._stove_ok(s):
                cands.append((d, 0, s["id"], s))
        for tb in self.tables:
            d = math.dist(self.pos, tb["pos"])
            if d <= r and self._table_ok(tb):
                cands.append((d, 1, tb["id"], tb))
        if not cands:
            return
        _, kind, _, obj = min(cands, key=lambda x: x[:3])
        if kind == 0:
            self._use_stove(obj, events)
        else:
            self._serve(obj, events)

    def _use_stove(self, s, events):
        if s["state"] == "ready":
            self.hand, self._hand_order, dish = s["dish"], s.get("order_id"), s["dish"]
            s.update(state="idle", dish=None, cook_ticks_left=0, ready_ticks=0, order_id=None)
            events.append(("dish_picked", {"stove_id": s["id"], "dish_id": dish}))
            return
        c = self._next_order()
        dish = c["dish_id"]
        recipe = self.menu[dish]["recipe"]
        for k, n in recipe.items():
            self.stock[k] = self.stock.get(k, 0) - n
        self.release(c)  # phần giữ đã thành món đang nấu
        s.update(state="cooking", dish=dish, cook_ticks_left=self._ticks(self.menu[dish]["cook_s"]),
                 ready_ticks=0, order_id=c["id"])
        events.append(("cook_started", {"stove_id": s["id"], "dish_id": dish,
                                        "cook_ticks": s["cook_ticks_left"]}))

    def _serve(self, tb, events):
        q = self.t
        c = self._table_customer(tb)
        dish = self._hand_dish()
        owner = self._customer(self._hand_order) if self._hand_order else None
        if owner is not None and owner is not c and owner.get("state") == "waiting":
            # giao món của đơn khác cùng món: chuyển phần giữ của khách được giao sang đơn gốc
            owner["reserved"], c["reserved"] = c.get("reserved", {}), {}
        else:
            self.release(c)
        price = self.menu[dish]["price"]
        pmax = self._ticks(q["patience_s"])
        ratio = c.get("patience_ticks_left", pmax) / pmax
        tip = math.floor(round(price * q["tip_rate"], 9)) if ratio >= q["tip_min_patience_ratio"] else 0
        self.hand, self._hand_order = None, None
        c.update(state="eating", price=price, tip=tip, eat_ticks_left=self._ticks(q["eat_s"]))
        events.append(("served", {"customer_id": c["id"], "table_id": tb["id"], "dish_id": dish,
                                  "price": price, "tip": tip}))

    def _move(self, inp):
        speed = self.t["walk_speed"]
        mx, mz = inp.move
        self.vel = ramp_velocity(self, (mx * speed, mz * speed), int(self.t.get("ramp_max_ticks", 6)))
        b = self.t["bounds"]
        for i, axis in enumerate(("x", "z")):
            self.pos[i] += self.vel[i] / TICK
            lo, hi = b[axis]
            if self.pos[i] <= lo:
                self.pos[i], self.vel[i] = lo, max(0.0, self.vel[i])
            elif self.pos[i] >= hi:
                self.pos[i], self.vel[i] = hi, min(0.0, self.vel[i])
