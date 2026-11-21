# Kiểm chứng bông súng, nhãn cá và HUD Godot

- Godot 4.5.1 chạy scene chính trong chế độ headless và OpenGL Compatibility. Dùng snapshot Gather với bông súng tại `[44, 0]` và cá linh gần người chơi.
- Xác nhận cụm bông súng nổi cao hơn đỉnh sóng, ẩn khi nút hết hàng và hiện lại khi nút mọc lại.
- Xác nhận nhãn Cá linh hiện trên đàn cá trong bán kính 4 m, ẩn khi đi xa và được dọn cùng model khi đàn bị bắt.
- Ảnh OpenGL cho thấy HUD trong mờ, nhãn cá và vùng mặt nước. Smoke test xác nhận vẫn bật được tương phản cao.
- Sau khi thu nhỏ chữ, Godot 4.5.1 import được Be Vietnam Pro Medium từ file cục bộ. Smoke test xác nhận HUD và nhãn cá dùng cùng font, có các ký tự tiếng Việt trong mẫu, và giữ tên cá đọc được ở ảnh 960 × 540.
