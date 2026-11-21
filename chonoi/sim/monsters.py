"""Thủy quái (Cá Sấu Năm Chèo & Rắn Hổ Mây) cho GatherSim (Phase 2 — TICKET-02 mục 1.2 & Mở rộng snake).

Luật:
- Mỗi quái có: id, kind, pos [x, d], waypoints [[x0, d0], [x1, d1]], target_idx (0|1),
  state ("patrol" | "chase" | "recoil" | "stunned"), state_ticks_left (int), recoil_dir ([ux, ud] hoặc None).
- Thứ tự mỗi tick (sau khi người chơi đã di chuyển & tính oxy/ngạt):
  1. Cập nhật chuyển động quái theo id (sort_by_id):
     - stunned: giảm state_ticks_left 1; nếu về 0 chuyển sang patrol (không di chuyển trong bước đang choáng).
     - recoil: lùi theo recoil_dir mỗi bước recoil_dist / recoil_ticks (2/60 m), chặn mép x và depths của loài;
       giảm state_ticks_left 1; nếu về 0 chuyển sang patrol (xét phát hiện/chạm từ bước kế).
     - patrol / chase:
       * Xét chuyển trạng thái trước khi bơi:
         - Nếu đang patrol: người chơi ở d >= d_min của loài và dist(player, monster) <= detect_radius -> chuyển sang chase.
         - Nếu đang chase: dist(player, monster) > exit_radius hoặc người chơi ở d < d_min của loài -> trở về patrol.
       * Di chuyển:
         - Nếu chase: bơi về phía người chơi ở tốc độ chase_speed (chặn mép x và depths của loài).
         - Nếu patrol: đi ở tốc độ patrol_speed tới waypoints[target_idx]; nếu chạm waypoint (khoảng cách <= bước đi),
           đặt pos = waypoint và đổi target_idx = 1 - target_idx cho bước sau.
  2. Xét va chạm (hit):
     - Chỉ khi người chơi ở dưới ngưỡng d >= d_min của loài, khoảng cách <= hit_radius (1.5 m),
       quái không ở trạng thái recoil/stunned, và người chơi hết bất tử (player.invuln_ticks == 0).
     - Mỗi bước tối đa MỘT hit: chọn con gần nhất trong các con đủ điều kiện, hòa theo id.
     - Khi hit:
       * player.hp -= 1
       * Mất k = floor(len(hold) * loss_ratio) nguyên liệu theo LIFO (nhặt sau mất trước).
       * player.invuln_ticks = invuln_ticks (90).
       * Quái gây hit chuyển sang state = "recoil", state_ticks_left = recoil_ticks (60),
         recoil_dir = vector đơn vị hướng từ người chơi tới quái lúc chạm (trùng tâm dùng [1.0, 0.0]).
       * Phát sự kiện ("monster_hit", {"monster_id": m["id"], "hp": player.hp, "lost": lost_list, "pos": player.pos.copy()}).
"""

import math

from ..ids import sort_by_id

TICK = 60.0


def init_monsters(gather_tuning: dict, scenario: dict, ids, day: int = 1) -> list:
    m_cfg = gather_tuning.get("monsters", {})
    species_map = m_cfg.get("species", {})
    if "monsters" in scenario:
        raw = scenario["monsters"]
    else:
        raw = [s for s in m_cfg.get("spawns", []) if s.get("from_day", 1) <= day]
    out = []
    for m in raw:
        kind = m["kind"]
        if kind not in species_map:
            continue
        wps = [[float(c) for c in wp] for wp in m["waypoints"]]
        pos = [float(c) for c in m.get("pos", wps[0])]
        st = m.get("state", "patrol")
        stl = int(m.get("state_ticks_left", 0))
        rdir = [float(c) for c in m["recoil_dir"]] if m.get("recoil_dir") is not None else None
        t_idx = int(m.get("target_idx", 1))
        out.append({
            "id": m["id"],
            "kind": kind,
            "pos": pos,
            "waypoints": wps,
            "target_idx": t_idx,
            "state": st,
            "state_ticks_left": stl,
            "recoil_dir": rdir,
        })
        ids.reserve(m["id"])
    return sort_by_id(out)


def snapshot_monsters(monsters: list) -> list:
    return [
        {
            "id": m["id"],
            "kind": m["kind"],
            "pos": list(m["pos"]),
            "waypoints": [list(wp) for wp in m["waypoints"]],
            "target_idx": m["target_idx"],
            "state": m["state"],
            "state_ticks_left": m["state_ticks_left"],
            "recoil_dir": list(m["recoil_dir"]) if m["recoil_dir"] is not None else None,
        }
        for m in sort_by_id(monsters)
    ]


def _clamp_monster_pos(pos: list, x_bounds: list, d_bounds: list):
    pos[0] = min(float(x_bounds[1]), max(float(x_bounds[0]), pos[0]))
    pos[1] = min(float(d_bounds[1]), max(float(d_bounds[0]), pos[1]))


