# Changelog

Mọi thay đổi đáng chú ý của **Quán Ăn Chợ Nổi** (Nhóm `AnhChang3Chan`) qua các phase SDLC được ghi nhận tại đây.

---

## [Phase 3 — v1.2] — TICKET-03 "Mùa Nước Nổi" (Change Request)

### BREAKING CHANGES (Thay thế luật cũ v1.0 / v1.1)
1. **Kho đếm theo loại → Kho cá thể (`{"items": [...]}`):**
   - **Cũ (`v1.0` / `v1.1`):** `{"items": {"ca_linh": 1, "ca_loc": 1}}` (object đếm theo loại).
   - **Mới (`v1.2`):** `{"items": [{"id": "I1", "kind": "ca_linh", "fresh": 100}, {"id": "I2", "kind": "ca_loc", "fresh": 97.5}]}` (mảng cá thể; kho rỗng là `{"items": []}`).
   - Khi `contract_version: "1.2"`, file kho đếm cũ hoặc sai schema (`kind` lạ, `id` trùng, `fresh` ngoài `[0, 100]`) **bắt buộc thoát mã `2`**.
   - ID cá thể cấp `I1, I2, ...` theo thứ tự vào giỏ, tăng liên tục xuyên pha và xuyên Ngày (không tái sử dụng).
2. **Giữ chỗ theo lượng → Giữ chỗ theo ID cá thể (`customers[].reserved`):**
   - **Cũ (`v1.1`):** `reserved: {"ca_loc": 1}`.
   - **Mới (`v1.2`):** `reserved: ["I1"]` (mảng ID cá thể khả dụng tươi nhất của từng loại trong công thức, hòa theo `id`).
   - Nếu cá thể đang giữ vừa ươn (`fresh < 30`), nhả toàn bộ phần giữ của đơn và thử giữ lại đúng 1 lần theo thứ tự `(order_tick, id bàn)`; không đủ thì đơn thường chuyển `unfulfillable`.
3. **Giá niêm yết → Giá chốt theo độ tươi (`base_price`):**
   - Khi bắt đầu nấu (`cook_started`, kèm `data.items` sắp theo `kind` rồi `id`), tiêu đúng các ID đang giữ và chốt:
     `base_price = floor(giá niêm yết × trung bình fresh của các cá thể dùng / 100)`.
   - Nếu đủ điều kiện boa, áp `floor(base_price × 0.2)` trên giá đã chốt.

### Added (Độ tươi & Manifest v1.2)
- Manifest `game.contract.json`: nâng `contract_version: "1.2"`, thêm khối `freshness`:
  `{"initial": 100, "gather_decay_per_s": 0.5, "quan_decay_per_s": 0.25, "spoiled_below": 30}`.
- Quy tắc hao tươi chuẩn xác bằng đơn vị nguyên (`240 đơn vị = 1 điểm tươi`: `gather` giảm `2 đơn vị/tick`, `quan` giảm `1 đơn vị/tick`, `pause` dừng hao tươi, món chín không hao).
- Sự kiện mới `spoiled`: phát đúng 1 lần khi `fresh` đi từ `>= 30` xuống `< 30`, `data: {"item_id": ..., "kind": ..., "location": "hold"|"stock"}` (nhiều cá thể cùng vượt ngưỡng phát theo `id`).
- `monster_hit.lost` và `faint.lost` đổi sang mảng cá thể `{id, kind, fresh}` theo thứ tự bỏ LIFO.
- Bộ kiểm thử Phase 3 hộp đen (`tests/test_p3_freshness_qa.py`) và nâng cấp `tools/qa_stability_suite.py` tương thích cả `v1.1` (dict) lẫn `v1.2` (list cá thể).

