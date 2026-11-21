# Kế hoạch Phase 4 — TICKET-04 "Phát hành v1.0.0" (Test Contract v1.3)

> 30 phút (2:30–3:00). Tag `phase-4` **và** GitHub Release `v1.0.0` cùng trỏ một commit trên `main`, chậm nhất 3:00.
> Điều kiện trước: Phase 3 (v1.2, kho cá thể + độ tươi) đã vào `main`. Gameplay/JSONL của v1.3 giữ nguyên v1.2.

## Việc / người
| # | Việc | Người | File chính | Phụ thuộc |
|---|---|---|---|---|
| 1 | Contract v1.3: `contract_version:"1.3"`, khai `bench_cmd`, `soak_cmd` ở gốc manifest | **Hoàng Vũ** | `game.contract.json` | #2, #3 có lệnh |
| 2 | `soak_cmd --seed --days N --out soak.json`: bot tất định chạy N Ngày (D1–D5 lặp ở 6–10), xuất `days,days_completed,crashes,results[{day,earned,reputation,score}],duration_s` | **Hoàng Vũ** | `chonoi/soak.py` (dùng `DaySim`) | Phase 3 trên `dev` |
| 3 | `bench_cmd --seed 42 --duration 30 --out bench.json`: cảnh lặn 1280×720, Út Sen đứng ở bến, làm nóng 3 s, đo 30 s; xuất `avg_fps,p1_low_fps,frames,measured_s,load_ms` | Trần Gia Bảo (`Jay-Gabriel`) | `godot/scripts/bench.gd`, `tools/bench.sh` | cảnh `DiveUnderwater` |
| 4 | Cảnh báo bằng chữ/biểu tượng: **thủy quái gần**, **oxy sắp hết**, **khách sắp giận**; chế độ **tương phản cao** (phím/tuỳ chọn) | Trần Gia Bảo + Hà Anh (`hnha02`) — Hà Anh lấy ngưỡng từ snapshot, Gia Bảo vẽ HUD | `godot/scripts/game.gd` | — |
| 5 | Đóng gói: clone sạch chạy giao diện **≤ 3 lệnh** trên macOS/Linux; README ghi môi trường, điều khiển, lệnh test/headless/bench; bản export Godot đính kèm Release | Nguyễn An (`AnK17-UIT`) | `README.md`, `godot/export_presets.cfg` | #3, #4 |
| 6 | Bench/QA: chạy bench + regression P1–P3, lưu `docs/proof/phase-4/` (bench.json, soak.json, log test), ma trận `AC-P4-xx` | Nhật Nguyên (`double-n-021`) | `docs/verification/phase-4.md`, `docs/proof/phase-4/` | #2, #3 |
| 7 | `CHANGELOG.md` theo từng phase, rà `CREDITS.md` + thêm `LICENSE` | Hà Anh (`hnha02`) | `CHANGELOG.md`, `CREDITS.md`, `LICENSE` | — |
| 8 | Mở rộng `leaderboard` (tuỳ chọn, làm sau lõi): top 10 lưu bền, `--leaderboard --player-name` ở day, `--export-leaderboard` | Từ Huy Bảo (`thbao4545`) | `chonoi/leaderboard.py`, `chonoi/headless.py` | #2 |
| 9 | Release: kiểm commit bàn giao, release notes, merge `dev` → `main`, gắn tag `phase-4`, công bố Release `v1.0.0` kèm bản đóng gói | **Hoàng Vũ** | GitHub Release | tất cả |
| 10 | Điều phối retro: mở đầu bằng rà hành động P2, ghi tốt/cần sửa/hành động, một lỗi AI và cách xác minh | Nhật Nguyên | `docs/retro.md` | — |

**Mọi người:** `docs/members/<handle>.md` ≤ 200 từ (phần mình làm, đã giúp ai, AI sai ở đâu, bài học, link commit); thêm dòng vào `docs/ai-usage-log.md`.

## Mốc nội bộ
- 0–15: #2, #3, #4, #5, #7 song song; #6 chạy regression ngay khi có lệnh.
- 15–25: retro (#10) + phản tư cá nhân; phút 20 standup, người xong sang hỗ trợ #3/#5.
- 25–30: Vũ merge `dev` → `main`, kiểm artifact khớp commit, tag `phase-4` + Release `v1.0.0`.

## Demo (sau 3:00, ≤ 5 phút)
Chơi một Ngày gather → quan → đóng Shop · chạy test đạt · chỉ bằng chứng chia việc từng người · mở ma trận truy vết.

## Rủi ro
- Phase 3 chưa xong thì soak/bench chạy trên v1.1 → hoàn tất P3 trước phút 0 của P4, nếu trễ ghi trung thực trong verification.
- Bench cần render thật (không headless) → chạy trên máy có GPU, lưu artifact từ đúng commit nộp.
- Godot client cần server Python: lệnh chạy ≤ 3 lệnh nên gói vào một script khởi động.
