# Quán Ăn Chợ Nổi — FULL 3D ASSET FINDER / GODOT KIT v3

**Mục tiêu:** sông chợ nổi 3D Tây Nam Bộ có phối cảnh và chiều sâu, mặt nước/nước sâu, ghe có lòng, rừng dừa nước, NPC, khu quán và mô hình cá. Bộ này là công cụ tải + project dựng cảnh, KHÔNG phải game hoàn thiện.

## CÀI NHANH (Máy bạn phải có Internet)

```bash
python3 tools/download_full_assets.py --all
```

Lệnh trên lấy các pack CC0 từ nhà phát hành (model GLB hoặc zip GitHub) và **River Delta** về thư mục dự án trên máy bạn. Asset River Delta chỉ dùng theo giấy phép sử dụng trong game; không phát tán lại dưới dạng bộ model thô. Nếu cần chỉ CC0:

```bash
python3 tools/download_full_assets.py --core
```

Sau đó mở `project.godot` trong **Godot 4.x**. F1 = cảnh sông, F2 = quán bè, F3 = cảnh khảo sát dưới nước. Đây là **scene xem asset 3D**, không có bơi, bắt cá, nấu ăn hay lưu kho. Camera dùng perspective; chuột phải + kéo để xoay, cuộn zoom. Bản shader mặc định tự viết tương thích GL Compatibility, bản CC0 nước đẹp hơn ở `docs/SOURCES_FULL.md` tùy Godot 4.7.

## Danh sách toàn bộ khu vực và asset

| Khu vực | Nguồn | Trạng thái cài đặt |
|---|---|---|
| Sông, cây dừa, dừa nước, chuối | Tropical Island pack (70 GLB) | script tải CC0 |
| Bờ bùn, rễ, cây đước, hoa súng, môi trường lặn | Swamp and Mangrove (76 GLB) | script tải CC0 |
| Cá nước ngọt, cần câu, bến, hoa súng | Quiet Lake Fishing (~26 GLB) | script tải CC0; loài cá chỉ làm mẫu |
| Ghe, nhà sàn, cầu khỉ, chợ trái cây | River Delta (19 model) | script lấy về **local-only**, không đóng raw vào zip |
| Xuồng gỗ lòng thuyền | Flat-Bottom Boat | script tải CC0 |
| Bếp, món ăn, dụng cụ | KayKit Restaurant Bits (140+ model) | script tải CC0 từ Github gốc |
| Bàn ghế/quầy nội thất | KayKit Furniture Bits (50+ model) | script tải CC0 từ Github gốc |
| NPC khách/nhân vật nữ với animation cơ bản | Gobkit free chars | script tải một số nhân vật CC0 |
| Út Sen chính xác với áo bà ba và khăn rằn | Chưa có asset đủ chuẩn | Cần sửa trang phục model người nữ, gắn animation bơi |
| Animation bơi | KinemIQ | tải/export thủ công, retarget |
| Cá lóc thật | Sketchfab CC0 spotted snakehead | tải thủ công, kiểm tra loài cá cụ thể |
| Cá linh thật | chưa xác minh được asset phù hợp | phải tự tạo/chỉnh model |
| Bông điên điển | chưa xác minh được asset đúng loài | phải tự tạo/chỉnh |
| Nước phản chiếu và bọt theo độ sâu | GodotLearning Water Shader | tùy chọn, tải thủ công (Godot 4.7) |
| Scene kiểm thử headless | theo PRD | CHƯA làm |

## Cần phân biệt

1. **Full danh mục asset**: có đủ nhóm để dựng game về mặt hình ảnh, nhưng KHÔNG phải asset đã được gán vào một level gameplay hoàn chỉnh.
2. **Full cảnh playable**: còn phải tạo animation, điều khiển, nước trong suốt phù hợp khi lặn, catch/gather, HUD, camera, collision và riêng Test Contract.
3. Đây là môi trường 3D minh họa và downloader; chưa kiểm thử bằng Godot trên máy thực tế. Nếu một link/CDN thay đổi, script sẽ báo lỗi, không giả vờ tải thành công.

## Bản quyền và phân phối

- KayKit và 3DAssets.dev/tevy/Gobkit được công bố CC0 tại các URL trong `docs/SOURCES_FULL.md`.
- River Delta của 1DesignTool cho phép tích hợp vào game, nhưng cấm phát tán model gốc như asset pack. VÌ THẾ chỉ có mã tải từ trang họ.
- Các nguồn itch.io yêu cầu nhấn download sẽ do bạn tự tải; mọi file đã tải cần giữ giấy phép đi kèm.

## File của bộ này
- `tools/download_full_assets.py`: script download qua mạng của bạn.
- `tools/sources.json` và `docs/SOURCES_FULL.md`: nguồn/giấy phép.
- `scenes/GatherRiver.tscn`, `scenes/RestaurantNight.tscn`: hai cảnh 3D phối cảnh.
- `scenes/UnderwaterRiver.tscn`: khảo sát lòng sông 3D, có placeholder cá do bộ v2 trước tạo.
- `assets/legacy/*.glb`: 2 placeholder cá (không thay thế asset cá lóc/linh chất lượng cao).
