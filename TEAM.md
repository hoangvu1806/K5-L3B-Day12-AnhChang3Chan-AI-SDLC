# TEAM

**Tên nhóm:** AnhChang3Chan  **Số người:** 6  (khớp `team_size` trong `game.contract.json`)

| Thành viên | GitHub handle | Module chính | Vai quy trình | Người dự phòng cho |
|---|---|---|---|---|
| Nguyễn An | `AnK17-UIT` | `sim/gather` (Lát 1 — chỉ logic: bơi, oxy, chặn biên, giỏ) | Member | Từ Huy Bảo (`sim/gather` Lát 2) |
| Từ Huy Bảo | `thbao4545` | `sim/gather` (Lát 2 — chỉ logic: hái, bắt cá, cập bến, ghi file kho) | Member | Nguyễn An (`sim/gather` Lát 1) |
| Hoàng Vũ | `hoangvu1806` | `sim/quan` (Lát 3 — chỉ logic: khách, giữ chỗ nguyên liệu, kiên nhẫn) | Integrator / Scrum | Hà Anh (`sim/quan` Lát 4) |
| Hà Anh | `hnha02` | `sim/quan` (Lát 4 — chỉ logic: bếp, bưng, phục vụ, tiền) | Member | Hoàng Vũ (`sim/quan` Lát 3) |
| Trần Gia Bảo | `Jay-Gabriel` | `client/godot` (Asset, đồ họa 2D/3D trên Godot) | Member | Hoàng Vũ (UI/tích hợp) |
| Nhật Nguyên | `double-n-021` | `qa` (Tester — test case, headless contract, verification & proof) | QA lead / PO | Tất cả các lát khi cần rà lỗi |

## Phân công theo phase (chi tiết trong `docs/plan/phase-n.md`)

| Thành viên | Phase 2 (v1.1) | Phase 3 (v1.2) |
|---|---|---|
| Nguyễn An (`AnK17-UIT`) | Số chuẩn gather, cá bơi/sinh, N5/N6 | Hao tươi giỏ, `spoiled`, cấp id cá thể · mở rộng `current` |
| Từ Huy Bảo (`thbao4545`) | Cá Sấu, Máu/ngất do quái · mở rộng `snake` | LIFO cá thể khi mất hàng, ghi kho cá thể khi `gather_end` |
| Hoàng Vũ (`hoangvu1806`) | `--mode day`, Shop, pause; khách quán theo lịch mới; gắn tag | Adapter kho cá thể, giữ chỗ theo id, bàn giao trong `day`; gắn tag · mở rộng `reservations` (cùng Hà Anh) |
| Hà Anh (`hnha02`) | 2 bếp/4 bàn, 6 món, đóng ca · mở rộng `burn` | Hao tươi kho quán, giá theo tươi, boa · mở rộng `reservations` |
| Trần Gia Bảo (`Jay-Gabriel`) | Menu, màn chuyển pha, pause, HUD sáng/quán | HUD độ tươi / hàng ươn |
| Nhật Nguyên (`double-n-021`) | Manifest v1.1, test, smoke, verification P2 | Test ngưỡng/bàn giao, regression, `CHANGELOG.md`, verification P3 |

**Vai quy trình:** PO (đầu mối hỏi giảng viên, giữ `docs/clarify.md`) · Integrator (giữ `docs/contracts/`, gắn tag) · QA lead · Scrum/Release.

## Thỏa thuận làm việc nhóm

- Kênh liên lạc: Nhóm chat chung của nhóm & GitHub Issues/PR.
- Nguyên tắc tách biệt Logic & Đồ họa: 4 thành viên làm Lát 1–4 **chỉ làm logic**, thống nhất chuẩn chung (từ `game.contract.json` và `docs/contracts/`) và khớp yêu cầu bài, có thể sáng tạo mở rộng (tắt ở chế độ headless).
- Đồ họa & Asset: Trần Gia Bảo thực hiện asset, đồ họa qua **Godot** (đọc trạng thái/chỉ dùng chuẩn tích hợp chung, không nhân đôi luật sim).
- Kiểm thử: Nhật Nguyên phụ trách viết/chạy test, đối chiếu Test Contract và tổng hợp bằng chứng.
- Khi bất đồng về thiết kế: Thảo luận nhanh 2 phút; nếu chưa xong thì Integrator chốt để giữ tiến độ và ghi lại lý do.
- Khi ai đó trễ hoặc vướng quá 10 phút: Báo ngay trên nhóm chat để người dự phòng hoặc QA hỗ trợ (kiểm tra lại tại phút 20 mỗi phase).
- Cách làm việc với Git: Mỗi thành viên tự commit bằng GitHub handle của mình (tối thiểu 3 commit có nội dung); chạy test pass trước khi push/gộp vào `main`; Integrator chịu trách nhiệm gắn tag `phase-1` … `phase-4`.
