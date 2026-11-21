# Phản tư cá nhân — Trần Gia Bảo (`Jay-Gabriel`)

- **Phần mình làm (`client/godot`):** Tìm, chuẩn hóa (`gltf-transform dequantize`) và import 58 model 3D CC0 cho Godot 4.5.1; dựng 3 cảnh 3D (`GatherRiver`, `RestaurantNight`, `DiveUnderwater` 2.5D lặn sông phù sa) với hoạt ảnh bơi `Skeleton3D` và đi bộ/ngồi không T-pose; viết `bench_cmd` (`godot/scripts/bench.gd`, `tools/bench.sh`) và nâng cấp HUD cảnh báo, độ tươi, tương phản cao (`H`) trong `godot/scripts/game.gd`.
- **Đã giúp ai:** Hỗ trợ Hoàng Vũ sửa T-pose trên luồng live gameplay và cung cấp `bench_cmd` cho QA Nhật Nguyên.
- **AI sai ở đâu:** AI dựng cảnh lặn xanh như băng, quên gọi `AnimationPlayer.play()` ở `_live_node()` gây T-pose, và lộn chiều tam giác bờ sông phải. Mình kiểm tra trực quan bằng ảnh chụp thực tế để sửa dứt điểm.
- **Bài học:** Luôn chạy thử trực quan và tách bạch render khỏi sim 60Hz để cả nhóm tích hợp không xung đột.
- **Commit/PR:** PR #4 (`6159fd9`), PR #6 (`215155d`, `ed99bbf`, `c2cb40f`, `34329cd`), PR #10 (`7fa1fa5`), PR #14 (`51c16c6`).
