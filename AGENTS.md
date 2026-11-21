# AGENTS.md — hướng dẫn chung cho mọi agent AI của nhóm

> Cập nhật file này qua các phase (lịch sử git phải cho thấy điều đó). Ngắn gọn, có lệnh chạy thật.

## Lệnh
- Mở Godot 4.5.1: `godot --editor --path godot`. Kiểm tra scene: `godot --headless --path godot --quit-after 5`.
- Test: `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v`
- Headless: `python3 -m chonoi.headless --mode gather|quan --seed 1 --ticks 600 --out out.jsonl`
- Chơi thử trên trình duyệt: `python3 -m chonoi.live --mode gather|quan` (mở địa chỉ in ra; WASD, E, Space, R)

## Cấu trúc & quy ước
- (Starter Python là TÙY CHỌN; nhóm có thể dùng ngôn ngữ khác nếu giữ Test Contract.) Khung do giảng viên cấp: `chonoi/{headless,inputs,scenario,contract,rng,ids,jsonl,inventory,runner,live}.py` và `chonoi/web/`. Hạn chế sửa; nếu phải sửa thì báo cả nhóm và ghi lại lý do.
- Luật chơi của nhóm: `chonoi/sim/gather.py`, `chonoi/sim/quan.py` (tìm `TODO(nhóm)`).
- **Số liệu chỉ đọc từ `game.contract.json` / dữ liệu**, không hard-code trong luật.
- Mọi số ngẫu nhiên đi qua `Streams` (`chonoi/rng.py`); không dùng `random` toàn cục, không dùng đồng hồ hệ thống.
- Sắp danh sách thực thể bằng `ids.sort_by_id`; cấp id bằng `IdAllocator`.

## Nên tránh
- Không sửa `docs/contracts/`, `game.contract.json` (khóa contract) hoặc schema kho khi chưa báo cả nhóm (đổi hợp đồng ảnh hưởng mọi module).
- Không làm hỏng nhánh chính: trước khi đẩy, chạy test.
- Không bịa yêu cầu: chỗ mơ hồ thì ghi `docs/clarify.md` và hỏi PO.
- Không sửa test cho xanh khi luật sai; phải sửa luật hoặc ghi lý do đổi test trong commit.

## Quy tắc làm việc với agent
- Mỗi agent một việc rõ ràng (một lát). Cho agent đọc PRD/ticket đúng phase và hợp đồng kho trước.
- Agent làm xong phải chạy test và ghi kết quả vào mô tả commit hoặc `docs/proof/`; người đọc lại thay đổi trước khi đẩy.
- Sáng tạo thêm được khuyến khích nhưng phải tắt ở headless (xem README, mục "Tự do sáng tạo").

## Skills / hooks của nhóm
- `.agents/skills/headless-contract-check/` — chạy test + headless + so byte cùng seed + lưu proof. Dùng sau mỗi lần sửa luật và trước khi push.
- `.agents/skills/phase-gate-audit/` — checklist trước khi gắn tag (team, test, commit mỗi người, hồ sơ, bí mật). Dùng cuối mỗi phase.
- [chonoi-sim](.agents/skills/chonoi-sim/SKILL.md) — sửa luật Gather hoặc Quán, thứ tự tick, sự kiện và kho.
- [chonoi-headless](.agents/skills/chonoi-headless/SKILL.md) — kiểm thử Test Contract, tái hiện lỗi và ghi bằng chứng.
- [chonoi-godot](.agents/skills/chonoi-godot/SKILL.md) — dựng scene 3D third-person, camera, HUD và nối với mô phỏng.
- `python tools/qa_stability_suite.py` — chạy fuzz, kiểm tra bất biến, determinism SHA-256, benchmark 10,800 ticks và stress HTTP server `chonoi.live`.

## Chia việc không đụng nhau (6 người)
- Lát 1 (An) và Lát 2 (Bảo) cùng file `chonoi/sim/gather.py`: mỗi người viết helper riêng, `step()` chỉ thêm 1 dòng gọi helper. Lát 1: `_update_oxygen`. Lát 2: `_nearest`, harvest/catch.
- Lát 3 (Vũ) và Lát 4 (Hà Anh) cùng file `chonoi/sim/quan.py`: Lát 3: `_load_customer`, `_tick_patience`, `_spawn_customer`. Lát 4: `_tick_stoves`, `_tick_eating`, `_interact`.
- Pull trước khi sửa `step()`, commit nhỏ, push thường xuyên. Godot (`godot/`) chỉ đọc snapshot, không nhân đôi luật sim.
- Số liệu thật chỉ từ PRD của phase trên lab board; chưa rõ thì ghi `docs/clarify.md`, không đoán.
- [chonoi-sim](.agents/skills/chonoi-sim/SKILL.md) — sửa luật Gather hoặc Quán, thứ tự tick, sự kiện và kho.
- [chonoi-headless](.agents/skills/chonoi-headless/SKILL.md) — kiểm thử Test Contract, tái hiện lỗi và ghi bằng chứng.
- [chonoi-godot](.agents/skills/chonoi-godot/SKILL.md) — dựng scene 3D third-person, camera, HUD và nối với mô phỏng.
