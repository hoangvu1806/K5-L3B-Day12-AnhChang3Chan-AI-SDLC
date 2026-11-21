# Credits

Liệt kê asset ngoài (nguồn, giấy phép) và công cụ hỗ trợ đã dùng trong dự án **Quán Ăn Chợ Nổi**.

## 3D Environment & Gameplay Assets (`godot/assets/external/`)

### 1. Cây miền Tây (`godot/assets/external/tropical/`) — CC0 1.0 Universal
- Nguồn: [Tropical Island and Palm Trees — 3DAssets.dev](https://3dassets.dev/packs/tropical-island-ecology)
- Giấy phép: **CC0 1.0 Universal**
- Danh sách file (đã dequantize về glTF 2.0 chuẩn cho Godot 4.5.1):
  - `coconut_tall.glb`, `coconut_lean.glb`, `nipa_palm.glb`, `mangrove_small.glb`, `mangrove_large.glb`, `mangrove_red.glb`, `banana_clump.glb`, `taro.glb`

### 2. Xuồng gỗ (`godot/assets/external/boats/`) — CC0 1.0 Universal
- Nguồn: [Flat Bottom Boat — tevy.dev](https://tevy.dev/models/flat-bottom-boat)
- Giấy phép: **CC0 1.0 Universal**
- Danh sách file (đã giải nén `EXT_meshopt_compression` & `KHR_mesh_quantization` cho Godot 4.5.1):
  - `flat_boat.glb`

### 3. Cá, Hoa Súng, Sen & Thủy sinh (`godot/assets/external/aquatic/`) — CC0 1.0 Universal
- Nguồn: [3DAssets.dev](https://3dassets.dev/) & [Quaternius Animated Cute Fish Pack](https://quaternius.com/packs/cutefish.html) (via `codepawl/quaternius-glb`)
- Giấy phép: **CC0 1.0 Universal**
- Danh sách file:
  - `fish_carp.glb`, `fish_perch.glb`, `fish_whole_raw.glb`, `fish_ca_keo.glb` (animated), `ca_ho.glb` (animated), `lotus_clump.glb`, `lily_pads_blossom.glb`, `lily_pads_swamp.glb`, `flower_yellow.glb`, `keo_neo.glb`

### 3c. Thủy quái & Vũ khí Phase 2 (`godot/assets/external/monsters/`, `props/`) — CC0 1.0 Universal
- Nguồn: [3DAssets.dev](https://3dassets.dev/) (Australian Outback Animals, Reptiles/Amphibians, Wipe Day Survival Island)
- Giấy phép: **CC0 1.0 Universal**
- Danh sách file (đã dequantize cho Godot 4.5.1):
  - `monsters/ca_sau.glb` (Cá Sấu Năm Chèo), `monsters/ran_ho_may.glb` (Rắn Hổ Mây), `props/wooden_spear.glb` (Lao xua)

### 3b. Địa hình & Thủy sinh Dưới Lòng Sông (`godot/assets/external/underwater/`) — CC0 1.0 Universal
- Nguồn: [3DAssets.dev](https://3dassets.dev/) (Coral Reef, Sunken City, Tropical Island Ecology, Stylized Trees and Rocks Kit, Primeval Frontier, Beach Surf & Paddle Kit)
- Giấy phép: **CC0 1.0 Universal**
- Danh sách file (đã dequantize cho Godot 4.5.1):
  - `kelp_forest.glb`, `kelp_cluster.glb`, `seaweed_rock.glb`, `cliff_basalt.glb`, `cliff_block.glb`, `boulder_large.glb`, `boulder_mossy.glb`, `driftwood_rootball.glb`, `driftwood_log.glb`

### 4. Nhân vật 3D (`godot/assets/external/characters/`) — CC0 1.0 Universal
- Nguồn: [Quaternius Animated Women Pack](https://quaternius.com/packs/animatedwoman.html) (via `codepawl/quaternius-glb`) & [3DAssets.dev](https://3dassets.dev/)
- Giấy phép: **CC0 1.0 Universal**
- Danh sách file:
  - `ut_sen_girl.glb` (`Smooth_Female_Casual`, rigged + 12 animations — nhân vật bé gái Út Sen)
  - `customer_girl.glb` (`Smooth_Female_Dress`, rigged + 12 animations — khách nữ quán ăn)
  - `tidal_navigator.glb`, `villager_woman.glb`, `villager_man.glb`

### 5. Đèn lồng (`godot/assets/external/props/`) — CC0 1.0 Universal
- Nguồn: [3DAssets.dev](https://3dassets.dev/) (Imperial China Palace and Garden, Izakaya Alley)
- Giấy phép: **CC0 1.0 Universal**
- Danh sách file (đã dequantize cho Godot 4.5.1):
  - `lantern_silk.glb`, `lantern_paper.glb`

### 6. Bếp, Nồi, Bàn Ghế & Món Ăn (`godot/assets/external/kitchen/`) — CC0 1.0 Universal
- Nguồn: [KayKit Restaurant Bits 1.0 — Kay Lousberg](https://github.com/KayKit-Game-Assets/KayKit-Restaurant-Bits-1.0)
- Giấy phép: **CC0 1.0 Universal**
- Danh sách file (`.gltf` + `.bin` + `restaurantbits_texture.png`):
  - `stove_single`, `pot_A_stew`, `pan_A`, `stew_bowl`, `food_dinner`, `plate`, `bowl`, `table_round_A`, `chair_stool`, `cuttingboard`

### 7. Bối cảnh Chợ Nổi / River Delta (`godot/assets/external/river_delta/`) — 1DesignTool Game Use
- Nguồn: [River Delta Collection — 1DesignTool](https://1designtool.com/3d/collections/river-delta)
- Giấy phép: [1DesignTool 3D License](https://1designtool.com/3d/license) (cho phép dùng, sửa, tích hợp trong game; không phân phối lại như thư viện asset thô)
- Danh sách file:
  - `sampans.glb`, `long_tail_boat.glb`, `stilt_houses.glb`, `floating_docks.glb`, `rice_store.glb`, `nets.glb`, `fruit_baskets.glb`, `fish_traps.glb`, `monkey_bridge.glb`, `conical_hats.glb`
- Asset cài thêm trên từng máy bằng `python3 godot/tools/download_full_assets.py --river-delta`.

### 8. Shader & Showcase Scene
- `godot/shaders/mekong_water.gdshader`: Shader nước phù sa tự viết.
- `godot/scripts/delta_showcase.gd`, `godot/scenes/GatherRiver.tscn`, `godot/scenes/RestaurantNight.tscn`: Scene trưng bày bối cảnh & asset 3D Tây Nam Bộ (tương thích Godot 4.5.1).
- `godot/scenes/UnderwaterRiver.tscn` và hai model cá mẫu trong `godot/assets/legacy/` lấy từ bộ asset kit v3. Tài liệu của bộ nằm ở `godot/asset_kit/`.

### 9. Các bộ asset bổ sung (`godot/assets/downloaded_packs/`)

| Pack | Dùng cho | Giấy phép | Nguồn |
|---|---|---|---|
| Tropical Island and Palm Trees | Cây ven sông | CC0 | [3DAssets.dev](https://3dassets.dev/packs/tropical-island-ecology) |
| Swamp and Mangrove | Rễ, bờ bùn, cây nước | CC0 | [3DAssets.dev](https://3dassets.dev/packs/swamp-and-mangrove) |
| Quiet Lake Fishing | Cá, bến, hoa súng và thuyền mẫu | CC0 | [3DAssets.dev](https://3dassets.dev/packs/quiet-lake-fishing) |
| KayKit Restaurant Bits | Bếp, món ăn và dụng cụ | CC0 | [KayKit](https://github.com/KayKit-Game-Assets/KayKit-Restaurant-Bits-1.0) |
| KayKit Furniture Bits | Bàn ghế và quầy | CC0 | [KayKit](https://github.com/KayKit-Game-Assets/KayKit-Furniture-Bits-1.0) |
| Gobkit Characters Vol. 1 | Nhân vật mẫu | CC0 | [Gobkit](https://gobkit.itch.io/gobkit-free-character-pack-vol-1) |

Các bộ CC0 có thể tải bằng `python3 godot/tools/download_full_assets.py --core`. Script `godot/tools/dequantize_glb.py` chuyển đổi các model dùng `KHR_mesh_quantization` để Godot import được.
