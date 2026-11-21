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
from fractions import Fraction

from ..ids import id_key, sort_by_id
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
        src = inventory if inventory is not None else scenario.get("stock", {})
        # P3: kho cá thể (mảng {id, kind, fresh}) -> giữ chỗ theo id; kho đếm (dict) -> chạy như v1.1
        self.item_mode = isinstance(src, list)
        self.stock = [dict(it) for it in src] if self.item_mode else dict(src)
        self.spoiled_below = tuning.get("freshness", {}).get("spoiled_below", 30)
        # P3 (Hà Anh): hao tươi kho quán tính chính xác bằng Fraction (như gather), float chỉ để ghi snapshot
        fr = tuning.get("freshness")
        self._fresh_on = bool(fr) and self.item_mode
        if self._fresh_on:
            # mặc định theo Ticket-03 (0.25/s, ngưỡng 30) nếu manifest chưa khai đủ khóa
            self._q_decay = Fraction(str(fr.get("quan_decay_per_s", 0.25))) / int(TICK)
            self._spoil_at = Fraction(str(fr.get("spoiled_below", 30)))
        self._fresh_by_id = {}
        if self.item_mode:
            for it in self.stock:
                ids.reserve(it["id"])
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
        if self.item_mode:
            self._auto_reserve_loaded()
        self.random_customers = scenario.get("random_customers", True)
        self.menu_filter = None  # v1.1 day: chỉ các món trong kế hoạch Ngày (DaySim gán)
        self.elapsed = 0
        self.next_customer_tick = int(t["first_customer_tick"])
        self.customer_interval_ticks = max(1, int(round(t["customer_interval_s"] * 60)))
        self._hand_order = None  # lát 4: đơn của món đang cầm (nội bộ)
        # P3: giá đã chốt của món đang cầm; scenario có thể dựng hand {dish_id, base_price}
        h = self.hand
        self._hand_base = h.get("base_price") if isinstance(h, dict) else None
        if isinstance(h, dict):
            self.hand = h.get("dish_id")
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
            if self.item_mode:
                c["reserved"] = []  # cấp theo order_tick rồi id bàn sau khi nạp hết khách
                c["_auto_reserve"] = bool(dish) and c["state"] == "waiting"
            else:
                c["reserved"] = dict(dish["recipe"]) if dish and c["state"] == "waiting" else {}
        elif self.item_mode:
            c["reserved"] = list(c["reserved"])
        return c

    def _auto_reserve_loaded(self):
        """P3: khách scenario thiếu reserved -> cấp theo order_tick rồi id bàn, tươi nhất rồi id nhỏ."""
        for c in sorted(self.customers, key=self._order_key):
            if c.pop("_auto_reserve", False):
                c["reserved"] = self._pick_items(self.menu[c["dish_id"]]["recipe"]) or []

    # ---- Lát 3: giữ chỗ nguyên liệu (Lát 4 dùng available()/release() khi nấu) ----
    def reserved_total(self) -> dict:
        tot = {}
        for c in self.customers:
            if self.item_mode:
                for k in self._kinds_of(c.get("reserved") or []):
                    tot[k] = tot.get(k, 0) + 1
                continue
            for k, n in c.get("reserved", {}).items():
                tot[k] = tot.get(k, 0) + n
        return tot

    def available(self) -> dict:
        """Kho còn dùng được = kho - phần đã giữ chỗ (P3: chỉ cá thể chưa ươn, chưa giữ)."""
        if self.item_mode:
            out = {}
            for it in self._free_items():
                out[it["kind"]] = out.get(it["kind"], 0) + 1
            return out
        res = self.reserved_total()
        return {k: self.stock.get(k, 0) - res.get(k, 0) for k in set(self.stock) | set(res)}

    def cookable_dishes(self) -> list:
        avail = self.available()
        return sorted(d for d, m in self.menu.items()
                      if (self.menu_filter is None or d in self.menu_filter) and all(avail.get(k, 0) >= n for k, n in m["recipe"].items()))

    def release(self, customer):
        customer["reserved"] = [] if self.item_mode else {}

    # ---- P3 (Hoàng Vũ): giữ chỗ theo id cá thể ----
    def _item(self, iid):
        return next((it for it in self.stock if it["id"] == iid), None)

    def _kinds_of(self, item_ids):
        return [it["kind"] for it in (self._item(i) for i in item_ids) if it is not None]

    def _spoiled(self, it) -> bool:
        return it["fresh"] < self.spoiled_below

    def _free_items(self):
        held = {i for c in self.customers for i in (c.get("reserved") or [])}
        return [it for it in self.stock if it["id"] not in held and not self._spoiled(it)]

    def _pick_items(self, recipe):
        """Mỗi loại lấy các cá thể khả dụng tươi nhất, hòa theo id. Thiếu -> None."""
        free = self._free_items()
        out = []
        for kind in sorted(recipe):
            cands = sorted((it for it in free if it["kind"] == kind),
                           key=lambda it: (-it["fresh"], id_key(it["id"])))
            if len(cands) < recipe[kind]:
                return None
            out += [it["id"] for it in cands[:recipe[kind]]]
        return out

    def _reserve(self, c) -> bool:
        """Giữ chỗ (lại) cho đơn của khách; True nếu đủ công thức."""
        recipe = self.menu[c["dish_id"]]["recipe"]
        if not self.item_mode:
            avail = self.available()
            ok = all(avail.get(k, 0) >= n for k, n in recipe.items())
            c["reserved"] = dict(recipe) if ok else {}
            return ok
        c["reserved"] = []
        picked = self._pick_items(recipe)
        c["reserved"] = picked or []
        return picked is not None

    def _reserved_ok(self, c) -> bool:
        recipe = self.menu[c["dish_id"]]["recipe"]
        if not self.item_mode:
            return (all(c.get("reserved", {}).get(k, 0) >= n for k, n in recipe.items())
                    and all(self.stock.get(k, 0) >= n for k, n in recipe.items()))
        items = [self._item(i) for i in c.get("reserved") or []]
        if any(it is None or self._spoiled(it) for it in items):
            return False
        have = {}
        for it in items:
            have[it["kind"]] = have.get(it["kind"], 0) + 1
        return all(have.get(k, 0) >= n for k, n in recipe.items())

    def _consume(self, c) -> list:
        """Bắt đầu nấu: tiêu đúng phần giữ. Trả cá thể đã dùng (sắp theo kind rồi id); kho đếm trả []."""
        recipe = self.menu[c["dish_id"]]["recipe"]
        if not self.item_mode:
            for k, n in recipe.items():
                self.stock[k] = self.stock.get(k, 0) - n
            self.release(c)
            return []
        used_ids = set(c.get("reserved") or [])
        used = [it for it in self.stock if it["id"] in used_ids]
        self.stock = [it for it in self.stock if it["id"] not in used_ids]
        self.release(c)
        return sorted(used, key=lambda it: (it["kind"], id_key(it["id"])))

    def recheck_spoiled(self, events):
        """Gọi SAU bước hao tươi kho quán: đơn có cá thể vừa ươn -> nhả toàn bộ phần giữ và thử giữ lại
        đúng một lần, theo order_tick rồi id bàn; thiếu -> unfulfillable (khách chờ tới hạn)."""
        if not self.item_mode:
            return
        hit = []
        for c in self.customers:
            if c.get("state") != "waiting":
                continue
            items = [self._item(i) for i in c.get("reserved") or []]
            if any(it is not None and self._spoiled(it) for it in items):
                hit.append(c)
        for c in hit:
            c["reserved"] = []
        for c in sorted(hit, key=self._order_key):
            c["order_status"] = "reserved" if self._reserve(c) else "unfulfillable"

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
             "patience_ticks_left": self.patience_ticks, "reserved": [] if self.item_mode else {},
             "order_tick": self.elapsed}  # P2: bếp lấy đơn cũ nhất theo order_tick rồi id bàn
        self._reserve(c)  # giữ nguyên liệu khi gọi món (P3: tươi nhất, hòa theo id)
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
            "stock": (sort_by_id(self.stock) if self.item_mode
                      else {k: self.stock[k] for k in sorted(self.stock) if self.stock[k] > 0}),
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
        self._tick_freshness(events)  # P3 (Hà Anh): hao tươi kho thô + spoiled theo id
        self.recheck_spoiled(events)  # P3 (Vũ): nhả và giữ lại theo id khi phần giữ vừa ươn
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
    # ---- P3 (Hà Anh): độ tươi kho quán + giá theo tươi ----
    def _exact_fresh(self, it):
        f = self._fresh_by_id.get(it["id"])
        return f if f is not None else Fraction(str(it["fresh"]))

    def _tick_freshness(self, events):
        """Kho quán (kể cả hàng đang giữ chỗ) giảm quan_decay_per_s, kẹp đáy 0. Món chín không hao.
        spoiled phát đúng một lần khi đi từ >= ngưỡng xuống < ngưỡng, theo id, location "stock"."""
        if not self._fresh_on:
            return
        exact = {}
        for it in sorted(self.stock, key=lambda x: id_key(x["id"])):
            before = self._exact_fresh(it)
            after = max(Fraction(0), before - self._q_decay)
            exact[it["id"]] = after
            it["fresh"] = float(after)
            if before >= self._spoil_at > after:
                events.append(("spoiled", {"item_id": it["id"], "kind": it["kind"], "location": "stock"}))
        self._fresh_by_id = exact

    def _base_price(self, dish, used):
        """floor(giá niêm yết × trung bình fresh của các cá thể dùng / 100); kho đếm -> giá niêm yết."""
        price = self.menu[dish]["price"]
        if not used:
            return price
        avg = sum((self._exact_fresh(it) for it in used), Fraction(0)) / len(used)
        return math.floor(price * avg / 100)

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
            status = "reserved" if self._reserve(c) else "unfulfillable"
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
        self.hand, self._hand_order, self._hand_base = None, None, None

    @staticmethod
    def _order_key(c):
        return (c.get("order_tick", 0), c["table_id"])

    def _next_order(self):
        """Đơn reserved cũ nhất theo order_tick rồi id bàn, kho thực còn đủ công thức."""
        for c in sorted((c for c in self.customers if c.get("state") == "waiting"), key=self._order_key):
            m = self.menu.get(c.get("dish_id"))
            if m is None:
                continue
            if self._reserved_ok(c):
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
            self._hand_base = s.get("base_price")  # P3: giá chốt đi theo món lên tay
            s.update(state="idle", dish=None, cook_ticks_left=0, ready_ticks=0, order_id=None)
            events.append(("dish_picked", {"stove_id": s["id"], "dish_id": dish}))
            return
        c = self._next_order()
        dish = c["dish_id"]
        used = self._consume(c)  # phần giữ thành món đang nấu (P3: tiêu đúng các id đang giữ)
        s.update(state="cooking", dish=dish, cook_ticks_left=self._ticks(self.menu[dish]["cook_s"]),
                 ready_ticks=0, order_id=c["id"], used_items=used, base_price=self._base_price(dish, used))
        data = {"stove_id": s["id"], "dish_id": dish, "cook_ticks": s["cook_ticks_left"]}
        if self.item_mode:
            data["items"] = [dict(it) for it in used]  # Hà Anh: chốt base_price theo fresh từ used_items
        events.append(("cook_started", data))

    def _serve(self, tb, events):
        q = self.t
        c = self._table_customer(tb)
        dish = self._hand_dish()
        owner = self._customer(self._hand_order) if self._hand_order else None
        if owner is not None and owner is not c and owner.get("state") == "waiting":
            # giao món của đơn khác cùng món: chuyển phần giữ của khách được giao sang đơn gốc
            empty = [] if self.item_mode else {}
            owner["reserved"], c["reserved"] = c.get("reserved") or empty, ([] if self.item_mode else {})
        else:
            self.release(c)
        price = self._hand_base if self._hand_base is not None else self.menu[dish]["price"]  # P3: giá đã chốt
        self._hand_base = None
        pmax = self._ticks(q["patience_s"])
        ratio = c.get("patience_ticks_left", pmax) / pmax
        tip = math.floor(round(price * q["tip_rate"], 9)) if ratio >= q["tip_min_patience_ratio"] else 0
        self.hand, self._hand_order, self._hand_base = None, None, None
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
