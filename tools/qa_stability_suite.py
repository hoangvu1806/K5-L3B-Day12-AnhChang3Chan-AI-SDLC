"""QA Stability, Fuzz, Invariant, Determinism & Performance Suite (QA Lead: double-n-021).

Chạy 5 lớp kiểm chứng độ ổn định toàn diện cho Quán Ăn Chợ Nổi (không cần cài thư viện ngoài):
  1. Fuzz / Monkey Testing: sinh nhiều kịch bản input ngẫu nhiên có seed (move, interact, catch)
     và chạy headless tới hết ca cho cả `gather` và `quan`.
  2. Invariant Checking: kiểm tra các bất biến vật lý & kinh doanh trên MỌI dòng snapshot.
  3. Determinism Verification: chạy 2 lần độc lập cùng seed + inputs, so khớp SHA-256 từng byte.
  4. Performance & Memory Soak: đo tốc độ (ticks/giây) và bộ nhớ đỉnh (tracemalloc) cho full ca 180s (10,800 ticks).
  5. Live HTTP Server Stress: bắn liên tục GET /state và POST /input vào `chonoi.live` kiểm tra ổn định & tắt sạch.

Cách chạy:
    python tools/qa_stability_suite.py
    python tools/qa_stability_suite.py --seeds 5 --ticks 1800 --out docs/proof/phase-1/stability_report.md
"""

import argparse
import hashlib
import json
import os
import platform
import random
import shlex
import subprocess
import sys
import tempfile
import time
import tracemalloc
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from chonoi.contract import load_contract  # noqa: E402
from chonoi.inputs import InputPlayer  # noqa: E402
from chonoi.live import LiveGame, LiveServer  # noqa: E402
from chonoi.runner import Session  # noqa: E402


def _headless_cmd() -> list:
    with open(os.path.join(ROOT, "game.contract.json"), encoding="utf-8") as f:
        cmd = shlex.split(json.load(f)["headless_cmd"])
    if cmd and cmd[0] in ("python", "python3"):
        cmd[0] = sys.executable
    return cmd


def _sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _generate_fuzz_frames(seed: int, total_ticks: int, mode: str) -> dict:
    rng = random.Random(seed * 9973 + (1 if mode == "gather" else 2))
    frames = []
    t = 0
    while t < total_ticks:
        mx = rng.choice([-1, -0.5, 0, 0.5, 1])
        my = rng.choice([-1, -0.5, 0, 0.5, 1])
        fr = {"tick": t, "move": [mx, my]}
        if rng.random() < 0.35:
            fr["interact"] = rng.choice([True, False])
        if mode == "gather" and rng.random() < 0.35:
            fr["catch"] = rng.choice([True, False])
        frames.append(fr)
        t += rng.randint(1, 25)
    return {"frames": frames}


