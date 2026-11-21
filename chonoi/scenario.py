"""Nạp và kiểm scenario (Contract D, v1.0 & v1.1). Trả về dict của đúng khối theo mode."""

import json
import math

from .errors import BadInput
from .inventory import KINDS_P1, validate_item_list, validate_items

GATHER_KEYS = {"player", "hold", "nodes", "fish", "random_fish", "monsters", "ca_ho", "random_ho", "time_left_ticks"}
CURRENT_KEYS = {"random_current", "current_direction"}
GATHER_PLAYER_KEYS = {"pos", "vel", "heading_deg", "hp", "oxygen_ticks", "zero_oxy_ticks",
                      "invuln_ticks", "catch_cd_ticks", "attack_cd_ticks"}
NODE_KINDS = ("bong_dien_dien", "bong_sung", "keo_neo")
FISH_KINDS = ("ca_linh", "ca_loc", "ca_keo")
MONSTER_STATES = ("patrol", "chase", "recoil", "stunned")
QUAN_PLAYER_KEYS = {"pos", "vel"}
QUAN_KEYS = {"player", "stock", "hand", "stoves", "tables", "customers", "random_customers",
             "reputation", "time_left_ticks"}


def _check_ids(name, arr):
    if not isinstance(arr, list):
        raise BadInput(f"{name} phải là mảng")
    seen = set()
    for e in arr:
        if not isinstance(e, dict) or not isinstance(e.get("id"), str) or not e["id"]:
            raise BadInput(f"{name}: mỗi phần tử cần id (chuỗi khác rỗng)")
        if e["id"] in seen:
            raise BadInput(f"{name}: id trùng {e['id']}")
        seen.add(e["id"])


def load_scenario(path, mode: str, tuning: dict) -> dict:
    if path is None:
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        raise BadInput(f"không đọc được scenario {path}: {e}")
    if mode == "day":
        return _load_day(data, tuning)
    if not isinstance(data, dict) or not set(data) <= {"gather", "quan"}:
        raise BadInput("scenario chỉ được có khối 'gather' hoặc 'quan'")
    if set(data) - {mode}:
        raise BadInput(f"khối sai mode: chạy --mode {mode} chỉ nhận khối '{mode}'")
    return _check_block(data.get(mode, {}), mode, tuning)


DAY_KEYS = {"money", "earned", "reputation", "upgrades", "day_plan"}


def _load_day(data, tuning):
    """v1.1: khối day dựng trạng thái xuyên Ngày; gather/quan là mẫu khởi tạo mỗi Ngày."""
    if not isinstance(data, dict) or not set(data) <= {"day", "gather", "quan"}:
        raise BadInput("scenario day chỉ được có khối 'day', 'gather', 'quan'")
    out = {m: _check_block(data[m], m, tuning, in_day=True) for m in ("gather", "quan") if m in data}
    for k in ("stock", "reputation"):
        if k in out.get("quan", {}):
            raise BadInput(f"cấm quan.{k} khi chạy day (dùng gather.hold / day.reputation)")
    d = data.get("day", {})
    if not isinstance(d, dict) or set(d) - DAY_KEYS:
        raise BadInput(f"khối day chỉ nhận {sorted(DAY_KEYS)}")
    for k in ("money", "earned"):
        if k in d:
            _nonneg_int(f"day.{k}", d[k])
    if ("money" in d) != ("earned" in d) and d.get("money", 0) > 0:
        raise BadInput("có tiền đầu kỳ thì khai cả day.money và day.earned")
    if d.get("money", 0) > d.get("earned", 0):
        raise BadInput("cần 0 <= day.money <= day.earned")
    q = tuning["quan"]
    if "reputation" in d and not (_num(d["reputation"]) and q["reputation_min"] <= d["reputation"] <= q["reputation_max"]):
        raise BadInput("day.reputation ngoài miền uy tín")
    ups = d.get("upgrades", {})
    shop = tuning["shop"]["upgrades"]
    if not isinstance(ups, dict):
        raise BadInput("day.upgrades phải là object")
    for k, v in ups.items():
        if k not in shop:
            raise BadInput(f"day.upgrades: nâng cấp lạ {k}")
        if isinstance(v, bool) or not isinstance(v, int) or not 0 <= v <= len(shop[k]):
            raise BadInput(f"day.upgrades.{k} phải là cấp trong [0, {len(shop[k])}]")
    plans = d.get("day_plan", [])
    if not isinstance(plans, list):
        raise BadInput("day.day_plan phải là mảng")
    seen = set()
    for p in plans:
        if not isinstance(p, dict) or p.get("day") not in range(1, 6) or p["day"] in seen:
            raise BadInput("day.day_plan: mỗi mục cần day duy nhất trong [1, 5]")
        seen.add(p["day"])
        dishes = p.get("dishes")
        if not isinstance(dishes, dict) or not dishes:
            raise BadInput(f"day.day_plan[{p['day']}]: cần dishes")
        for dish, n in dishes.items():
            if dish not in tuning["menu"] or isinstance(n, bool) or not isinstance(n, int) or n <= 0:
                raise BadInput(f"day.day_plan[{p['day']}]: món {dish} phải có trong menu, số suất nguyên dương")
        if "ingredients" in p:
            calc = {}
            for dish, n in dishes.items():
                for k, c in tuning["menu"][dish]["recipe"].items():
                    calc[k] = calc.get(k, 0) + c * n
            if p["ingredients"] != calc:
                raise BadInput(f"day.day_plan[{p['day']}]: ingredients không khớp công thức × số suất")
    out["day"] = d
    return out


