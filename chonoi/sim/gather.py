"""Buổi sáng — Lặn & Hái (`gather`, Test Contract v1.1).

Thứ tự xử lý trong một tick (mục 4.5 TICKET-02):
  1. Đồng hồ, cooldown, giảm bất tử và hồi nút (`node_regrown`).
  2. Bơi + chặn mép -> `dive` / `surface` -> oxy, `oxygen_empty`, ngạt (`choke`) -> nếu Máu về 0: `faint`, `gather_end(fainted)` và kết thúc ngay.
  3. Cập nhật thủy quái theo id và xét tối đa 1 `monster_hit` -> nếu Máu về 0: `faint(cause="monster")`, `gather_end(fainted)` và kết thúc ngay.
  4. Tương tác (`interact`): xét cập bến (`docked`) TRƯỚC hái nút (`gather` / `hold_full`).
  5. Bắt cá (`catch`) theo vị trí cá TRƯỚC khi bơi (`fish_caught` / `hold_full`).
  6. Xét hết giờ (`time_left_ticks <= 0` -> `gather_end(time)`).
  7. Nếu còn giờ: đàn cá bơi (đổi hướng theo seed ở bước bơi 120, 240... trước khi di chuyển, phản xạ mép) và sinh thêm cá theo lịch tại `phase_tick = 360 * k` (`fish_spawned`).
"""

import math

from ..ids import sort_by_id
from ..inventory import hold_to_items
from .monsters import init_monsters, snapshot_monsters, step_monsters
from .ramp import ramp_velocity

TICK = 60.0
AXES = ("x", "d")
FISH_ORDER = ("ca_linh", "ca_loc", "ca_keo")