def _check_invariants(jsonl_path: str, mode: str, tuning: dict) -> list:
    """Kiểm tra toàn bộ bất biến trên mọi dòng snapshot và dòng end."""
    violations = []
    g = tuning["gather"]
    q = tuning["quan"]
    omax = int(round(g["oxygen_max_s"] * 60))
    last_tick = -1
    end_count = 0

    with open(jsonl_path, encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except ValueError as e:
                violations.append(f"L{lineno}: JSON hỏng ({e})")
                continue

            rtype = row.get("type")
            if rtype == "end":
                end_count += 1
                continue
            if rtype != "snapshot":
                continue

            tick = row.get("tick", -1)
            if tick < last_tick:
                violations.append(f"L{lineno}: tick giảm ({tick} < {last_tick})")
            last_tick = tick

            if row.get("time_left_ticks", -1) < 0:
                violations.append(f"tick {tick}: time_left_ticks âm ({row.get('time_left_ticks')})")

            rep = row.get("reputation", 0)
            if not (q["reputation_min"] - 1e-6 <= rep <= q["reputation_max"] + 1e-6):
                violations.append(f"tick {tick}: reputation ngoài [{q['reputation_min']}, {q['reputation_max']}]: {rep}")

            p = row.get("player", {})
            pos = p.get("pos", [0, 0])
            if mode == "gather":
                bx, bd = g["bounds"]["x"], g["bounds"]["d"]
                if not (bx[0] - 1e-6 <= pos[0] <= bx[1] + 1e-6 and bd[0] - 1e-6 <= pos[1] <= bd[1] + 1e-6):
                    violations.append(f"tick {tick}: player.pos ngoài bounds gather: {pos}")
                oxy = p.get("oxygen_ticks", 0)
                if not (0 <= oxy <= omax):
                    violations.append(f"tick {tick}: oxygen_ticks ngoài [0, {omax}]: {oxy}")
                hp = p.get("hp", 0)
                if not (0 <= hp <= g["hp_max"]):
                    violations.append(f"tick {tick}: hp ngoài [0, {g['hp_max']}]: {hp}")
                hold = row.get("hold", [])
                if len(hold) > g["hold_capacity"]:
                    violations.append(f"tick {tick}: hold vượt sức chứa ({len(hold)} > {g['hold_capacity']})")
                if row.get("hold_count") != len(hold):
                    violations.append(f"tick {tick}: hold_count ({row.get('hold_count')}) != len(hold) ({len(hold)})")
            else:
                bx, bz = q["bounds"]["x"], q["bounds"]["z"]
                if not (bx[0] - 1e-6 <= pos[0] <= bx[1] + 1e-6 and bz[0] - 1e-6 <= pos[1] <= bz[1] + 1e-6):
                    violations.append(f"tick {tick}: player.pos ngoài bounds quan: {pos}")
                stock = row.get("stock", {})
                for k, v in stock.items():
                    if not isinstance(v, int) or v <= 0:
                        violations.append(f"tick {tick}: stock[{k}] không dương ({v})")
                customers = row.get("customers", [])
                tables_used = [c.get("table_id") for c in customers]
                if len(tables_used) != len(set(tables_used)):
                    violations.append(f"tick {tick}: 2 khách ngồi cùng 1 bàn ({tables_used})")
                for c in customers:
                    if c.get("patience_ticks_left", 0) < 0:
                        violations.append(f"tick {tick}: khách {c.get('id')} có patience âm")
                if row.get("money", 0) < 0:
                    violations.append(f"tick {tick}: money âm ({row.get('money')})")

            if len(violations) >= 20:
                violations.append("... (cắt bớt sau 20 vi phạm)")
                break

    if end_count != 1:
        violations.append(f"Số dòng type='end' phải là 1 (thực tế: {end_count})")
    return violations


def run_fuzz_and_invariants(seeds: int, ticks: int, tuning: dict) -> dict:
    cmd = _headless_cmd()
    results = []
    passed = 0
    total = seeds * 2
    with tempfile.TemporaryDirectory() as tmp:
        for mode in ("gather", "quan"):
            for seed in range(1, seeds + 1):
                inp_path = os.path.join(tmp, f"in_{mode}_{seed}.json")
                out_path = os.path.join(tmp, f"out_{mode}_{seed}.jsonl")
                sc_path = os.path.join(tmp, f"sc_{mode}_{seed}.json")
                with open(inp_path, "w", encoding="utf-8") as f:
                    json.dump(_generate_fuzz_frames(seed, ticks, mode), f)

                args = [*cmd, "--mode", mode, "--seed", str(seed), "--ticks", str(ticks),
                        "--inputs", inp_path, "--snapshot-every", "10", "--out", out_path]
                if mode == "quan":
                    with open(sc_path, "w", encoding="utf-8") as f:
                        json.dump({"quan": {"stock": {"ca_loc": 5, "bong_sung": 6, "ca_linh": 9, "bong_dien_dien": 4}}}, f)
                    args.extend(["--scenario", sc_path])

                t0 = time.perf_counter()
                p = subprocess.run(args, cwd=ROOT, capture_output=True, text=True)
                dt_ms = (time.perf_counter() - t0) * 1000.0
                if p.returncode != 0:
                    results.append((mode, seed, False, dt_ms, [f"exit_code={p.returncode}: {p.stderr.strip()}"]))
                    continue
                viols = _check_invariants(out_path, mode, tuning)
                ok = len(viols) == 0
                if ok:
                    passed += 1
                results.append((mode, seed, ok, dt_ms, viols))
    return {"passed": passed, "total": total, "details": results}


def run_determinism_check(ticks: int) -> dict:
    cmd = _headless_cmd()
    checks = []
    with tempfile.TemporaryDirectory() as tmp:
        for mode in ("gather", "quan"):
            inp_path = os.path.join(tmp, f"det_{mode}.json")
            with open(inp_path, "w", encoding="utf-8") as f:
                json.dump(_generate_fuzz_frames(42, ticks, mode), f)
            out1 = os.path.join(tmp, f"det_{mode}_1.jsonl")
            out2 = os.path.join(tmp, f"det_{mode}_2.jsonl")
            sc_args = []
            if mode == "quan":
                sc_path = os.path.join(tmp, "det_quan_sc.json")
                with open(sc_path, "w", encoding="utf-8") as f:
                    json.dump({"quan": {"stock": {"ca_loc": 4, "bong_sung": 4, "ca_linh": 6, "bong_dien_dien": 2}}}, f)
                sc_args = ["--scenario", sc_path]

            p1 = subprocess.run([*cmd, "--mode", mode, "--seed", "42", "--ticks", str(ticks),
                                 "--inputs", inp_path, *sc_args, "--out", out1], cwd=ROOT, capture_output=True, text=True)
            p2 = subprocess.run([*cmd, "--mode", mode, "--seed", "42", "--ticks", str(ticks),
                                 "--inputs", inp_path, *sc_args, "--out", out2], cwd=ROOT, capture_output=True, text=True)
            if p1.returncode != 0 or p2.returncode != 0:
                checks.append((mode, False, "", "", f"exit_codes=({p1.returncode}, {p2.returncode})"))
                continue
            h1, h2 = _sha256(out1), _sha256(out2)
            checks.append((mode, h1 == h2, h1[:16], h2[:16], "OK" if h1 == h2 else "SHA-256 MISMATCH"))
    return {"passed": sum(1 for c in checks if c[1]), "total": len(checks), "checks": checks}


def run_perf_soak(tuning: dict) -> dict:
    """Chạy full 1 ca (180s = 10,800 ticks) trực tiếp trong memory để đo tốc độ & Peak RAM."""
    metrics = []
    for mode in ("gather", "quan"):
        full_ticks = int(round(tuning[mode]["duration_s"] * 60))
        frames = _generate_fuzz_frames(99, full_ticks, mode)["frames"]
        scenario = {"stock": {"ca_loc": 10, "bong_sung": 10, "ca_linh": 15, "bong_dien_dien": 5}} if mode == "quan" else {}
        player = InputPlayer(frames)

        tracemalloc.start()
        t0 = time.perf_counter()
        sess = Session(mode, tuning, scenario, seed=99)
        ran_ticks = 0
        while sess.tick < full_ticks and not sess.done:
            sess.step(player.advance(sess.tick))
            ran_ticks += 1
        elapsed_s = max(1e-6, time.perf_counter() - t0)
        _, peak_bytes = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        tps = ran_ticks / elapsed_s
        metrics.append({
            "mode": mode,
            "ticks": ran_ticks,
            "elapsed_ms": elapsed_s * 1000.0,
            "ticks_per_sec": tps,
            "peak_kb": peak_bytes / 1024.0,
            "reason": sess.sim.reason or "tick_limit",
        })
    return {"metrics": metrics}


def run_live_http_stress(tuning: dict, requests_count: int = 80) -> dict:
    """Kiểm tra chịu tải HTTP server `chonoi.live` khi client (Godot/Web) poll liên tục."""
    server = LiveServer(LiveGame("gather", tuning, {}, seed=1), port=0)
    server.start()
    ok_get, ok_post = 0, 0
    err_msg = ""
    t0 = time.perf_counter()
    try:
        base = f"http://127.0.0.1:{server.port}"
        for i in range(requests_count):
            with urllib.request.urlopen(base + "/state", timeout=3) as r:
                if r.status == 200:
                    ok_get += 1
            if i % 4 == 0:
                payload = json.dumps({"move": [1 if (i // 4) % 2 == 0 else -1, 0], "interact": False, "catch": False}).encode()
                req = urllib.request.Request(base + "/input", data=payload, method="POST",
                                             headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=3) as r:
                    if r.status == 200:
                        ok_post += 1
    except Exception as e:
        err_msg = str(e)
    finally:
        server.stop()
    dt_ms = (time.perf_counter() - t0) * 1000.0
    clean_stop = (not server.game._thread.is_alive()) and (not server._thread.is_alive())
    expected_post = (requests_count + 3) // 4
    passed = (ok_get == requests_count and ok_post == expected_post and clean_stop and not err_msg)
    return {
        "passed": passed,
        "ok_get": ok_get,
        "total_get": requests_count,
        "ok_post": ok_post,
        "total_post": expected_post,
        "clean_stop": clean_stop,
        "elapsed_ms": dt_ms,
        "error": err_msg,
    }


def format_markdown(fuzz, det, perf, live, seeds, ticks) -> str:
    lines = [
        "# Báo Cáo Kiểm Thử Ổn Định & Hiệu Năng (QA Stability Suite)",
        "",
        f"- **Thời điểm chạy:** {time.strftime('%Y-%m-%d %H:%M:%S')}",
        f"- **Môi trường:** {platform.system()} {platform.release()} · Python {platform.python_version()}",
        f"- **Cấu hình Fuzz:** {seeds} seeds x 2 modes (`gather`, `quan`) x {ticks} ticks/run",
        "",
        "## 1. Fuzz / Monkey Testing & Invariant Checking",
        f"**Kết quả:** `{fuzz['passed']}/{fuzz['total']}` kịch bản đạt (không crash, 0 vi phạm bất biến).",
        "",
        "| Mode | Seed | Trạng thái | Thời gian (ms) | Ghi chú / Vi phạm |",
        "|---|---:|---|---:|---|",
    ]
    for mode, seed, ok, dt_ms, viols in fuzz["details"]:
        note = "OK (0 vi phạm)" if ok else "; ".join(viols[:3])
        lines.append(f"| `{mode}` | {seed} | {'PASS' if ok else 'FAIL'} | {dt_ms:.1f} | {note} |")

    lines.extend([
        "",
        "## 2. Determinism (So khớp SHA-256 Từng Byte)",
        f"**Kết quả:** `{det['passed']}/{det['total']}` đạt.",
        "",
        "| Mode | Trạng thái | Run 1 (SHA-256) | Run 2 (SHA-256) | Kết luận |",
        "|---|---|---|---|---|",
    ])
    for mode, ok, h1, h2, note in det["checks"]:
        lines.append(f"| `{mode}` | {'PASS' if ok else 'FAIL'} | `{h1}` | `{h2}` | {note} |")

    lines.extend([
        "",
        "## 3. Performance & Memory Soak (Full Ca 180s = 10,800 ticks)",
        "",
        "| Mode | Ticks đã chạy | Thời gian (ms) | Tốc độ (ticks/s) | Peak RAM (KB) | Lý do dừng |",
        "|---|---:|---:|---:|---:|---|",
    ])
    for m in perf["metrics"]:
        lines.append(
            f"| `{m['mode']}` | {m['ticks']} | {m['elapsed_ms']:.1f} | {m['ticks_per_sec']:.0f} | {m['peak_kb']:.1f} | `{m['reason']}` |"
        )

    lines.extend([
        "",
        "## 4. Live HTTP Server Bridge Stress (`chonoi.live`)",
        f"- **Trạng thái:** `{'PASS' if live['passed'] else 'FAIL'}`",
        f"- **GET /state:** `{live['ok_get']}/{live['total_get']}` (200 OK)",
        f"- **POST /input:** `{live['ok_post']}/{live['total_post']}` (200 OK)",
        f"- **Tắt sạch thread (`server.stop()`):** `{live['clean_stop']}` (tổng thời gian `{live['elapsed_ms']:.1f} ms`)",
    ])
    if live["error"]:
        lines.append(f"- **Lỗi:** `{live['error']}`")
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="QA Stability, Fuzz, Invariant & Performance Suite")
    p.add_argument("--seeds", type=int, default=4, help="Số seed fuzz mỗi mode (mặc định: 4)")
    p.add_argument("--ticks", type=int, default=1200, help="Số ticks mỗi kịch bản fuzz (mặc định: 1200 = 20s)")
    p.add_argument("--out", help="Đường dẫn lưu báo cáo Markdown (tùy chọn)")
    a = p.parse_args(argv)

    tuning = load_contract()["tuning"]
    fuzz = run_fuzz_and_invariants(a.seeds, a.ticks, tuning)
    det = run_determinism_check(a.ticks)
    perf = run_perf_soak(tuning)
    live = run_live_http_stress(tuning)

    report = format_markdown(fuzz, det, perf, live, a.seeds, a.ticks)
    print(report)
    if a.out:
        os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
        with open(a.out, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"Đã lưu báo cáo tại: {a.out}")

    all_ok = (fuzz["passed"] == fuzz["total"] and det["passed"] == det["total"] and live["passed"])
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
