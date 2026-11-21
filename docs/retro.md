# Retro nhóm

## Phase 2 (nhanh)
- **Điều tốt:**
  - Cả 6 thành viên đều chia việc rõ ràng theo lát và phối hợp nhịp nhàng: Nguyễn An (`AnK17-UIT` — gather chuẩn & cá bơi/sinh), Từ Huy Bảo (`thbao4545` — Cá Sấu, Rắn Hổ Mây & LIFO), Hoàng Vũ (`hoangvu1806` — `--mode day`, Shop, pause & live bridge), Hà Anh (`hnha02` — 2 bếp/4 bàn, 6 món, đóng ca & `burn`), Trần Gia Bảo (`Jay-Gabriel` — cảnh 3D Godot Mekong, nhân vật & assets Phase 2), Nhật Nguyên (`double-n-021` — QA Harness, test suite & verification).
  - Kiến trúc tách hàm helper (`chonoi/sim/monsters.py`, `chonoi/sim/day.py`, `_tick_stoves`, `_burn`, `_step_fish`) giúp tích hợp 6 thành viên lên **88/88 bài test PASS** ở tag `phase-2` rất nhanh.
  - Công cụ `tools/qa_stability_suite.py` kiểm chứng tự động Fuzz, Invariant, Determinism SHA-256 và tốc độ chạy (< 0.4s / 10,800 ticks, vượt xa yêu cầu <= 20s).
- **Điều tệ:**
  - Một số fixture test cũ của Phase 1 giả định `fish_initial = 6` hoặc `stock` rỗng nhưng khách vẫn có `reserved`, gây lỗi khi gộp các nhánh nếu không kiểm tra kỹ.
  - Các tài liệu chung (`docs/standup.md`, `docs/ai-usage-log.md`) ban đầu chưa được cập nhật đồng đều ngay khi từng thành viên merge PR code.
- **Hành động cho Phase 3 (Phân công đủ 6 thành viên):**
  - **Hoàng Vũ (`hoangvu1806`):** Viết adapter kho cá thể v1.2 trong `chonoi/inventory.py` trước khi bật `contract_version: "1.2"`, giữ chỗ theo `item_id` và bàn giao trong `day.py`.
  - **Nguyễn An (`AnK17-UIT`) & Từ Huy Bảo (`thbao4545`):** Dùng đơn vị nguyên `240 đơn vị = 1 điểm tươi` (gather `-2/tick`), phát `spoiled` ở ngưỡng `< 30` và gom mất hàng LIFO về `GatherSim._lose_lifo`.
  - **Hà Anh (`hnha02`):** Hao tươi kho quán (`-1/tick` trên thang 240), chốt `base_price` và `cook_started.items` theo độ tươi.
  - **Trần Gia Bảo (`Jay-Gabriel`):** Sửa dứt điểm T-pose nhân vật và cập nhật HUD Godot hiển thị độ tươi / hàng ươn.
  - **Nhật Nguyên (`double-n-021`):** Chỉ làm đúng phạm vi QA/PO (`CHANGELOG.md`, `tests/test_p3_freshness_qa.py` tự kích hoạt khi bật `1.2`, `docs/verification/phase-3.md`, và tổng hợp đầy đủ đóng góp của cả 6 thành viên trong `docs/standup.md`, `docs/ai-usage-log.md`).

## Phase 4 (cuối)
- Rà lại hành động Phase 2: đã làm chưa? vì sao?
- Điều tốt / điều tệ:
- Số liệu: số commit theo người, cách đọc code của nhau, token theo người:
- Một lần AI sai và cách nhóm phát hiện:
- Nếu làm lại, đổi gì:
