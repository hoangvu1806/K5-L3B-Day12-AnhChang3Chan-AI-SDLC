# Quán Ăn Chợ Nổi v1.0.0 — Phát hành chính thức (Nhóm AnhChang3Chan)

> **Test Contract:** `v1.3` (tương thích hoàn toàn gameplay/JSONL `v1.2`) · **Tags trên `main`:** `phase-3`, `phase-4`, `v1.0.0`

## Điểm nổi bật
- **Vòng ngày hoàn chỉnh (`--mode day --days 5`):** Lặn & Hái → Mở Quán → Shop nâng cấp theo kế hoạch 5 Ngày của Má Tư (D1–D5).
- **Buổi sáng (`gather`):** Bơi 2D, oxy, ngạt, Máu, 6 nút hái, 8–12 đàn cá bơi/sinh tất định theo seed, thủy quái Cá Sấu Năm Chèo (`M1`, `M2`) & mở rộng **Rắn Hổ Mây** (`snake`, `M3`), giỏ LIFO.
- **Buổi tối (`quan`):** 2 bếp (`B1`, `B2`), 4 bàn (`T1`–`T4`), 6 món ăn đặc trưng Tây Nam Bộ, khách theo lịch, giữ chỗ theo ID cá thể, tiền boa, uy tín, đóng ca và mở rộng **cháy món** (`burn`, `burn_s: 20`).
- **Mùa Nước Nổi (`v1.2` / `v1.3`):** Kho cá thể `{id, kind, fresh}`, hao tươi chính xác bằng số nguyên (`-0.5/s` khi lặn, `-0.25/s` tại quán), sự kiện `spoiled` tại ngưỡng `< 30`, chốt `base_price` theo trung bình độ tươi lúc bắt đầu nấu.
- **Trải nghiệm Godot 3D & HUD (`godot/`):** Cảnh lặn 2.5D + quán bè Tây Nam Bộ 3D kết nối `chonoi.live`, cảnh báo HUD cấu hình từ dữ liệu (`tuning.hud_alerts` → `meta.alerts`) cho thủy quái gần / oxy thấp / khách sắp giận, chế độ **Tương phản cao** (phím `H`).
- **Đo kiểm & Chất lượng phát hành:**
  - **Regression Suite:** `148/148` tests PASS (`0` fail, `0` error, `0` skip) — xem `docs/proof/phase-4/unittest_run.log`.
  - **Soak 10 Ngày (`python3 -m chonoi.soak --seed 7 --days 10`):** `10/10` ngày hoàn tất, `0` crash, tất định 100% — xem `docs/proof/phase-4/soak-v13.json`.
  - **GPU Benchmark 30s (`bash tools/bench.sh --seed 42 --duration 30`, 1280×720):** `122.15 avg FPS` / `71.63 p1_low` (`load_ms: 497 ms`, `bench-godot-4.7.2.json`) và xác minh bổ sung trên RTX 3050 VSync `60.0 avg FPS` / `60.0 p1_low` (`bench.json`).
  - **QA Stability Suite (`tools/qa_stability_suite.py`):** `8/8` Fuzz & Invariant PASS, `2/2` SHA-256 Determinism từng byte PASS, `100/100` Live HTTP `200 OK`.

## Cách chạy nhanh (≤ 3 lệnh từ clone sạch)
Xem chi tiết tại `README.md`:
```bash
PYTHONPATH=tests:. python3 -m unittest discover -s tests -v
python3 -m chonoi.live --mode day --days 5
godot --path godot
```
- **Headless:** `python3 -m chonoi.headless --mode day --seed 1 --days 5 --ticks 111000 --out out.jsonl`
- **Soak 10 Ngày:** `python3 -m chonoi.soak --seed 7 --days 10 --out soak.json`
- **Benchmark 30s:** `bash tools/bench.sh --seed 42 --duration 30 --out bench.json`

## Ghi nhận trung thực & Giới hạn đã biết
- Client Godot 3D cần server Python (`chonoi.live`) chạy song song.
- Benchmark GPU được thực hiện trên Godot `4.7.2` (phiên bản cài đặt trên máy kiểm thử) thay vì `4.5.1`; thông số trung thực nằm trong `docs/verification/phase-4.md`.
- Một số model 3D thay thế gần đúng và giấy phép bên thứ ba được kê khai rõ trong `CREDITS.md` và `LICENSE` (mục `docs/clarify.md #26` ghi nhận cần rà lại phân phối lại thư mục `river_delta`).
- Phản tư cá nhân hiện có 4/6 thành viên trong `docs/members/` (`double-n-021`, `hnha02`, `hoangvu1806`, `Jay-Gabriel`); `AnK17-UIT` và `thbao4545` bổ sung sau.
