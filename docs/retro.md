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
- **Rà lại hành động Phase 2:**
  - *Đã làm:* Dùng đơn vị chính xác (`Fraction` / đơn vị nguyên 240) cho độ tươi ở `gather.py`, tách adapter kho cá thể `chonoi/inventory.py` trước khi đổi schema, gom mất hàng LIFO về `GatherSim._lose_lifo`, sửa triệt để T-pose và bổ sung HUD độ tươi / High Contrast trên Godot 3D, cập nhật đủ đóng góp cả 6 thành viên trong `docs/standup.md` và `docs/ai-usage-log.md`.
  - *Còn dang dở nhỏ:* Nhánh `feat/p3-quan-tuoi` của Hà Anh cần được gộp vào `dev` trước khi chuyển cờ `contract_version` từ `1.1` sang `1.2`/`1.3` để 5 test v1.2 tự động bật xanh.
- **Điều tốt:**
  - **Quy trình QA phát hiện lỗi sớm cực hiệu quả:** Báo cáo 5 lỗi thực tế của QA (`BUG-01`..`BUG-05`) giúp nhóm vá ngay `BUG-03` (dead code `gather.py`), `BUG-04` (`bench.gd` đóng băng `_physics_process` khi đo FPS) và `BUG-05` (`tools/bench.sh` lỗi đường dẫn Windows) chỉ sau 10 phút trong PR #25 (`12579b6`).
  - **Hiệu năng & độ ổn định vượt chuẩn:** Benchmark 3D 30 giây đạt `60.0 FPS` / `p1_low_fps = 60.0` (`load_ms: 523ms`), Soak 10 Ngày đạt `10/10` ngày không crash trong `2.068s`, `128/128` test active PASS.
- **Điều tệ:**
  - Ở Phase 2, một số commit lấn sang file lát của bạn khác và có lúc gộp nhánh chưa kiểm tra lại tài liệu chung (`standup.md`, `ai-usage-log.md`). Sang Phase 3–4 đã khắc phục hoàn toàn nhờ khóa phạm vi theo nhánh PR nhỏ.
- **Số liệu (tính tại `ff85a32`):**
  - **Số commit theo thành viên (cả 6 người đều vượt xa ngưỡng >= 3 commit):** Nguyễn An (`AnK17-UIT`: 23), Nhật Nguyên (`double-n-021`: 18), Trần Gia Bảo (`Jay-Gabriel`: 18), Hoàng Vũ (`hoangvu1806`: 18), Hà Anh (`hnha02`: 14), Từ Huy Bảo (`thbao4545`: 12).
  - **Cách đọc code của nhau:** Toàn bộ thay đổi đều đi qua PR vào `dev` (PR #1–#26), có kiểm `unittest` + `check_team.py` và rà soát chéo giữa QA và chủ lát trước khi merge.
  - **Token ước tính theo người:** Ghi chi tiết theo từng phase tại `docs/ai-usage-log.md` (~10k–24k tokens/người/phase).
- **Một lần AI sai và cách nhóm phát hiện:**
  - Khi sinh `godot/scripts/bench.gd` ở Phase 4, AI gọi `world.set_physics_process(false)` để giữ Út Sen đứng yên ở bến `[2, 0]`, vô tình đóng băng luôn đàn cá, bọt khí và tia nắng trong suốt 30s đo FPS. QA phát hiện khi đọc chéo `bench.gd` với `dive_underwater.gd` (báo `BUG-04`) và nhóm đã vá ngay trong PR #25 (`12579b6`).
- **Nếu làm lại, đổi gì:**
  - Chốt cứng bảng phân công file (file ownership) ngay từ phút thứ 5 của mỗi phase và chạy `tests/test_p3_*.py` dạng `@unittest.skipUnless` ngay từ đầu phase để mọi lát nhìn thấy cùng một hợp đồng kiểm thử trước khi code.
