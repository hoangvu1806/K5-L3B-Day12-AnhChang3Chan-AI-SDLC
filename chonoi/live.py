"""Cầu nối mô phỏng cho client Godot 3D (`godot/`), chỉ dùng thư viện chuẩn Python.

    python3 -m chonoi.live [--mode day|gather|quan] [--days N] [--seed N] [--port 8000]

Máy chủ HTTP nhỏ (ThreadingHTTPServer), chỉ có API (giao diện 2D trên trình duyệt đã bỏ, nhóm dùng Godot 3D):
    GET  /state  -> snapshot JSON hiện tại (cùng trường như dòng snapshot của headless) + `meta` + `events`
    POST /input  -> {"move": [a, b], "interact": bool, "catch": bool, "pause": bool, "shop_done": bool,
                     "buy": "oxygen"}   (trạng thái phím đang giữ; buy là lệnh một lần)
    POST /restart -> chơi lại từ đầu (cùng seed, cùng scenario)

Mô phỏng chạy 60 tick/s trong một luồng nền, dùng CÙNG lớp sim như headless (qua `runner.Session`).
Client chỉ ĐỌC snapshot và tự bỏ qua trường chưa có, nên luật do nhóm viết thêm trường nào cũng không vỡ.
Ngẫu nhiên vẫn đi qua `Streams` (seed); chỉ nhịp chạy theo đồng hồ thật, không đi vào luật.
"""

import argparse
import json
import os
import sys
import threading
import time
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from .contract import load_contract
from .errors import BadInput
from .inputs import BUTTONS_V11, InputState, LiveInputs
from .inventory import read_inventory
from .leaderboard import default_store, export_entries, player_name, read_entries, record_completed
from .runner import Session
from .scenario import load_scenario

TICK_S = 1.0 / 60.0
MAX_BODY = 4096
RECENT_EVENTS = 40
INTRO_TICKS = 4 * 60


def hud_alerts(tuning) -> dict:
    """Ngưỡng cảnh báo HUD (Ticket-04) lấy từ dữ liệu: oxy/kiên nhẫn theo tỉ lệ, thủy quái gần theo
    detect_radius của từng loài. Chỉ đi qua `meta` của API live, KHÔNG ghi vào JSONL headless."""
    a = dict(tuning.get("hud_alerts", {}))
    a.setdefault("oxygen_low_ratio", 0.25)
    a.setdefault("patience_low_ratio", 0.25)
    a.setdefault("time_low_s", 30)
    species = tuning.get("gather", {}).get("monsters", {}).get("species", {})
    a["monster_near_m"] = {k: v["detect_radius"] for k, v in sorted(species.items()) if "detect_radius" in v}
    return a


class LiveGame:
    """Một lượt chơi + luồng nền bước 60 tick/s. Mọi truy cập trạng thái đi qua khóa."""

    def __init__(self, mode, tuning, scenario, seed, inventory=None, inventory_out=None, days=1,
                 *, presentation=False, leaderboard=None, name="Út Sen"):
        self._args = (mode, tuning, scenario, seed, inventory, days)
        self.mode = mode
        self.tuning = tuning
        self.inventory_out = inventory_out
        self.leaderboard = leaderboard
        self.name = name
        self.seed = seed
        self.presentation_enabled = presentation and mode == "day"
        self.run_id = 0
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread = None
        self._reset(menu=True)

    def _reset(self, *, menu=False):
        self.run_id += 1
        self.session = Session(*self._args)
        self.inputs = LiveInputs()
        self.events = self.session.initial_events()  # day: day_start, day_plan, phase_start ở tick 0
        self._saved = False
        self.error = None
        self.screen = None
        self._resume_requested = False
        self.dish_sales = {}
        self.shift_summary = {}
        self.waiting_reservations = set()
        if self.presentation_enabled:
            self._show_screen("menu" if menu else "day_intro")

    def _show_screen(self, name):
        self.screen = {"name": name, "ticks_left": None if name == "menu" else INTRO_TICKS}

    def _update_presentation(self, rows):
        for row in rows:
            name, data = row["name"], row["data"]
            if name == "phase_start":
                if row["phase"] == "gather":
                    self._show_screen("day_intro")
                elif row["phase"] == "quan":
                    self.shift_summary = dict(served=0, left=0, earned=0, tips=0,
                                              reputation_start=self.session.sim.reputation)
                    self.waiting_reservations.clear()
                    self._show_screen("evening_intro")
                else:
                    self._show_screen("day_result")
            elif name == "served":
                self.shift_summary["served"] += 1
            elif name == "customer_left":
                self.shift_summary["left"] += 1
            elif name == "reservation_arrived":
                self.waiting_reservations.add(data["reservation_id"])
            elif name == "reservation_served":
                self.waiting_reservations.discard(data["reservation_id"])
            elif name == "reservation_failed" and data["reservation_id"] in self.waiting_reservations:
                self.waiting_reservations.remove(data["reservation_id"])
                self.shift_summary["left"] += 1
            elif name == "paid":
                self.shift_summary["earned"] += data["price"] + data["tip"]
                self.shift_summary["tips"] += data["tip"]
                dish = data["dish_id"]
                self.dish_sales[dish] = self.dish_sales.get(dish, 0) + 1

    # --- luồng nền ----------------------------------------------------------------
    def start(self):
        self._thread = threading.Thread(target=self._loop, name="chonoi-sim", daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2)

    def _loop(self):
        nxt = time.perf_counter()
        while not self._stop.is_set():
            nxt += TICK_S
            with self._lock:
                try:
                    self._tick_once()
                except Exception:  # luật của nhóm lỗi: báo ra terminal + client, dừng bước (restart để chơi lại)
                    self.error = traceback.format_exc()
                    sys.stderr.write(self.error)
                    self.session.sim.done = True
                    self.session.sim.reason = "error"
            delay = nxt - time.perf_counter()
            if delay > 0:
                self._stop.wait(delay)
            elif delay < -0.25:  # chạy chậm quá thì bỏ bù, tránh chạy dồn
                nxt = time.perf_counter()

    def _tick_once(self):
        s = self.session
        if s.done:
            return
        inp = self.inputs.advance()
        if self.screen is not None:
            remaining = self.screen["ticks_left"]
            if remaining is not None:
                if remaining == 1:
                    self.screen = None
                else:
                    self.screen["ticks_left"] = remaining - 1
            return
        if self._resume_requested:
            self._resume_requested = False
            if s.paused:
                inp = InputState(inp.move, inp.held, {"pause"})
        rows = s.step(inp)
        self.events.extend(rows)
        if self.presentation_enabled:
            self._update_presentation(rows)
        del self.events[:-RECENT_EVENTS]
        if s.done and not self._saved:
            self._saved = True
            if self.inventory_out:
                try:
                    s.write_inventory_if_done(self.inventory_out)
                except OSError as e:
                    sys.stderr.write(f"lỗi ghi kho: {e}\n")
            if self.leaderboard:
                try:
                    record_completed(self.leaderboard, self.name, self.seed, s.sim, self.tuning)
                except (OSError, BadInput) as e:
                    sys.stderr.write(f"lỗi ghi bảng xếp hạng: {e}\n")

    # --- API cho handler -----------------------------------------------------------
    def state_json(self) -> bytes:
        with self._lock:
            snap = self.session.snapshot()
            phase = snap.get("phase", self.mode)
            snap["meta"] = dict(self.tuning.get(phase, {}), menu=self.tuning["menu"],
                                alerts=hud_alerts(self.tuning))
            snap["events"] = list(self.events)
            snap["finished"] = self.session.done
            snap["reason"] = self.session.sim.reason if self.session.done else None
            snap["error"] = self.error
            snap["run_id"] = self.run_id
            if self.presentation_enabled:
                snap["presentation"] = self.screen
                snap["shift_summary"] = self.shift_summary
                snap["dish_sales"] = self.dish_sales
            return json.dumps(snap, ensure_ascii=False, separators=(",", ":")).encode("utf-8")

    def set_input(self, body: dict):
        move = body.get("move")
        if move is not None:
            ok = (isinstance(move, list) and len(move) == 2 and
                  all(isinstance(c, (int, float)) and not isinstance(c, bool) and abs(c) <= 1 for c in move))
            if not ok:
                raise ValueError("move phải là [a, b] trong [-1, 1]")
        buttons = {}
        for b in BUTTONS_V11:
            if b in body:
                if not isinstance(body[b], bool):
                    raise ValueError(f"{b} phải là boolean")
                buttons[b] = body[b]
        buy = body.get("buy")
        if buy is not None and not (isinstance(buy, str) and buy):
            raise ValueError("buy phải là chuỗi khác rỗng")
        with self._lock:
            self.inputs.set(move, **buttons)
            if buy:
                self.inputs.set_buy(buy)

    def restart(self):
        with self._lock:
            self._reset()

    def go_to_menu(self):
        with self._lock:
            if self.presentation_enabled:
                self._reset(menu=True)

    def continue_playing(self):
        with self._lock:
            if self.screen is not None:
                if self.screen["name"] == "menu":
                    self._show_screen("day_intro")
                else:
                    self.screen = None
            elif self.session.paused:
                self._resume_requested = True


