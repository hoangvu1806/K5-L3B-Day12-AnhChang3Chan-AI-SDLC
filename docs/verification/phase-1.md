# Ma trận truy vết Phase 1 (Verification Matrix — Nhóm AnhChang3Chan)

| AC / Hạng mục | Cách kiểm chứng | Bằng chứng (link `docs/proof/phase-1/...`) | Kết quả (đạt / chưa đạt — ghi trung thực) |
|---|---|---|---|
| **CON-01**: Headless CLI `--mode gather\|quan`, snapshot tick 0 và đúng 1 dòng `end` | Chạy `test_con_01_ticks_zero_and_end_line` và chạy trực tiếp `chonoi.headless` với `--ticks 120` | [`docs/proof/phase-1/gather_seed1.jsonl`](../proof/phase-1/gather_seed1.jsonl), [`docs/proof/phase-1/quan_seed1.jsonl`](../proof/phase-1/quan_seed1.jsonl) | **Đạt** (`39/39` tests pass) |
| **CON-02**: Tính tất định (Determinism) — cùng seed & inputs cho output giống từng byte | Chạy `test_con_02_deterministic_bytes` (so khớp nhị phân 2 lần chạy seed 7, 300 ticks) | [`docs/proof/phase-1/unittest_run.log`](../proof/phase-1/unittest_run.log) | **Đạt** |
| **CON-03**: Đầu vào / scenario sai thoát mã `2` trước khi ghi file output | Chạy `test_con_03_bad_input_exit_2`, `test_scenario_out_of_domain_exit_2`, `test_khoi_sai_mode_exit_2` | [`docs/proof/phase-1/unittest_run.log`](../proof/phase-1/unittest_run.log) | **Đạt** |
| **MOVE-01..03**: Bơi 60 Hz, ramp tăng/giảm tốc tối đa 6 ticks, hướng mặt, chặn mép `bounds` | Chạy `Movement` suite trong `tests/test_smoke_p1.py` | [`docs/proof/phase-1/unittest_run.log`](../proof/phase-1/unittest_run.log) | **Đạt** |
| **INV-01**: Cập bến (`docked`) hoặc hết giờ (`time`) ghi file kho 1 lần; chế độ `quan` nạp đúng `stock` | Chạy `Integration` suite & `test_gather_dock_priority_and_inventory_persistence` | [`docs/proof/phase-1/unittest_run.log`](../proof/phase-1/unittest_run.log) | **Đạt** |
| **GODOT-3D**: Scene 3D (`Node3D`, `Camera3D`, `DirectionalLight3D`) đồng bộ với `chonoi.live` qua HTTP bridge và hỗ trợ Offline 3D Preview | Chạy `test_godot_3d_scene_and_script_configured` & `test_state_input_and_clean_stop` | [`docs/proof/phase-1/unittest_run.log`](../proof/phase-1/unittest_run.log), [`docs/proof/godot-setup.md`](../proof/godot-setup.md) | **Đạt** |
| **TEAM & HARNESS**: Bảng `TEAM.md` 6 thành viên khớp `team_size: 6`, có 2 skills trong `.agents/skills/` và hợp đồng `docs/contracts/README.md` | Chạy `python3 tools/check_team.py` và `Phase1HarnessAndContracts` | [`docs/proof/phase-1/check_team.log`](../proof/phase-1/check_team.log), [`docs/proof/phase-1/unittest_run.log`](../proof/phase-1/unittest_run.log) | **Đạt** |
| **Lát 1–4 Mở rộng (Oxy/Ngạt/Hái/Bắt cá/Khách/Bếp)**: Các luật chi tiết trong `gather.py` & `quan.py` | Các thành viên Lát 1 (`AnK17-UIT`), Lát 2 (`thbao4545`), Lát 3 (`hoangvu1806`), Lát 4 (`hnha02`) đang tích hợp theo helper riêng | Xem trạng thái commit trên nhánh `main` và `unittest_run.log` | **Đang tích hợp** (Khung core, bơi, cập bến, mọc lại nút, kho, hết giờ đã **Đạt**; các sự kiện chi tiết của 4 lát sẽ cập nhật tiếp khi từng thành viên merge) |

## Đánh giá ngắn
- **Yêu cầu nào đạt / chưa đạt:**
  - **Đạt:** Toàn bộ khung Test Contract v1.0 (39/39 bài kiểm thử tự động pass 100%), tính tất định từng byte, xuất/nhập kho giữa buổi sáng (`gather`) và buổi tối (`quan`), kiểm lỗi đầu vào mã thoát `2`, cấu hình nhóm 6 người (`check_team.py` OK), bộ AI Harness (2 skills + `AGENTS.md`), và thế giới 3D trên Godot 4.5 (`Node3D` cho cả dòng sông 3D và quán nổi 3D kết nối với `chonoi.live`).
  - **Đang hoàn thiện bởi các thành viên Lát 1–4:** Logic chi tiết trong các helper của `gather.py` (tiêu thụ oxy, ngạt, hái nút, bắt cá) và `quan.py` (sinh khách, nấu bếp, phục vụ, tính tiền/tip).
- **Điều cần chỉnh cho phase sau:**
  - Ngay khi 4 thành viên Lát 1–4 push các helper lên `main`, chạy lại skill `headless-contract-check` để cập nhật log bằng chứng trước khi gắn tag.
