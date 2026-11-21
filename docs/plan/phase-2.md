# Kế hoạch Phase 2 — TICKET-02 "Một ngày ở chợ nổi" (Test Contract v1.1)

> 55 phút (1:00–1:55). Tag `phase-2` trên `main` trước 1:55. Nhóm 6 người → làm **≥ 2 mở rộng** sau khi lõi đúng.

## Mục tiêu
- `contract_version: "1.1"`, số chuẩn mục 1, đủ 6 nguyên liệu (`ca_keo`, `keo_neo` mới) và 6 món.
- Cá bơi/sinh, Cá Sấu + Máu/ngất, 2 bếp/4 bàn, `--mode day` (D1–D5, Shop, pause) chạy đúng.
- Regression P1 xanh với số chuẩn; test đổi vì luật mới phải ghi lý do.

## Việc / người / phụ thuộc
| # | Việc | Người | File chính | Phụ thuộc |
|---|---|---|---|---|
| 0 | `game.contract.json` v1.1: tuning chuẩn, `day_plan`, `shop`, `monsters`, khóa cá mới; `chonoi/contract.py` kiểm khóa mới | Nhật Nguyên (`double-n-021`) + Vũ duyệt | `game.contract.json`, `chonoi/contract.py` | — (làm **đầu tiên**, phút 0–10) |
| 1 | Số chuẩn gather + cá bơi/đổi hướng/phản xạ mép + sinh cá theo lịch (`fish_spawned`), nút N5/N6, `ca_keo` yield 2 | Nguyễn An (`AnK17-UIT`) | `chonoi/sim/gather.py` (`_step_fish`, `_spawn_fish`) | #0 |
| 2 | Cá Sấu M1/M2: patrol/chase/recoil, hit (`monster_hit`, LIFO floor(n/2)), bất tử 90, `faint cause:"monster"` | Từ Huy Bảo (`thbao4545`) | `chonoi/sim/gather.py` (`_step_monsters`), file mới `chonoi/sim/monsters.py` | #0 |
| 3 | Quán: B2, T2–T4, 6 món; khách theo lịch 120 + 900·k; bếp lấy đơn theo `order_tick` rồi id bàn; đóng ca (khách ăn trả ngay, khách chờ rời không trừ uy tín); lọc menu theo kế hoạch ngày | Hà Anh (`hnha02`) — bếp/đóng ca · Hoàng Vũ — khách/`order_tick`/lọc menu | `chonoi/sim/quan.py` | #0 |
| 4 | `--mode day`: DayIntro→gather→quan→Shop, bàn giao kho trong bộ nhớ, `day_start`/`day_plan`/`phase_start`, Shop (`bought`, `buy_failed`, `shop_end`), pause/`resumed`, `--days`, `days_completed` | **Hoàng Vũ** (`hoangvu1806`) | file mới `chonoi/sim/day.py`, `chonoi/headless.py`, `chonoi/runner.py`, `chonoi/inputs.py` | #1–#3 dùng fixture cố định để tích hợp sớm |
| 5 | Godot: menu chính, DayIntro/EveningIntro/DayResult/Summary, pause (Esc/P), HUD sáng + quán (chữ ≥ 18 px ở 1280×720, ≥ 30 FPS) | Trần Gia Bảo (`Jay-Gabriel`) | `godot/` | schema snapshot v1.1 từ #4 |
| 6 | QA: test v1.1, smoke `gather --inventory-out → quan --inventory` (phút 20), smoke `day --days 1` và nhiều Ngày, regression P1, `docs/verification/phase-2.md`, `docs/proof/phase-2/` | Nhật Nguyên (`double-n-021`) | `tests/`, `docs/` | tất cả |

## Mở rộng (chọn 2, sau khi lõi xanh)
| Mở rộng | Người | Lý do chọn |
|---|---|---|
| `burn` (Cháy món, `burn_s: 20`, `dish_burnt`) | Hà Anh | Nằm gọn trong bếp, đã có `ready_ticks` |
| `snake` (Rắn Hổ Mây M3) | Từ Huy Bảo | Dùng lại luật chạm/recoil của Cá Sấu, chỉ thêm dữ liệu loài |

Khai `extensions: ["burn", "snake"]` ở gốc manifest; ghi vào README mục mở rộng kèm test.

## Mốc nội bộ
- 0–5: đọc ticket, so số chuẩn với giả định P1 (cập nhật `docs/clarify.md`), chốt giao diện chuyển pha.
- 5–20: #0 xong trước phút 10; #1–#3 song song; #4 dựng khung day với fixture.
- 20: smoke tích hợp file kho, lưu `docs/proof/phase-2/integration.*`; standup 2–3 phút.
- 20–35: nối day với gather/quan thật, Shop, pause; Godot HUD.
- 35–45: smoke `day --days 1` và `--days 3` (kiểm cấp oxygen/hp áp từ Ngày kế), regression P1, verification.
- 45–50: retro nhanh vào `docs/retro.md`.
- 50–55: merge `dev` → `main`, Integrator (Vũ) gắn tag `phase-2`.

## Rủi ro
- `gather.py` có 2 người (An: cá, Bảo: quái) → tách hàm/file riêng, `step()` chỉ gọi một dòng mỗi phần.
- Thứ tự tick (mục 4.5) sai làm lệch JSONL từng byte → QA viết test thứ tự sự kiện cùng tick sớm.
- Ngày không pause ≤ 22.200 tick phải chạy ≤ 20 s → đo thời gian ở smoke.
