# Retro nhóm

## Phase 2 (nhanh)
- **Điều tốt:**
  - Kiến trúc tách hàm helper (`chonoi/sim/monsters.py`, `chonoi/sim/day.py`, `_tick_stoves`, `_burn`, `_step_fish`) giúp tích hợp 6 thành viên lên **88/88 bài test PASS** rất nhanh.
  - Công cụ `tools/qa_stability_suite.py` kiểm chứng tự động Fuzz, Invariant, Determinism SHA-256 và tốc độ chạy (< 0.4s / 10,800 ticks, vượt xa yêu cầu <= 20s).
- **Điều tệ:**
  - Một số fixture test cũ của Phase 1 giả định `fish_initial = 6` hoặc `stock` rỗng nhưng khách vẫn có `reserved`, gây lỗi khi gộp các nhánh nếu không kiểm tra kỹ.
- **1 hành động cho Phase 3 (Người nhận: Hoàng Vũ `hoangvu1806` & Nhật Nguyên `double-n-021`):**
  - Khi chuyển sang **Test Contract v1.2 (Độ tươi & Kho cá thể `[{"id": "I1", "kind": ..., "fresh": ...}]`)**, thống nhất dùng đơn vị nguyên `240 đơn vị = 1 điểm tươi` (gather `-2/tick`, quán `-1/tick`) và viết adapter chuẩn trong `chonoi/inventory.py` trước khi sửa `gather.py` và `quan.py`.

## Phase 4 (cuối)
- Rà lại hành động Phase 2: đã làm chưa? vì sao?
- Điều tốt / điều tệ:
- Số liệu: số commit theo người, cách đọc code của nhau, token theo người:
- Một lần AI sai và cách nhóm phát hiện:
- Nếu làm lại, đổi gì:
