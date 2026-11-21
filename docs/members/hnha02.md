# hnha02 (Trần Thị Hà Anh) — phản tư cá nhân (≤ 200 từ)

- **Vai trò:** `sim/quan` Lát 4 (bếp, bưng, phục vụ, tiền); dự phòng Lát 3.
- **Tôi đã làm:**
  - P1: Lát 4 + 11 test, bằng chứng `docs/proof/phase-1/lat4/` — `035b837`, PR #9.
  - P2: B2/T2–T4, đơn theo `order_tick`, đóng ca, mở rộng `burn` + 11 test — `fe80837`, PR #13.
  - P3: hao tươi kho quán 0.25/s, `spoiled` ở kho, chốt `base_price`, boa theo giá chốt + 11 test — `22a117b`, PR #23.
  - P4: ngưỡng cảnh báo thành dữ liệu (`meta.alerts`), CHANGELOG P4, rà CREDITS, LICENSE — `025267a`, PR #24.
- **Đã giúp ai:** khớp `order_id`/giữ chỗ với Lát 3 (Vũ); đưa ngưỡng cho HUD (Gia Bảo); phát hiện `river_delta` commit trái giấy phép (clarify #26).
- **AI sai ở đâu và tôi phát hiện thế nào:**
  - Đoán trường event, công thức boa khi chưa có ticket → ghi clarify, sửa khi có Ticket-02.
  - Đẩy thẳng `main` → revert `630d518`, chuyển sang nhánh + PR.
  - Kỳ vọng giá 45 ở ca biên; tính lại có hao 1 tick → 44, thêm test.
  - Khai biến sai phạm vi GDScript; `godot --check-only` bắt được.
- **Bài học:** đọc ticket trước khi code, test hộp đen ở ngưỡng, và mọi thay đổi đi qua PR.
