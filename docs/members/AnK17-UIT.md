# Nguyễn An (`AnK17-UIT`) — phản tư cá nhân

- **Tôi đã làm (kèm commit):**
  - Khởi tạo cấu hình `godot/project.godot` (`963683f`) và triển khai Lát 1 `chonoi/sim/gather.py` (oxy, ngạt, Máu, ngất) + `tests/test_gather_oxygen.py` (`86e31b7`, `40f889b`).
  - Phase 2–3: cập nhật số liệu gather v1.1, triển khai hao độ tươi giỏ `-0.5/s`, cấp ID `I1..`, sự kiện `spoiled` ngưỡng 30 và mở rộng dòng nước lũ `current` kèm `tests/test_gather_freshness.py`, `tests/test_gather_current.py` (`0097871`).
  - Phase 4: chỉnh hoa súng theo logic, nhãn cá, cỡ chữ HUD Godot và cập nhật `README.md` (`63950c5`).
- **Đã giúp / review:** Phối hợp Vũ, Bảo chốt biên độ tươi/cá thể và hỗ trợ giải xung đột khi gộp nhánh Phase 2–4 vào `dev`.
- **AI sai ở đâu & cách phát hiện:** AI chưa rõ tick oxy về 0 có tính vào chu kỳ ngạt 60 tick không (`docs/clarify.md` #12) và đặt hao tươi sau bước quái làm sai `fresh` trong `lost`; phát hiện nhờ đối chiếu TICKET-03 và test biên (`clarify.md` #19, #21).
- **Bài học:** Luôn chốt thứ tự xử lý trong tick và viết test biên trước khi tích hợp liên lát.
