---
name: chonoi-headless
description: Kiểm thử Test Contract Lab 12 qua CLI headless, tái hiện lỗi theo tick và ghi bằng chứng Phase cho Gather hoặc Quán.
---

# Kiểm chứng headless

- Đọc `headless_cmd` trong `game.contract.json`. Dùng `tests/helpers.py` để tạo fixture trong thư mục tạm, chạy CLI và đọc JSONL.
- Dùng seed cố định, fixture nhỏ và `--snapshot-every 1` khi cần xác định tick lỗi. Input ở tick k được xử lý trong bước phát sự kiện ở tick k+1. Snapshot tick 0 thể hiện trạng thái trước input.
- Kiểm tra trạng thái, thứ tự sự kiện và lý do kết thúc theo luật đang sửa. Với luồng Gather sang Quán, dùng `--inventory-out` ở Gather và `--inventory` ở Quán để kiểm tra việc chuyển file kho thực tế. Khi lỗi liên quan đến tính xác định, so sánh byte JSONL giữa hai lần chạy với cùng tham số.
- Chạy `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v` từ gốc repo. Ghi lệnh, kết quả thực tế và phần chưa kiểm chứng trong `docs/proof/` hoặc hồ sơ verification của phase.
