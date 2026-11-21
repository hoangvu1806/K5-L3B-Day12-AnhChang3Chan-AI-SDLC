# Kiểm chứng lát 2 — Từ Huy Bảo

Chạy trên Windows PowerShell, Python 3.14:

```powershell
$env:PYTHONPATH='tests;.'
python -m unittest discover -s tests -v
```

Kết quả: 35 test đạt. `test_gather_slice2` kiểm tra nút mọc lại và chọn ID khi cùng khoảng cách, bắt cá khi giỏ thiếu chỗ, bắt ở tick cuối và xuất kho, cùng cập bến xuất kho. Smoke test `test_inv_01_gather_writes_inventory_quan_reads_it` kiểm tra quán đọc file kho từ gather.

Phạm vi kết quả chỉ là các trường hợp đã kiểm tra; phần oxy/ngạt thuộc lát 1 vẫn còn TODO và bộ test hiện tại chưa chứng minh toàn bộ luật Phase 1.
