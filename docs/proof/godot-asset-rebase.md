# Kiểm chứng rebase bộ asset Godot

- Rebase `feat/godot-3d-asset-kit` lên `dev` tại `691101b`. Dùng các GLB, metadata import và UID trùng từ `dev`. Giữ cảnh lòng sông cùng phím F3 và gộp nguồn của hai phía vào `CREDITS.md`.
- `PYTHONPATH=tests:. python3 -m unittest discover -s tests` đạt 62/62 test với quyền localhost.
- Godot 4.5.1 tải được scene chính, GatherRiver, RestaurantNight và UnderwaterRiver bằng `--headless --quit-after 5`. Hai scene showcase lần lượt đặt được 181 và 169 model.
- Headless import trên 4.5.1 báo lỗi mở socket nội bộ trong sandbox. Các scene chạy thành công sau import. Cấu hình project từ nhánh asset khai báo 4.7, phiên bản này chưa được kiểm thử ở lần rebase.
