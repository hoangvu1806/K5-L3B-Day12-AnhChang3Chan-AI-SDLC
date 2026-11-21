# double-n-021 (Bùi Đặng Nhật Nguyên) — phản tư cá nhân (≤ 200 từ)

- **Vai trò:** QA Lead / PO cho nhóm 6 người (`AnhChang3Chan`).
- **Tôi đã làm:**
  - **Phase 1:** Tạo AI Harness (`.agents/skills/`), `docs/contracts/README.md`, `tests/test_p1_team_suite.py`, `tools/qa_stability_suite.py`, `docs/verification/phase-1.md` (`62/62` PASS) (`2162375`).
  - **Phase 2:** Hoàn thiện `tests/test_p2_v11_suite.py`, `docs/verification/phase-2.md`, `docs/retro.md` và bằng chứng tag `phase-2` (`88/88` PASS) (`d3317cf`, `98bf347`).
  - **Phase 3:** Viết `CHANGELOG.md` (v1.2), bộ test tự kích hoạt `tests/test_p3_freshness_qa.py`, nâng cấp `qa_stability_suite.py` dual-schema, đồng bộ nhật ký 6 thành viên (PR #21, `975111e`).
  - **Phase 4:** Rà soát thực chiến phát hiện 5 lỗi (`BUG-01..05`, giúp nhóm vá `BUG-03/04/05` ở PR #25), chạy GPU Benchmark 30s (`60 FPS`), Soak 10 Ngày (`0` crash), viết `docs/verification/phase-4.md` và điều phối `docs/retro.md`.
- **Đã giúp ai:** Hỗ trợ vá lỗi ghép Lát 3–4 (`_cook_plan`), rà lỗi `gather.py`, `bench.gd`, `bench.sh` cho An và Gia Bảo.
- **AI sai ở đâu:** Ở Phase 1 AI nhầm sang đề cá nhân L3; ở Phase 2 AI sửa lấn file của lát khác. Tôi phát hiện qua kiểm tra `git diff` và khóa chặt phạm vi QA ở Phase 3–4.
- **Bài học:** Kiểm thử hộp đen tự động + phân tách rõ phạm vi file theo từng người giúp 6 thành viên tích hợp nhanh mà không xung đột.
