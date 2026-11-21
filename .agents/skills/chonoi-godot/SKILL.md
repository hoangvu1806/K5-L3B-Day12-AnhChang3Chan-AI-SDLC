---
name: chonoi-godot
description: Phát triển scene, camera third-person, đầu vào, HUD hoặc tích hợp dữ liệu mô phỏng cho client Godot 3D của Lab 12.
---

# Tích hợp Godot 3D third-person

- Đọc `godot/project.godot` và scene chính trước khi chỉnh. Repo dùng Godot 4.5.1 Standard, GDScript và renderer Compatibility. Kiểm tra trạng thái scene để biết phần nào vẫn là bản thử.
- Dùng giao diện trong `docs/contracts/` và snapshot của mode tương ứng để nối client. Godot lấy input và hiển thị trạng thái. Mô phỏng quyết định kết quả di chuyển, oxy, giỏ và tương tác.
- Với Gather, ánh xạ `[x, d]` sang `Vector3(x, -d, 0)` cho vùng mô phỏng hiện tại. Đặt camera bám sau nhân vật. Áp dụng nội suy ở lớp hiển thị nếu cần, còn tọa độ chấm điểm và tương tác lấy từ sim.
- Chạy `godot --headless --path godot --quit-after 5` từ gốc repo để kiểm tra scene tải được. Với camera, đầu vào và HUD, chạy scene trong editor để kiểm tra trực tiếp và ghi rõ phần đã thử.
