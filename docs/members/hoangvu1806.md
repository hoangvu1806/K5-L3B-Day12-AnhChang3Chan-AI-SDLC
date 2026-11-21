# hoangvu1806 (Hoàng Vũ) — phản tư cá nhân (≤ 200 từ)

- **Vai trò:** Integrator / Scrum; phụ trách `sim/quan` Lát 3; dự phòng cho Lát 4.
- **Tôi đã làm:**
  - Lập `TEAM.md` 6 người, đồng bộ `team_size` — [6a5ac41](https://github.com/hoangvu1806/K5-L3B-Day12-AnhChang3Chan-AI-SDLC/commit/6a5ac41).
  - Lát 3 trong `chonoi/sim/quan.py`: khách theo lịch, giữ chỗ nguyên liệu, kiên nhẫn, `customer_left`, `no_dish`; kiểm scenario mã 2 trong `chonoi/scenario.py`; 7 test `tests/test_quan_customers.py` — [40c009e](https://github.com/hoangvu1806/K5-L3B-Day12-AnhChang3Chan-AI-SDLC/commit/40c009e).
  - Đưa bộ asset 3D Tây Nam Bộ vào `godot/`, viết `godot/tools/dequantize_glb.py` để Godot import được 185 model — [c351bc3](https://github.com/hoangvu1806/K5-L3B-Day12-AnhChang3Chan-AI-SDLC/commit/c351bc3).
- **Tôi đã review:** PR #2 (Lát 3 → dev); đối chiếu hàm `available()`/`release()` với Lát 4 của `hnha02` (clarify #7, #11).
- **AI sai ở đâu và tôi phát hiện thế nào:**
  - AI không đọc được PRD-0 nên tự đặt tên sự kiện `customer_arrived` và trường `data` → ghi thành giả định, chờ đối chiếu.
  - AI tự sửa `docs/` khi chưa được yêu cầu → tôi yêu cầu hoàn tác.
  - Script của asset kit có cú pháp Python trong GDScript và model nén Godot không đọc được → phát hiện khi chạy `godot --headless`.
- **Điều tôi học được:** Chạy thử thật (headless, Godot) mới lộ lỗi; giả định phải ghi ra ngay để lát bên cạnh khớp theo.
