# Gợi ý ráp thành 3D Godot

- **Cảnh buổi sáng:** kênh rộng hơn bố cục vùng chơi, nước màu phù sa, bờ thoải, cây dừa nước, ghe chở trái cây, nhà sàn. Camera perspective 3/4 từ phía sau/trên. Gameplay gốc vẫn cố định trục [x,d] (x ngang sông, d là độ sâu) theo PRD, 60Hz.
- **Lặn dưới nước:** thể tích nước từ d=0 đến d=30, sương nước và hạt phù sa, 6 đàn cá ở vị trí đã định, rễ/nước/đáy bùn. Camera third-person là hiển thị; đừng đổi vị trí 2D logical khi xoay camera.
- **Bến cập và hái:** dock [2,0], node N1 (12,0), N2 (28,0), N3 (44,0), N4 (60,0); đặt các scene render tại đúng vị trí từ hợp đồng (chuyển tọa độ sang Godot X/Y/Z bằng adapter duy nhất).
- **Buổi tối:** nhà bè thực 16x10, bếp B1 (2,8), bàn T1 (9,2), NPC khách, ba món ăn, quầy và hàng ghế/giỏ. Không tự mở thêm bếp/bàn vì Test Contract mặc định đúng 1 mỗi loại.
- **Chuyển cảnh:** vật phẩm kho JSON (không phải transfer mesh); hoạt cảnh cập bến và đổi ánh sáng là lớp hiển thị, không đổi mô phỏng.
- **Chú ý:** asset từ 3DAssets.dev dùng hệ tọa độ +Y up, Godot cũng +Y up. Kiểm tra chiều model ghe và uniform scale sau import. Nếu model River Delta có sẵn tấm nước giả, ẩn nước của model để thay bằng shader nước chung.
