# hnha02 (Trần Thị Hà Anh) — phản tư cá nhân (≤ 200 từ)

- **Vai trò:** Member, phụ trách `sim/quan` Lát 4 (bếp, bưng, phục vụ, tiền); dự phòng cho Lát 3.
- **Tôi đã làm:**
  - Luật Lát 4 trong `chonoi/sim/quan.py`: `cook_started`, `dish_ready`, `dish_picked`, `served`, `paid`, boa, uy tín; kiểm scenario mâu thuẫn (mã 2) trong `chonoi/scenario.py`; 11 test hộp đen `tests/test_quan_lat4.py` — [035b837](https://github.com/hoangvu1806/K5-L3B-Day12-AnhChang3Chan-AI-SDLC/commit/035b83711f298199b7c8742ee5c00d8ef7a4e542).
  - Ghi 7 giả định Lát 4 vào `docs/clarify.md` (#5–11).
- **Tôi đã review:** đối chiếu Lát 4 với hợp đồng tích hợp `docs/contracts/README.md` mục 4.2 khi gộp với [433016a](https://github.com/hoangvu1806/K5-L3B-Day12-AnhChang3Chan-AI-SDLC/commit/433016a0de9ae18ad4cae8e7b1ae9a1663442fe3); chạy lại bộ test của QA (62/62 xanh trên dev).
- **AI sai ở đâu và tôi phát hiện thế nào:**
  - AI không đọc được PRD-0 trên lab board nên tự đặt trường `data` sự kiện, công thức boa → buộc ghi thành giả định chờ PO xác nhận.
  - AI đặt bước giảm kiên nhẫn (Lát 3) trước bếp; phát hiện khi so với hợp đồng mục 4.2 và đã sửa.
  - Trên Windows, test fail vì thiếu lệnh `python3` và web sập vì lỗi mã hóa tiếng Việt (cần `PYTHONUTF8=1`).
- **Điều tôi học được:** Viết test hộp đen và ghi giả định ngay từ đầu giúp sửa nhanh khi PRD được xác nhận; chốt hợp đồng dữ liệu khách với lát bên cạnh trước khi code.
