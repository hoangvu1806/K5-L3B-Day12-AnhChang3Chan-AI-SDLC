# Kiểm tra chuyển contract v1.3 — 2026-11-21

- `python -m unittest tests.test_p3_freshness_qa tests.test_quan_lat4.Lat4.test_serve_then_paid_with_tip -v`: 8 test đạt; test Phase 3 được mở rộng để tiếp tục chạy với v1.3.
- `python -m unittest discover -s tests`: 133 test, 17 failure và 1 error. Các test cũ vẫn dùng kho đếm/giỏ chuỗi hoặc yêu cầu manifest đúng v1.1; v1.2 thay thế schema đó. Chưa chuyển các fixture này và chưa kết luận regression đạt.
- `python -m chonoi.headless --mode gather --seed 1 --ticks 600 --out ...` chạy hai lần mã 0; SHA-256 của cả hai: `843ac8f70098da297ce0bd12eb049e1282a8081e4e816b109072a81cba0cd7a9`.
- `python -m chonoi.headless --mode quan --seed 1 --ticks 600 --out ...`: mã 0.
- `python -m chonoi.headless --mode gather --seed 1 --ticks -1 --out ...`: mã 2, không tạo output.
- `python -m chonoi.soak --seed 7 --days 10 --out docs/proof/phase-4/soak-v13.json`: hoàn thành 10 ngày, 0 crash. Lặp lại cùng seed cho kết quả gameplay giống nhau sau khi bỏ `duration_s`.
- Godot 4.7.2: `Godot_v4.7.2-stable_win64_console.exe --headless --path godot --quit-after 5` tải scene chính, mã 0. Đây không phải bản 4.5.1 được dự án chỉ định.
- Benchmark render 4.7.2, seed 42, 1280×720, làm nóng 3 giây, đo 30 giây: [bench-godot-4.7.2.json](bench-godot-4.7.2.json), trung bình 122.15 FPS, 1% low 71.63 FPS, load 497 ms. Chưa xác minh cảnh benchmark có đủ dữ liệu mô phỏng sống theo PRD; không coi đây là bằng chứng benchmark phát hành hoàn chỉnh.
- Chưa thử điều khiển, ba cảnh báo và tương phản trực tiếp hoặc thử đóng gói.
- Sau khi bật extension `burn` với `burn_s: 20`, ba test ngưỡng cháy và giữ chỗ lại trong `tests.test_quan_p2_bep.Burn` đạt. Test toàn bộ chạy 133 test, 18 failure và 1 error: các fixture cũ dùng schema v1.1, và một test cũ còn đòi `burn_s: null` dù extension đã bật. Chưa kết luận regression đạt.

Các file JSONL được tạo thực tế nhưng bị `.gitignore` bỏ qua. `soak-check.json` là kết quả trước migration v1.1, không phải bằng chứng v1.3.
