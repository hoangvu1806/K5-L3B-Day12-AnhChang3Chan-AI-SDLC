# Kiểm chứng hao tươi giỏ Gather

Ngày chạy 2026-11-21. Nhánh đã đồng bộ `origin/dev` tại `1de5552`.

- `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v` đạt 104/104. Test Gather mới kiểm tra ngưỡng 30 trước làm tròn, thứ tự sự kiện và LIFO, tốc độ giảm, ID xuyên Ngày, pause, lực đẩy ở biên, và kết thúc dòng trước khi ngất.
- Chạy CLI `python3 -m chonoi.headless --mode gather --seed 1 --ticks 600 --out gather.jsonl` hai lần và chạy tương tự với mode `quan`. Cả ba lượt thoát mã 0. Hai file Gather trùng byte, SHA-256 `843ac8f70098da297ce0bd12eb049e1282a8081e4e816b109072a81cba0cd7a9`. SHA-256 của Quán là `7704b77b7066ff5282145f0a4f3fa502bd46cdb14a5f0b46d39df853793597ef`.
- CLI với `--ticks -1` thoát mã 2 và không tạo JSONL.
- CLI trên bản sao có manifest v1.2 và `current` xác nhận warning/start/end tại tick 1680/1800/2280. Hai lượt cùng seed trùng byte, SHA-256 `8f1f2784a4bf92631e31d42f9274bdeaaefcb60161cc7fc28a9de80f776c59cb`. Chạy đến giới hạn 1800 vẫn thấy `ticks_left: 480` và kết thúc vì `tick_limit`.
- Manifest repo vẫn ở v1.1. Bàn giao file và kho Quán cần adapter v1.2. Cảnh báo bằng chữ, biểu tượng và âm thanh cần client Godot đọc `current_warning`.
