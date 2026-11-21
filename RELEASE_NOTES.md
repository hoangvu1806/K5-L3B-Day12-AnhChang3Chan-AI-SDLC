# Quán Ăn Chợ Nổi v1.0.0 (bản nháp — Integrator cập nhật trước khi công bố)

## Điểm mới
- Vòng ngày đầy đủ: Lặn & Hái → Mở Quán → Shop nâng cấp, 5 Ngày theo kế hoạch của Má Tư (D1–D5).
- Buổi sáng: oxy, ngạt, Máu, cá bơi/sinh theo seed, Cá Sấu Năm Chèo (+ Rắn Hổ Mây), giỏ LIFO.
- Buổi tối: 2 bếp, 4 bàn, 6 món, khách theo lịch, giữ chỗ nguyên liệu, boa, uy tín, đóng ca.
- Mùa Nước Nổi: kho cá thể `{id, kind, fresh}`, độ tươi, hàng ươn, giá theo độ tươi.
- Client Godot 3D (cảnh lặn 2.5D + quán bè góc nhìn thứ 3) nối logic qua `chonoi.live`.
- Mở rộng: `burn` (cháy món), `snake` (Rắn Hổ Mây).

## Cách chạy
Xem `README.md` (≤ 3 lệnh từ clone sạch). Headless: `python3 -m chonoi.headless --mode day --seed 1 --days 5 --ticks 111000 --out out.jsonl`.
Soak: `python3 -m chonoi.soak --seed 7 --days 10 --out soak.json`.

## Giới hạn đã biết
- Client Godot cần server Python (`chonoi.live`) chạy song song.
- Model cá linh / bông điên điển là bản thay thế gần đúng (xem `CREDITS.md`).