def _check_block(block, mode, tuning, in_day=False):
    if not isinstance(block, dict):
        raise BadInput(f"khối {mode} phải là object")
    allowed = GATHER_KEYS if mode == "gather" else QUAN_KEYS
    if mode == "gather" and tuning["gather"].get("current") is not None:
        allowed = allowed | CURRENT_KEYS
    extra = set(block) - allowed
    if extra:
        raise BadInput(f"trường lạ/chưa hỗ trợ trong {mode}: {sorted(extra)}")
    dur = int(round(tuning[mode]["duration_s"] * 60))
    if "time_left_ticks" in block:
        t = block["time_left_ticks"]
        if isinstance(t, bool) or not isinstance(t, int) or not (1 <= t <= dur):
            raise BadInput(f"time_left_ticks phải là số nguyên trong [1, {dur}]")
    if mode == "gather":
        _validate_gather(block, tuning)
    else:
        _validate_quan(block, tuning, in_day=in_day)
    return block


def _num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _nonneg_int(name, v):
    if isinstance(v, bool) or not isinstance(v, int) or v < 0:
        raise BadInput(f"{name} phải là số nguyên không âm")


def _pos(name, pos, bounds, axes=("x", "d")):
    if not (isinstance(pos, list) and len(pos) == 2 and all(_num(c) for c in pos)):
        raise BadInput(f"{name} phải là [{axes[0]}, {axes[1]}]")
    for c, axis in zip(pos, axes):
        lo, hi = bounds[axis]
        if not (lo <= c <= hi):
            raise BadInput(f"{name} nằm ngoài vùng nước ({axis} ∈ [{lo}, {hi}])")