### Hướng dẫn cập nhật Fixture & Test khi chuyển từ v1.1 → v1.2
| Thành phần | Trước (`v1.1`) | Sau (`v1.2`) |
|---|---|---|
| `gather.hold` | `["ca_loc", "bong_sung"]` | `[{"id": "I1", "kind": "ca_loc", "fresh": 100}, {"id": "I2", "kind": "bong_sung", "fresh": 100}]` |
| `quan.stock` / `inventory.json` | `{"ca_loc": 2}` / `{"items": {"ca_loc": 2}}` | `[{"id": "I1", "kind": "ca_loc", "fresh": 100}, {"id": "I2", "kind": "ca_loc", "fresh": 100}]` |
| `customers[].reserved` | `{"ca_loc": 1}` | `["I1"]` |
| Giá món & boa | `price` niêm yết cố định | `base_price = floor(price × avg_fresh / 100)` chốt lúc `cook_started` |

### Chiến lược tích hợp giữ `main` luôn xanh
1. Adapter kho cá thể (`chonoi/inventory.py`, `chonoi/scenario.py`) hỗ trợ chọn schema theo `contract_version` (`1.1` vs `1.2`).
2. Các lát `gather.py`, `quan.py`, `day.py` và HUD Godot triển khai song song trên nhánh riêng.
3. QA kiểm chứng smoke ngưỡng `fresh: 30` → `spoiled` ở tick 1, smoke bàn giao file kho cá thể, và regression P1–P2 trên `dev` trước khi bật `contract_version: "1.2"` và merge vào `main` gắn tag `phase-3`.

---

## [Phase 2 — v1.1] — TICKET-02 "Một ngày ở chợ nổi" (Tag `phase-2`)

### Added
- Nâng `contract_version` lên `"1.1"` với số liệu chuẩn: 6 nguyên liệu (`ca_keo`, `keo_neo` mới), 6 nút hái (`N1..N6`), 8 đàn cá đầu ca, 6 món ăn, 2 bếp (`B1, B2`), 4 bàn (`T1..T4`), kế hoạch `day_plan` D1–D5 và `shop` nâng cấp `oxygen`/`hp`.
- Chuyển động đàn cá (`1.5 m/s`, đổi hướng theo seed ở bước 120, phản xạ mép) và sinh cá mới theo lịch (`phase_tick = 360 * k`, trần 12 đàn).
- Hệ thống thủy quái (`chonoi/sim/monsters.py`): Cá Sấu Năm Chèo (`M1`, `M2`) & mở rộng `snake` Rắn Hổ Mây (`M3`) — `patrol`/`chase`/`hit` (mất 1 Máu + `floor(n/2)` LIFO + bất tử 90 tick + `recoil` 60 tick) & `faint(cause="monster")`.
- Chế độ vòng ngày `--mode day` (`chonoi/sim/day.py`, `--days 1..5`), `ShopSim`, `pause`/`resumed`, đóng ca Quán, thứ tự nấu theo `(order_tick, table_id)` và mở rộng cháy món `burn` (`dish_burnt`).
- Kết nối Godot 3D trực tiếp với `chonoi.live` (`godot/scenes/Game.tscn`, `godot/scripts/game.gd`, `sim_link.gd`).
- Bộ test `tests/test_day_mode.py`, `tests/test_quan_p2_bep.py`, `tests/test_p2_v11_suite.py` (**88/88 tests PASS**) và bằng chứng `docs/proof/phase-2/`.

---

## [Phase 1 — v1.0] — PRD-0 (Tag `phase-1`)

### Added
- Triển khai đủ 4 lát lõi: Lát 1 (bơi, oxy, ngạt, Máu, ngất), Lát 2 (hái nút, bắt cá, giỏ LIFO, cập bến, file kho), Lát 3 (khách, giữ chỗ, kiên nhẫn, `no_dish`), Lát 4 (bếp, bưng, phục vụ, tiền, boa, uy tín).
- Dựng khung Godot 3D và bộ 3D assets Tây Nam Bộ (`CREDITS.md`).
- Thiết lập AI Harness (5 skills trong `.agents/skills/`, `AGENTS.md`), hợp đồng tích hợp `docs/contracts/README.md`, công cụ kiểm thử ổn định `tools/qa_stability_suite.py` và bằng chứng `docs/proof/phase-1/` (**62/62 tests PASS**).