class GatherSim:
    mode = "gather"
    phase = "gather"

    def __init__(self, tuning, scenario, streams, ids, day=1):
        t = tuning["gather"]
        self.t = t
        self.rng = streams
        self.ids = ids
        self.day = day
        self.phase_tick = 0
        p = scenario.get("player", {})
        self.pos = [float(c) for c in p.get("pos", t["start_pos"])]
        self.vel = [float(c) for c in p.get("vel", [0.0, 0.0])]
        self._tgt = None
        self._ramp_left = 0
        self.heading = float(p.get("heading_deg", t["start_heading_deg"]))
        self.oxygen_max = int(round(t["oxygen_max_s"] * TICK))
        self.oxygen_ticks = p.get("oxygen_ticks", self.oxygen_max)
        self.hp = p.get("hp", t["hp_max"])
        self.zero_oxy_ticks = p.get("zero_oxy_ticks", 0)
        self.invuln_ticks = p.get("invuln_ticks", 0)
        self.catch_cd_ticks = p.get("catch_cd_ticks", 0)
        self.hold = list(scenario.get("hold", []))  # thứ tự nhặt, cuối mảng là mới nhất
        self.time_left_ticks = scenario.get("time_left_ticks", int(round(t["duration_s"] * TICK)))

        src_nodes = scenario["nodes"] if "nodes" in scenario else t["nodes"]
        self.nodes = [{"id": n["id"], "kind": n["kind"], "pos": [float(c) for c in n["pos"]],
                       "regrow_ticks": n.get("regrow_ticks", 0)} for n in src_nodes]
        for e in self.nodes:
            ids.reserve(e["id"])

        self.random_fish = scenario.get("random_fish", True)
        self._fish_moves = bool(self.random_fish)
        self.fish = self._init_fish(scenario)
        for e in self.fish:
            ids.reserve(e["id"])

        self.monsters = init_monsters(t, scenario, ids, day=day)

        self.money = 0
        self.earned = 0
        self.reputation = tuning["quan"]["reputation_initial"]
        self.done = False
        self.reason = None

    def _init_fish(self, scenario: dict) -> list:
        if "fish" in scenario:
            return [
                {
                    "id": f["id"],
                    "kind": f["kind"],
                    "pos": [float(c) for c in f["pos"]],
                    "heading_deg": float(f.get("heading_deg", 0.0)),
                    "age_ticks": int(f.get("age_ticks", 0)),
                }
                for f in scenario["fish"]
            ]
        if not self.random_fish:
            return []
        fi = self.t.get("fish_initial", 8)
        if isinstance(fi, list):
            return [
                {
                    "id": f["id"],
                    "kind": f["kind"],
                    "pos": [float(c) for c in f["pos"]],
                    "heading_deg": float(f.get("heading_deg", 0.0)),
                    "age_ticks": int(f.get("age_ticks", 0)),
                }
                for f in fi
            ]
        # v1.1: sinh đầu ca `fi` (8) đàn ở 8 điểm hình học khác nhau
        count = int(fi)
        used_points = set()
        out = []
        for _ in range(count):
            picked = self._pick_spawn_candidate(used_points)
            if picked is None:
                break
            kind, pt, heading = picked
            used_points.add((pt[0], pt[1]))
            fid = self.ids.new("F")
            out.append({
                "id": fid,
                "kind": kind,
                "pos": [float(pt[0]), float(pt[1])],
                "heading_deg": heading,
                "age_ticks": 0,
            })
        return out

    def _candidate_points_for_kind(self, kind: str, existing_positions, clearance: float) -> list:
        xs = self.t.get("fish_spawn_x", [15, 30, 45, 60, 75, 90])
        ds = self.t.get("fish_spawn_depths", {}).get(kind, [])
        pts = []
        for x in xs:
            for d in ds:
                pt = (float(x), float(d))
                if all(math.dist(pt, ep) > clearance for ep in existing_positions):
                    pts.append(pt)
        return pts

    def _pick_spawn_candidate(self, used_points_set=None):
        """Chọn (kind, (x, d), heading_deg) theo trọng số loài chuẩn hóa và điểm hợp lệ."""
        rng = self.rng.get("fish_spawn")
        weights_map = self.t.get("fish_weights", {"ca_linh": 0.4, "ca_loc": 0.3, "ca_keo": 0.3})
        clearance = float(self.t.get("fish_spawn_clearance", 1.0))
        if used_points_set is not None:
            existing = list(used_points_set)
            clearance = 0.0  # đầu ca: 8 điểm hình học khác nhau (dist > 0)
        else:
            existing = [(f["pos"][0], f["pos"][1]) for f in self.fish]

        valid_by_kind = {}
        for k in FISH_ORDER:
            if k not in weights_map:
                continue
            pts = self._candidate_points_for_kind(k, existing, clearance)
            if pts:
                valid_by_kind[k] = pts
        if not valid_by_kind:
            return None

        total_w = sum(float(weights_map[k]) for k in valid_by_kind)
        r = rng.random() * total_w
        acc = 0.0
        chosen_kind = next(iter(valid_by_kind))
        for k in FISH_ORDER:
            if k not in valid_by_kind:
                continue
            acc += float(weights_map[k])
            if r <= acc:
                chosen_kind = k
                break

        pt = rng.choice(valid_by_kind[chosen_kind])
        heading = rng.uniform(0.0, 360.0)
        return chosen_kind, pt, heading

    # --- giao diện cho runner -------------------------------------------------
    def inventory_items(self) -> dict:
        return hold_to_items(self.hold)

    def snapshot(self) -> dict:
        return {
            "player": {"pos": self.pos, "vel": self.vel, "heading_deg": self.heading,
                       "oxygen_ticks": self.oxygen_ticks, "oxygen_max_ticks": self.oxygen_max,
                       "hp": self.hp, "hp_max": self.t["hp_max"], "zero_oxy_ticks": self.zero_oxy_ticks,
                       "invuln_ticks": self.invuln_ticks, "catch_cd_ticks": self.catch_cd_ticks,
                       "at_surface": self._at_surface()},
            "hold": self.hold, "hold_count": len(self.hold),
            "hold_capacity": self.t["hold_capacity"],
            "nodes": [{"id": n["id"], "pos": n["pos"], "kind": n["kind"],
                       "ready": n["regrow_ticks"] == 0, "regrow_ticks": n["regrow_ticks"]}
                      for n in sort_by_id(self.nodes)],
            "fish": [{"id": f["id"], "pos": f["pos"], "kind": f["kind"], "heading_deg": f["heading_deg"],
                      "age_ticks": f.get("age_ticks", 0)}
                     for f in sort_by_id(self.fish)],
            "monsters": snapshot_monsters(self.monsters),
        }

    # --- một bước ---------------------------------------------------------------
    def step(self, inp):
        events = []
        self.phase_tick += 1
        # 1. đồng hồ và hàng có sẵn: giảm bộ đếm, nút mọc lại
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        self.invuln_ticks = max(0, self.invuln_ticks - 1)
        self.catch_cd_ticks = max(0, self.catch_cd_ticks - 1)
        for n in sort_by_id(self.nodes):
            if n["regrow_ticks"] > 0:
                n["regrow_ticks"] -= 1
                if n["regrow_ticks"] == 0:
                    events.append(("node_regrown", {"node_id": n["id"]}))
        # 2. bơi + chặn mép + oxy + ngạt
        was_at_surface = self._at_surface()
        self._move(inp)
        at_surface = self._at_surface()
        if at_surface != was_at_surface:
            events.append(("surface" if at_surface else "dive", {"pos": self.pos.copy()}))
        self._update_oxygen(at_surface, events)
        if self.hp == 0:
            lost = self._lose_lifo(len(self.hold))
            events.append(("faint", {"pos": self.pos.copy(), "lost": lost, "hp": 0}))
            self._finish("fainted", events)
            return events
        # 2b. thủy quái (Cá Sấu / Rắn Hổ Mây)
        if step_monsters(self, events):
            return events
        # 3. interact: bến trước, rồi hái
        if inp.pressed("interact"):
            if self._in_dock():
                self._finish("docked", events)
                return events
            if self._at_surface():
                node = self._nearest((n for n in self.nodes if n["regrow_ticks"] == 0),
                                     self.t["interact_radius"])
                if node is not None:
                    amount = self.t["node_yield"]
                    free = self.t["hold_capacity"] - len(self.hold)
                    if free < amount:
                        events.append(("hold_full", {"action": "gather", "node_id": node["id"],
                                                     "required": amount, "free": free}))
                    else:
                        self.hold.extend([node["kind"]] * amount)
                        node["regrow_ticks"] = int(round(self.t["regrow_s"] * TICK))
                        events.append(("gather", {"node_id": node["id"], "kind": node["kind"],
                                                  "amount": amount}))
        # 4. bắt cá (theo vị trí cá trước khi bơi)
        if inp.pressed("catch"):
            if self.catch_cd_ticks == 0 and not self._at_surface():
                fish = self._nearest(self.fish, self.t["catch_radius"])
                if fish is not None:
                    amount = self.t["fish_yield"][fish["kind"]]
                    free = self.t["hold_capacity"] - len(self.hold)
                    if free < amount:
                        events.append(("hold_full", {"action": "catch", "fish_id": fish["id"],
                                                     "required": amount, "free": free}))
                    else:
                        self.hold.extend([fish["kind"]] * amount)
                        self.fish.remove(fish)
                        self.catch_cd_ticks = int(round(self.t["catch_cooldown_s"] * TICK))
                        events.append(("fish_caught", {"fish_id": fish["id"], "kind": fish["kind"],
                                                       "yield": amount}))
        # 5. hết giờ
        if self.time_left_ticks <= 0:
            self._finish("time", events)
            return events
        # 6. nếu còn giờ: cá bơi và sinh thêm theo lịch
        if self._fish_moves:
            self._step_fish()
            self._spawn_fish_if_due(events)
            return events
        # 6. nếu còn giờ: cá bơi và sinh thêm theo lịch
        if self.random_fish:
            self._step_fish()
            self._spawn_fish_if_due(events)
        return events

    # --- cá bơi & sinh thêm (v1.1) ---------------------------------------------
    def _step_fish(self):
        speed = float(self.t.get("fish_speed", 1.5))
        step_dist = speed / TICK
        turn_ticks = int(self.t.get("fish_turn_ticks", 120))
        x_lo, x_hi = [float(c) for c in self.t.get("fish_x", [4, 96])]
        depths_map = self.t.get("fish_depths", {"ca_linh": [3, 12], "ca_loc": [8, 20], "ca_keo": [22, 28]})
        rng = self.rng.get("fish_turn")

        for f in sort_by_id(self.fish):
            f["age_ticks"] = f.get("age_ticks", 0) + 1
            if turn_ticks > 0 and f["age_ticks"] % turn_ticks == 0:
                f["heading_deg"] = rng.uniform(0.0, 360.0)

            rad = math.radians(f["heading_deg"])
            vx = math.cos(rad)
            vd = math.sin(rad)
            nx = f["pos"][0] + vx * step_dist
            nd = f["pos"][1] + vd * step_dist
            d_lo, d_hi = [float(c) for c in depths_map.get(f["kind"], [1, 30])]

            flipped_x = False
            flipped_d = False
            while nx < x_lo or nx > x_hi:
                if nx < x_lo:
                    nx = x_lo + (x_lo - nx)
                else:
                    nx = x_hi - (nx - x_hi)
                vx = -vx
                flipped_x = not flipped_x
            while nd < d_lo or nd > d_hi:
                if nd < d_lo:
                    nd = d_lo + (d_lo - nd)
                else:
                    nd = d_hi - (nd - d_hi)
                vd = -vd
                flipped_d = not flipped_d

            f["pos"][0] = min(x_hi, max(x_lo, nx))
            f["pos"][1] = min(d_hi, max(d_lo, nd))
            if flipped_x or flipped_d:
                f["heading_deg"] = math.degrees(math.atan2(vd, vx)) % 360.0

    def _spawn_fish_if_due(self, events):
        spawn_ticks = int(self.t.get("fish_spawn_ticks", 360))
        fish_max = int(self.t.get("fish_max", 12))
        if spawn_ticks <= 0 or self.phase_tick % spawn_ticks != 0:
            return
        if len(self.fish) >= fish_max:
            return
        picked = self._pick_spawn_candidate(used_points_set=None)
        if picked is None:
            return
        kind, pt, heading = picked
        fid = self.ids.new("F")
        new_f = {
            "id": fid,
            "kind": kind,
            "pos": [float(pt[0]), float(pt[1])],
            "heading_deg": heading,
            "age_ticks": 0,
        }
        self.fish.append(new_f)
        events.append(("fish_spawned", {"id": fid, "kind": kind, "pos": [float(pt[0]), float(pt[1])]}))

    # --- tiện ích ---------------------------------------------------------------
    def _nearest(self, entities, radius):
        candidates = [e for e in sort_by_id(entities) if math.dist(self.pos, e["pos"]) <= radius]
        return min(candidates, key=lambda e: math.dist(self.pos, e["pos"]), default=None)

    def _at_surface(self) -> bool:
        return self.pos[1] <= self.t["surface_depth"]

    def _update_oxygen(self, at_surface, events):
        if at_surface:
            self.oxygen_ticks = min(self.oxygen_max, self.oxygen_ticks + self.t["oxygen_refill_per_tick"])
            self.zero_oxy_ticks = 0
            return

        previous_oxygen = self.oxygen_ticks
        self.oxygen_ticks = max(0, previous_oxygen - 1)
        if self.oxygen_ticks > 0:
            self.zero_oxy_ticks = 0
            return
        if previous_oxygen > 0:
            events.append(("oxygen_empty", {}))
        self.zero_oxy_ticks += 1
        if self.zero_oxy_ticks >= self.t["choke_interval_ticks"]:
            self.zero_oxy_ticks = 0
            self.hp -= 1
            events.append(("choke", {"hp": self.hp}))

    def _lose_lifo(self, n: int) -> list:
        """Lát 2 (Bảo): bỏ n món mới nhặt nhất khỏi giỏ (LIFO), trả về theo thứ tự mất: mới nhất trước.

        Điểm duy nhất làm mất hàng (ngất do ngạt, `monster_hit`, ngất do quái). Phần tử giỏ là
        mã nguyên liệu (v1.0–1.1) hoặc cá thể dict (v1.2); dict được sao chép để payload sự kiện
        không bị đổi theo nếu giỏ còn tham chiếu.
        """
        n = max(0, min(int(n), len(self.hold)))
        lost = []
        for _ in range(n):
            item = self.hold.pop()
            lost.append(dict(item) if isinstance(item, dict) else item)
        return lost

    def _in_dock(self) -> bool:
        return math.dist(self.pos, self.t["dock_pos"]) <= self.t["dock_radius"]

    def _finish(self, reason, events):
        self.done = True
        self.reason = reason
        events.append(("gather_end", {"reason": reason, "inventory": {"items": self.inventory_items()}}))

    def _move(self, inp):
        speed = self.t["swim_speed"]
        mx, md = inp.move
        self.vel = ramp_velocity(self, (mx * speed, md * speed), int(self.t["ramp_max_ticks"]))
        if (mx, md) != (0.0, 0.0):
            self.heading = math.degrees(math.atan2(md, mx)) % 360
        b = self.t["bounds"]
        for i, axis in enumerate(AXES):
            self.pos[i] += self.vel[i] / TICK
            lo, hi = b[axis]
            if self.pos[i] <= lo:
                self.pos[i] = lo
                self.vel[i] = max(0.0, self.vel[i])
            elif self.pos[i] >= hi:
                self.pos[i] = hi
                self.vel[i] = min(0.0, self.vel[i])
