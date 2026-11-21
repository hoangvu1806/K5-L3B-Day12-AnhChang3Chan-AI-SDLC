# Kiểm chứng Gather — Lát 1

- `PYTHONPATH=tests:. python3 -m unittest discover -s tests` đạt 34/34 test khi có quyền mở cổng localhost.
- Hai test headless mới xác nhận chuyển lặn/nổi, oxy tính theo độ sâu cuối tick, chuỗi ngạt/ngất và file kho rỗng khi ngất đúng tick hết giờ.
- Payload sự kiện oxy/ngạt/ngất và tick bắt đầu đếm ngạt đang chờ PO đối chiếu PRD-0. Xem [clarify.md](../clarify.md).