class _Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    game: LiveGame = None  # gán trên lớp con trong make_server

    def log_message(self, fmt, *args):  # yên lặng
        pass

    def _send(self, code, body: bytes, ctype="application/json; charset=utf-8"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path == "/state":
            self._send(200, self.game.state_json())
        else:
            self._send(404, b'{"error":"khong co"}')

    def do_POST(self):
        path = self.path.split("?", 1)[0]
        try:
            n = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            n = -1
        if n < 0 or n > MAX_BODY:
            self._send(400, b'{"error":"body sai"}')
            return
        raw = self.rfile.read(n) if n else b""
        try:
            if path == "/input":
                body = json.loads(raw.decode("utf-8") or "{}")
                if not isinstance(body, dict):
                    raise ValueError("body phải là object")
                self.game.set_input(body)
            elif path == "/restart":
                self.game.restart()
            elif path == "/menu":
                self.game.go_to_menu()
            elif path == "/continue":
                self.game.continue_playing()
            else:
                self._send(404, b'{"error":"khong co"}')
                return
        except (ValueError, UnicodeDecodeError) as e:
            self._send(400, json.dumps({"error": str(e)}).encode("utf-8"))
            return
        self._send(200, b'{"ok":true}')


class LiveServer:
    """Máy chủ + mô phỏng. port=0 -> cổng ngẫu nhiên (đọc `.port`)."""

    def __init__(self, game: LiveGame, host="127.0.0.1", port=8000):
        handler = type("Handler", (_Handler,), {"game": game})
        self.game = game
        # Windows: SO_REUSEADDR cho 2 server mở trùng cổng mà không báo lỗi -> tắt để lỗi 'cổng đã dùng' hiện ra
        server_cls = type("Server", (ThreadingHTTPServer,), {"allow_reuse_address": False})
        self.httpd = server_cls((host, port), handler)
        self.httpd.daemon_threads = True
        self.host = host
        self.port = self.httpd.server_address[1]
        self._thread = None

    @property
    def url(self):
        return f"http://{self.host}:{self.port}/"

    def start(self):
        self.game.start()
        self._thread = threading.Thread(target=self.httpd.serve_forever, name="chonoi-http", daemon=True)
        self._thread.start()

    def stop(self):
        self.httpd.shutdown()
        self.httpd.server_close()
        if self._thread:
            self._thread.join(timeout=2)
        self.game.stop()


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="chonoi.live", description="Server mô phỏng cho client Godot 3D.")
    p.add_argument("--mode", default="day", choices=["day", "gather", "quan"])
    p.add_argument("--days", type=int, default=5, help="chỉ với day: số Ngày (1..5)")
    p.add_argument("--seed", type=int, default=1)
    p.add_argument("--port", type=int, default=8000, help="0 = cổng ngẫu nhiên")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--scenario")
    p.add_argument("--presentation", action="store_true")
    p.add_argument("--leaderboard")
    p.add_argument("--player-name")
    p.add_argument("--export-leaderboard")
    p.add_argument("--inventory", help="chỉ với quan: nạp kho từ file")
    p.add_argument("--inventory-out", dest="inventory_out", help="chỉ với gather: ghi kho khi kết thúc buổi")
    a = p.parse_args(argv)
    try:
        if a.leaderboard == "" or a.export_leaderboard == "":
            raise BadInput("bảng xếp hạng cần đường dẫn")
        name = player_name(a.player_name) if a.player_name is not None else "Út Sen"
        store = a.leaderboard or default_store()
        if a.export_leaderboard is not None:
            export_entries(store, a.export_leaderboard)
            return 0
        if a.inventory and a.mode != "quan":
            raise BadInput("--inventory chỉ dùng với quan")
        if a.inventory_out and a.mode != "gather":
            raise BadInput("--inventory-out chỉ dùng với gather")
        contract = load_contract()
        tuning = contract["tuning"]
        scenario = load_scenario(a.scenario, a.mode, tuning)
        inventory = read_inventory(a.inventory, version=contract.get("contract_version", "1.0")) if a.inventory else None
        if inventory is not None and "stock" in scenario:
            raise BadInput("vừa có quan.stock vừa có --inventory")
        if not 1 <= a.days <= 5:
            raise BadInput("--days phải từ 1 đến 5")
        leaderboard = store if a.mode == "day" and a.days == 5 and a.scenario is None else None
        if leaderboard:
            read_entries(leaderboard)
        game = LiveGame(a.mode, tuning, scenario, a.seed, inventory, a.inventory_out,
                        days=a.days if a.mode == "day" else 1, presentation=a.presentation,
                        leaderboard=leaderboard, name=name)
        server = LiveServer(game, a.host, a.port)
    except BadInput as e:
        sys.stderr.write(f"đầu vào sai: {e}\n")
        return 2
    except OSError as e:
        sys.stderr.write(f"không khởi động được: {e}\n")
        return 1
    server.start()
    print(f"Server mô phỏng tại {server.url}  (chế độ {a.mode}, seed {a.seed}). Mở Godot (godot/) rồi nhấn F5. "
          "Ctrl+C để dừng.", flush=True)
    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        server.stop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