def _unit_away(from_pos: list, to_pos: list) -> list:
    dx = to_pos[0] - from_pos[0]
    dd = to_pos[1] - from_pos[1]
    dist = math.hypot(dx, dd)
    if dist <= 1e-9:
        return [1.0, 0.0]
    return [dx / dist, dd / dist]


def step_monsters(sim, events: list):
    """Cập nhật quái và xét tối đa 1 monster_hit. Trả về True nếu người chơi bị hit làm hp == 0 (ngất)."""
    m_cfg = sim.t.get("monsters", {})
    species_map = m_cfg.get("species", {})
    if not sim.monsters or not species_map:
        return False

    x_bounds = sim.t["bounds"]["x"]
    p_pos = sim.pos
    eligible_for_hit = []

    for m in sort_by_id(sim.monsters):
        sp = species_map[m["kind"]]
        d_bounds = sp["depths"]
        d_min = d_bounds[0]
        st = m["state"]

        if st == "stunned":
            m["state_ticks_left"] = max(0, m["state_ticks_left"] - 1)
            if m["state_ticks_left"] == 0:
                m["state"] = "patrol"
                m["recoil_dir"] = None
            continue

        if st == "recoil":
            step_dist = float(sp["recoil_dist"]) / max(1, int(sp["recoil_ticks"]))
            rdir = m["recoil_dir"] or [1.0, 0.0]
            m["pos"][0] += rdir[0] * step_dist
            m["pos"][1] += rdir[1] * step_dist
            _clamp_monster_pos(m["pos"], x_bounds, d_bounds)
            m["state_ticks_left"] = max(0, m["state_ticks_left"] - 1)
            if m["state_ticks_left"] == 0:
                m["state"] = "patrol"
                m["recoil_dir"] = None
            continue

        # patrol hoặc chase: xét chuyển trạng thái
        dist_to_player = math.dist(m["pos"], p_pos)
        player_in_depth = p_pos[1] >= d_min
        if st == "patrol":
            if player_in_depth and dist_to_player <= sp["detect_radius"]:
                st = "chase"
                m["state"] = "chase"
        elif st == "chase":
            if (not player_in_depth) or dist_to_player > sp["exit_radius"]:
                st = "patrol"
                m["state"] = "patrol"

        # Di chuyển
        if st == "chase":
            step_dist = float(sp["chase_speed"]) / TICK
            dx = p_pos[0] - m["pos"][0]
            dd = p_pos[1] - m["pos"][1]
            d_len = math.hypot(dx, dd)
            if d_len > 1e-9:
                if d_len <= step_dist:
                    m["pos"][0], m["pos"][1] = p_pos[0], p_pos[1]
                else:
                    m["pos"][0] += (dx / d_len) * step_dist
                    m["pos"][1] += (dd / d_len) * step_dist
            _clamp_monster_pos(m["pos"], x_bounds, d_bounds)
        else:
            step_dist = float(sp["patrol_speed"]) / TICK
            target = m["waypoints"][m["target_idx"]]
            dx = target[0] - m["pos"][0]
            dd = target[1] - m["pos"][1]
            d_len = math.hypot(dx, dd)
            if d_len <= step_dist + 1e-9:
                m["pos"][0], m["pos"][1] = float(target[0]), float(target[1])
                m["target_idx"] = 1 - m["target_idx"]
            else:
                m["pos"][0] += (dx / d_len) * step_dist
                m["pos"][1] += (dd / d_len) * step_dist
            _clamp_monster_pos(m["pos"], x_bounds, d_bounds)

        # Kiểm tra điều kiện gây hit sau khi cả hai đã di chuyển
        after_dist = math.dist(m["pos"], p_pos)
        if p_pos[1] >= d_min and after_dist <= sp["hit_radius"]:
            eligible_for_hit.append((after_dist, m))

    # Xét tối đa 1 hit nếu người chơi không bất tử
    if sim.invuln_ticks == 0 and eligible_for_hit:
        # Chọn con gần nhất, hòa theo id (eligible_for_hit đã duyệt theo sort_by_id)
        _, hitter = min(eligible_for_hit, key=lambda item: item[0])
        sp = species_map[hitter["kind"]]
        sim.hp = max(0, sim.hp - 1)
        loss_ratio = float(m_cfg.get("loss_ratio", 0.5))
        lost = sim._lose_lifo(math.floor(len(sim.hold) * loss_ratio))
        sim.invuln_ticks = int(m_cfg.get("invuln_ticks", 90))
        hitter["state"] = "recoil"
        hitter["state_ticks_left"] = int(sp["recoil_ticks"])
        hitter["recoil_dir"] = _unit_away(p_pos, hitter["pos"])
        events.append((
            "monster_hit",
            {
                "monster_id": hitter["id"],
                "hp": sim.hp,
                "lost": lost,
                "pos": sim.pos.copy(),
            },
        ))
        if sim.hp == 0:
            faint_lost = sim._lose_lifo(len(sim.hold))
            events.append((
                "faint",
                {
                    "pos": sim.pos.copy(),
                    "cause": "monster",
                    "lost": faint_lost,
                    "hp": 0,
                },
            ))
            sim._finish("fainted", events)
            return True

    return False
