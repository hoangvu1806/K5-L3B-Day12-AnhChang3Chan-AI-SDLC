# Từ Huy Bảo (`thbao4545`) — phản tư cá nhân

- **Tôi đã làm (kèm commit):**
  - Phase 1: triển khai Lát 2 `chonoi/sim/gather.py` (hái nút, mọc lại, bắt cá, giỏ LIFO, cập bến, xuất file kho) + `tests/test_gather_slice2.py` (`2517f47`).
  - Phase 2–3: triển khai thủy quái Cá Sấu & Rắn Hổ Mây (`chonoi/sim/monsters.py`), gom mất hàng LIFO vào `_lose_lifo` + `tests/test_gather_lifo_loss.py` (`06e0c20`) và `tests/test_gather_kho_ca_the.py` (`5aa436a`).
  - Phase 4: bổ sung tín hiệu 3D bếp/khách và chơi lại từ màn tạm dừng trên Godot (`a7a1032`, `d84829d`), vá `BUG-03/04/05` từ rà soát QA (`12579b6`), bật Contract v1.3 `freshness` và `burn_s: 20` (`50cebda`, `e7884bf`).
- **Đã giúp / review:** Phối hợp QA Nhật Nguyên vá lỗi kiểm thử và đồng bộ kho cá thể với An, Vũ (`docs/clarify.md` #18–20).
- **AI sai ở đâu & cách phát hiện:** AI xét hái nút trước cập bến khi trùng bán kính (`docs/clarify.md` #3) và quên kẹp độ sâu từng loài quái; phát hiện qua PRD-0 và test hộp đen.
- **Bài học:** Ghi câu hỏi biên vào `clarify.md` và gom helper dùng chung giúp đổi schema v1.1 → v1.3 ít xung đột.