def _validate_gather(b, tuning):
    g = tuning["gather"]
    bounds = g["bounds"]
    for arr in ("nodes", "fish", "monsters"):
        if arr in b:
            _check_ids(arr, b[arr])
    if "random_fish" in b and not isinstance(b["random_fish"], bool):
        raise BadInput("random_fish phải là boolean")
    if "random_current" in b and not isinstance(b["random_current"], bool):
        raise BadInput("random_current phải là boolean")
    if "current_direction" in b and (type(b["current_direction"]) is not int or b["current_direction"] not in (-1, 1)):
        raise BadInput("current_direction phải là -1 hoặc 1")
    if "hold" in b:
        h = b["hold"]
        if "freshness" in tuning:
            validate_item_list(h, name="gather.hold")
        elif not isinstance(h, list) or any(k not in KINDS_P1 for k in h):
            raise BadInput("hold phải là mảng id nguyên liệu hợp lệ")
        if len(h) > g["hold_capacity"]:
            raise BadInput("hold vượt sức chứa")
    p = b.get("player", {})
    if not isinstance(p, dict):
        raise BadInput("player phải là object")
    extra = set(p) - GATHER_PLAYER_KEYS
    if extra:
        raise BadInput(f"trường lạ/chưa hỗ trợ trong gather.player: {sorted(extra)}")
    if "pos" in p:
        _pos("player.pos", p["pos"], bounds)
    if "vel" in p and not (isinstance(p["vel"], list) and len(p["vel"]) == 2 and all(_num(c) for c in p["vel"])):
        raise BadInput("player.vel phải là [x, d]")
    if "heading_deg" in p and not _num(p["heading_deg"]):
        raise BadInput("player.heading_deg phải là số")
    for key in ("invuln_ticks", "catch_cd_ticks", "attack_cd_ticks", "zero_oxy_ticks", "oxygen_ticks", "hp"):
        if key in p:
            _nonneg_int(f"player.{key}", p[key])
    omax = int(round(g["oxygen_max_s"] * 60))
    if "oxygen_ticks" in p and p["oxygen_ticks"] > omax:
        raise BadInput("player.oxygen_ticks vượt oxy tối đa")
    if "hp" in p and not (1 <= p["hp"] <= g["hp_max"]):
        raise BadInput("player.hp phải trong [1, hp_max]")
    if "zero_oxy_ticks" in p:
        pos = p.get("pos", g["start_pos"])
        oxy = p.get("oxygen_ticks", omax)
        if p["zero_oxy_ticks"] > 59:
            raise BadInput("player.zero_oxy_ticks phải trong [0, 59]")
        if p["zero_oxy_ticks"] > 0 and not (oxy == 0 and pos[1] > g["surface_depth"]):
            raise BadInput("player.zero_oxy_ticks > 0 chỉ khi oxy = 0 và đang dưới nước")
    for n in b.get("nodes", []):
        if n.get("kind") not in NODE_KINDS:
            raise BadInput(f"nodes.{n['id']}: kind phải là một trong {NODE_KINDS}")
        _pos(f"nodes.{n['id']}.pos", n.get("pos"), bounds)
        if n["pos"][1] != 0:
            raise BadInput(f"nodes.{n['id']}: nút hái nằm ở mặt nước (d = 0)")
        if "regrow_ticks" in n:
            _nonneg_int(f"nodes.{n['id']}.regrow_ticks", n["regrow_ticks"])
    for f in b.get("fish", []):
        if f.get("kind") not in FISH_KINDS:
            raise BadInput(f"fish.{f['id']}: kind phải là một trong {FISH_KINDS}")
        _pos(f"fish.{f['id']}.pos", f.get("pos"), bounds)
        if f["pos"][1] <= g["surface_depth"]:
            raise BadInput(f"fish.{f['id']}: đàn cá phải ở dưới nước")
        if "heading_deg" in f and not _num(f["heading_deg"]):
            raise BadInput(f"fish.{f['id']}.heading_deg phải là số")
        if "age_ticks" in f:
            _nonneg_int(f"fish.{f['id']}.age_ticks", f["age_ticks"])
    species_cfg = g.get("monsters", {}).get("species", {})
    for m in b.get("monsters", []):
        kind = m.get("kind")
        if kind not in species_cfg:
            raise BadInput(f"monsters.{m['id']}: kind {kind!r} không hỗ trợ")
        sp = species_cfg[kind]
        m_bounds = {"x": bounds["x"], "d": sp["depths"]}
        _pos(f"monsters.{m['id']}.pos", m.get("pos"), m_bounds)
        wps = m.get("waypoints")
        if not isinstance(wps, list) or len(wps) != 2:
            raise BadInput(f"monsters.{m['id']}.waypoints phải có đúng 2 điểm")
        for idx, wp in enumerate(wps):
            _pos(f"monsters.{m['id']}.waypoints[{idx}]", wp, m_bounds)
        t_idx = m.get("target_idx", 1)
        if isinstance(t_idx, bool) or t_idx not in (0, 1):
            raise BadInput(f"monsters.{m['id']}.target_idx phải là 0 hoặc 1")
        st = m.get("state", "patrol")
        if st not in MONSTER_STATES:
            raise BadInput(f"monsters.{m['id']}.state không hợp lệ: {st!r}")
        stl = m.get("state_ticks_left", 0)
        _nonneg_int(f"monsters.{m['id']}.state_ticks_left", stl)
        if st in ("recoil", "stunned") and stl <= 0:
            raise BadInput(f"monsters.{m['id']}: state {st} cần state_ticks_left > 0")
        if st in ("patrol", "chase") and stl != 0:
            raise BadInput(f"monsters.{m['id']}: state {st} không có state_ticks_left > 0")
        rdir = m.get("recoil_dir")
        if st == "recoil":
            if not (isinstance(rdir, list) and len(rdir) == 2 and all(_num(c) for c in rdir)):
                raise BadInput(f"monsters.{m['id']}: recoil cần recoil_dir là vector 2D")
            norm = math.hypot(rdir[0], rdir[1])
            if abs(norm - 1.0) > 0.05:
                raise BadInput(f"monsters.{m['id']}: recoil_dir phải là vector đơn vị")
        elif rdir is not None:
            raise BadInput(f"monsters.{m['id']}: recoil_dir phải là null khi state={st}")


