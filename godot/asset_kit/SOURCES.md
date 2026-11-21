# Nguồn tài sản, giấy phép và tiêu chí chọn

## Trọng tâm 1 — Sông 3D

1. Shader nước có depth blending + foam, bản CC0: https://godotlearning.com/shaders/stylized-water (Godot 4.7, nguồn riêng, có demo)
2. TinyLantern Stylized Water Lite: https://tinylanterndev.itch.io/stylized-water (Godot 4.7+, bản Lite miễn phí nhưng cấm phân phối lại shader gốc)
3. Shader tự viết trong project: `shaders/mekong_water.gdshader` (sóng lăn tăn, nước màu phù sa, độ sâu và bọt gần bờ)
4. Swamp and Mangrove (CC0) có mô hình bùn, rễ, kênh: https://3dassets.dev/packs/swamp-and-mangrove

## Trọng tâm 2 — Cây miền Tây

Tropical Island and Palm Trees (CC0): https://3dassets.dev/packs/tropical-island-ecology

Model lẻ dùng trong scene: Tall coconut palm, Leaning shore coconut palm, Trunkless nipa palm (DỪA NƯỚC), Small red mangrove, Large red mangrove, Banana clump, Giant taro.

Mỗi asset có bản GLB tại URL CDN chính thức; 7 link cố định trong `tools/assets.json`. Nhà cung cấp tuyên bố CC0 1.0 Universal cho tất cả.

## Trọng tâm 3 — Ghe, xuồng, nhà sàn, bến chợ nổi

Bộ **River Delta** có 19 mô hình cùng bảng màu / tỷ lệ: https://1designtool.com/3d/collections/river-delta

Đặc biệt hữu ích:
- Sampans (ghe sông): https://1designtool.com/3d/models/river-delta-sampans
- Long-tail boat (ghe máy đuôi tôm): https://1designtool.com/3d/models/river-delta-long-tail-boat
- Stilt houses: https://1designtool.com/3d/models/river-delta-stilt-houses
- Floating docks: https://1designtool.com/3d/models/river-delta-floating-docks
- Rice store: https://1designtool.com/3d/models/river-delta-rice-store
- Fruit baskets, nets, fish traps, monkey bridge, conical hats: xem từng model trong bộ

Giấy phép: https://1designtool.com/3d/license — được dùng, sửa, kết hợp trong game, ứng dụng; **KHÔNG được tái phân phối model thô như pack / thư viện**. Vì vậy ZIP này chứa *script tải trực tiếp từ nhà phát hành*, không bao gồm lại model River Delta.

Xuồng gỗ: https://tevy.dev/models/flat-bottom-boat — CC0; 3 LOD, có ván gỗ và lòng thuyền.

## Bếp, quán và đạo cụ thêm (CC0; chưa gắn sẵn vào scene)

- KayKit Restaurant Bits: https://kaylousberg.itch.io/restaurant-bits — 140+ models, CC0, glTF/FBX/OBJ.
- KayKit Furniture Bits: https://kaylousberg.itch.io/furniture-bits — 50+ models, CC0.
- KayKit Restaurant Bits GitHub chính chủ, có thư mục addon Godot: https://github.com/KayKit-Game-Assets/KayKit-Restaurant-Bits-1.0

## Bản sắc Tây Nam Bộ

Nguồn này làm được bản sắc chợ nổi 3D khá tốt. Một số chi tiết cần tự dựng / thay vì pack chung không có: ghe ba lá đúng hình dáng địa phương; dừa nước dọc mương; cầu ván hẹp; bếp củi và bếp than; bông điên điển; bông súng; cá lóc/cá linh; áo bà ba, khăn rằn, nón lá của Út Sen.

Dựa trên PRD Phase 1, scene nghệ thuật không được tự ý đổi tick logic, quyền điều khiển, vị trí node cá và logic Test Contract.
