---
name: chonoi-sim
description: Triển khai hoặc sửa luật Gather và Quán của Lab 12 trong chonoi/sim, gồm trạng thái, thứ tự tick, sự kiện và dữ liệu kho.
---

# Phát triển mô phỏng Chợ Nổi

- Từ gốc repo, đối chiếu phần việc trong `TEAM.md`, yêu cầu của phase hiện tại, `game.contract.json` và `docs/contracts/`. Khi thiếu quy định ảnh hưởng đến thứ tự tick hoặc payload, ghi câu hỏi và giả định tạm vào `docs/clarify.md` để PO xác nhận.
- Giữ luật trong `chonoi/sim/`. Dùng số liệu từ tuning, bộ sinh số ngẫu nhiên `Streams` và quy ước ID trong `AGENTS.md`. Kiểm tra tình huống hai hành động xảy ra cùng tick và thứ tự sự kiện khi lượt kết thúc.
- Gather dùng tọa độ `[x, d]` với độ sâu dương hướng xuống. Giỏ lưu theo thứ tự nhặt, phần tử cuối là mới nhất. Dùng `inventory_items()` để lấy số lượng theo nguyên liệu và để runner ghi file khi Gather kết thúc.
- Khi hai lát cùng sửa một module, thống nhất cách đọc và cập nhật trạng thái chung trước khi gộp. Với thay đổi đi qua JSONL hoặc file kho, dùng skill `chonoi-headless` để kiểm tra từ CLI.