def _validate_quan(b, tuning, in_day=False):
    for arr in ("stoves", "tables", "customers"):
        if arr in b:
            _check_ids(arr, b[arr])
    item_mode = isinstance(b.get("stock"), list)
    if "freshness" in tuning and "stock" in b and not item_mode:
        raise BadInput("contract v1.2: quan.stock phải là mảng cá thể {id, kind, fresh}")
    if item_mode:
        validate_item_list(b["stock"], name="quan.stock")
    elif "stock" in b:
        validate_items(b["stock"])
    p = b.get("player", {})
    if not isinstance(p, dict) or set(p) - QUAN_PLAYER_KEYS:
        raise BadInput("quan.player chỉ có pos và vel")
    qb = tuning["quan"]["bounds"]
    if "pos" in p:
        _pos("player.pos", p["pos"], qb, axes=("x", "z"))
    if "vel" in p and not (isinstance(p["vel"], list) and len(p["vel"]) == 2 and all(_num(c) for c in p["vel"])):
        raise BadInput("player.vel phải là [x, z]")
    table_ids = [c.get("table_id") for c in b.get("customers", [])]
    known = {t["id"] for t in tuning["quan"]["tables"]} | {t.get("id") for t in b.get("tables", [])}
    for c in b.get("customers", []):
        if not isinstance(c.get("table_id"), str) or c["table_id"] not in known:
            raise BadInput(f"customers.{c['id']}: table_id phải là bàn có thật")
    if len(table_ids) != len(set(table_ids)):
        raise BadInput("hai khách cùng bàn")
    menu = tuning["menu"]
    stock = b.get("stock", {})
    reserved = {}
    if item_mode:
        _validate_reserved_ids(b, tuning)
    if "random_customers" in b and not isinstance(b["random_customers"], bool):
        raise BadInput("random_customers phải là boolean")
    for c in b.get("customers", []):
        if c.get("dish_id") not in menu:
            raise BadInput(f"customers.{c['id']}: dish_id phải có trong menu")
        if c.get("state", "waiting") not in ("waiting", "eating"):
            raise BadInput(f"customers.{c['id']}: state phải là waiting hoặc eating")
        if "patience_ticks_left" in c:
            _nonneg_int(f"customers.{c['id']}.patience_ticks_left", c["patience_ticks_left"])
        if "order_tick" in c:
            _nonneg_int(f"customers.{c['id']}.order_tick", c["order_tick"])
        if item_mode:
            continue
        r = c.get("reserved", menu[c["dish_id"]]["recipe"] if c.get("state", "waiting") == "waiting" else {})
        validate_items(r)
        for k, n in r.items():
            reserved[k] = reserved.get(k, 0) + n
    if "stock" in b:
        for k, n in reserved.items():
            if n > stock.get(k, 0):
                raise BadInput(f"khách giữ chỗ {k} vượt kho")
    _validate_quan_lat4(b, tuning)


def _validate_reserved_ids(b, tuning):
    """P3: customers[].reserved là mảng id cá thể: trỏ tới cá thể chưa ươn trong kho, đủ đúng công thức,
    không dùng chung giữa các đơn. Bỏ reserved thì sim tự cấp theo order_tick rồi id bàn."""
    menu = tuning["menu"]
    below = tuning.get("freshness", {}).get("spoiled_below", 30)
    by_id = {it["id"]: it for it in b["stock"]}
    used = set()
    for c in b.get("customers", []):
        if "reserved" not in c:
            continue
        r = c["reserved"]
        if not isinstance(r, list) or not all(isinstance(i, str) for i in r):
            raise BadInput(f"customers.{c['id']}.reserved phải là mảng id cá thể")
        need = dict(menu[c["dish_id"]]["recipe"]) if c.get("state", "waiting") == "waiting" else {}
        have = {}
        for i in r:
            it = by_id.get(i)
            if it is None:
                raise BadInput(f"customers.{c['id']}.reserved: không có cá thể {i} trong kho")
            if it["fresh"] < below:
                raise BadInput(f"customers.{c['id']}.reserved: cá thể {i} đã ươn")
            if i in used:
                raise BadInput(f"customers.{c['id']}.reserved: cá thể {i} đã giữ cho đơn khác")
            used.add(i)
            have[it["kind"]] = have.get(it["kind"], 0) + 1
        if r and have != need:
            raise BadInput(f"customers.{c['id']}.reserved không khớp công thức {c['dish_id']}")


STOVE_STATES = ("idle", "cooking", "ready")


def _validate_quan_lat4(b, tuning):
    """Lát 4: món trên tay, bếp, khách đang ăn phải nhất quán (mâu thuẫn -> mã 2)."""
    menu = tuning["menu"]
    hand = b.get("hand")
    if hand is not None and (not isinstance(hand, str) or hand not in menu):
        raise BadInput("hand phải là null hoặc id món có trong menu")
    known_stoves = {s["id"] for s in tuning["quan"]["stoves"]}
    burn_s = tuning["quan"].get("burn_s")
    burn_ticks = int(round(burn_s * 60)) if burn_s is not None else None
    for s in b.get("stoves", []):
        if s["id"] not in known_stoves:
            raise BadInput(f"stoves.{s['id']}: id bếp không tồn tại")
        st, dish = s.get("state", "idle"), s.get("dish")
        if st not in STOVE_STATES:
            raise BadInput(f"stoves.{s['id']}.state phải là một trong {STOVE_STATES}")
        for key in ("cook_ticks_left", "ready_ticks"):
            if key in s:
                _nonneg_int(f"stoves.{s['id']}.{key}", s[key])
        if st == "idle" and (dish is not None or s.get("cook_ticks_left", 0) or s.get("ready_ticks", 0)):
            raise BadInput(f"stoves.{s['id']}: bếp idle không được có món/đếm giờ")
        if st != "idle" and dish not in menu:
            raise BadInput(f"stoves.{s['id']}: bếp {st} phải có dish trong menu")
        if st == "cooking" and s.get("cook_ticks_left", 0) < 1:
            raise BadInput(f"stoves.{s['id']}: bếp cooking cần cook_ticks_left >= 1")
        if st == "ready" and burn_ticks is not None and s.get("ready_ticks", 0) > burn_ticks:
            raise BadInput(f"stoves.{s['id']}: ready_ticks vượt ngưỡng cháy {burn_ticks}")
    for c in b.get("customers", []):
        if "dish_id" in c and c["dish_id"] not in menu:
            raise BadInput(f"customers.{c['id']}: dish_id không có trong menu")
        if c.get("state") == "eating":
            for key in ("price", "tip", "eat_ticks_left"):
                if key not in c:
                    raise BadInput(f"customers.{c['id']}: khách eating thiếu {key}")
                _nonneg_int(f"customers.{c['id']}.{key}", c[key])
            if c["eat_ticks_left"] < 1:
                raise BadInput(f"customers.{c['id']}: eat_ticks_left phải >= 1")
