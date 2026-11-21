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
  - *Đã làm:* Dùng số học chính xác (`Fraction`) tránh lệch dấu phẩy động ở ngưỡng `30` cho cả `gather.py` và `quan.py`; xây dựng adapter kho cá thể `chonoi/inventory.py` trước khi bật `1.2`/`1.3`; gom mất hàng LIFO về `GatherSim._lose_lifo`; hoàn thiện HUD thẻ kính Godot 3D + cảnh báo + chế độ tương phản cao (`H`); đồng bộ đầy đủ tài liệu 6 thành viên và đưa bộ test regression v1.3 về **133/133 PASS**.
  - *Bài học giữ tiến độ:* Việc bật `contract_version: "1.3"` và `burn_s: 20` diễn ra muộn hơn kế hoạch ban đầu, dẫn tới 19 test v1.1 cũ bị đỏ trước khi QA kịp migrate đồng loạt trong nhánh cuối.
- **Điều tốt:**
  - **Vòng lặp QA phát hiện lỗi -> nhóm vá ngay cực hiệu quả:** Báo cáo lỗi thực chiến của QA giúp nhóm vá ngay `BUG-03/04/05` trong PR #25 (`12579b6`), bật `burn_s: 20` khớp `extensions` trong `e7884bf`, sửa lỗi mất kết nối `sim_link.gd` trong `50cebda`, và tách riêng bước migrate 19 test v1.1 cũ lên xanh **133/133 PASS** trên v1.3 mà không đụng logic lõi.
  - **Chất lượng kỹ thuật & hiệu năng ổn định:** `Soak 10 Ngày` v1.3 đạt `10/10` ngày không crash, tất định 100%; GPU Benchmark 30s đạt `122.15 FPS` (`p1_low: 71.63 FPS`, `load: 497ms`) trên Godot 4.7.2; `QA Stability Suite` đạt `8/8` Fuzz/Invariant, `2/2` SHA-256 từng byte và `100/100` Live HTTP 200 OK.
- **Điều tệ:**
  - Ở Phase 2 có giai đoạn commit lấn phạm vi lát của bạn khác và tài liệu chung (`standup.md`, `ai-usage-log.md`) chưa được cập nhật đồng đều ngay khi merge PR; sang Phase 3–4 đã khắc phục hoàn toàn bằng PR nhỏ theo đúng sở hữu file.
- **Số liệu (tính tại `e7884bf` trên toàn repo):**
  - **Số commit theo thành viên (cả 6 người đều vượt xa ngưỡng >= 3 commit):** Nguyễn An (`AnK17-UIT`: 23), Nhật Nguyên (`double-n-021`: 18+), Trần Gia Bảo (`Jay-Gabriel`: 18), Hoàng Vũ (`hoangvu1806`: 18), Hà Anh (`hnha02`: 14), Từ Huy Bảo (`thbao4545`: 14).
  - **Cách đọc code của nhau:** Toàn bộ thay đổi hợp nhất qua PR vào `dev` (PR #1–#28), có rà soát chéo giữa QA và chủ lát cùng kiểm chứng hộp đen `unittest` + `check_team.py`.
  - **Token ước tính theo người:** Ghi chi tiết theo từng phase tại `docs/ai-usage-log.md` (~10k–24k tokens/người/phase).
- **Một lần AI sai và cách nhóm phát hiện:**
  - Khi tạo `godot/scripts/bench.gd` ở Phase 4, AI đặt `world.set_physics_process(false)` để giữ Út Sen đứng yên ở bến `[2, 0]`, vô tình đóng băng luôn đàn cá, bọt khí và tia nắng suốt 30 giây đo FPS. QA phát hiện khi đọc chéo `bench.gd` với `dive_underwater.gd` (báo `BUG-04`), và nhóm đã vá ngay trong PR #25 (`12579b6`). Ngoài ra, khi chuyển sang `contract_version: "1.3"`, QA chạy `tools/qa_stability_suite.py` phát hiện ngay điều kiện `== "1.2"` bỏ sót `"1.3"` và đã sửa sang `>= (1, 2)`.
- **Nếu làm lại, đổi gì:**
  - Chốt bảng sở hữu file (file ownership) và cơ chế adapter/test tự kích hoạt (`>= (1, 2)`) ngay từ đầu mỗi phase để tránh lỗi đỏ đồng loạt khi nâng phiên bản contract.
