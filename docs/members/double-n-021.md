# double-n-021 (Bùi Đặng Nhật Nguyên) — phản tư cá nhân (≤ 200 từ)

- **Vai trò:** QA Lead / PO nhóm `AnhChang3Chan` (6 thành viên).
- **Tôi đã làm:**
  - **P1:** Tạo AI Harness (`.agents/skills/`), `docs/contracts/README.md`, `tests/test_p1_team_suite.py`, `tools/qa_stability_suite.py`, `docs/verification/phase-1.md` (`62/62` PASS, `2162375`).
  - **P2:** Viết `tests/test_p2_v11_suite.py`, `docs/verification/phase-2.md`, `docs/retro.md` và bằng chứng tag `phase-2` (`88/88` PASS, `d3317cf`, `98bf347`).
  - **P3:** Viết `CHANGELOG.md` (Breaking Changes v1.2), bộ test `tests/test_p3_freshness_qa.py`, nâng cấp `qa_stability_suite.py`, đồng bộ tài liệu 6 thành viên (PR #21, `975111e`).
  - **P4:** Rà lỗi thực chiến giúp nhóm vá `BUG-03/04/05` (PR #25) và bật `burn_s: 20`; migrate 19 test v1.1 đưa toàn repo lên xanh **133/133 PASS** trên v1.3; chốt `docs/verification/phase-3.md`, `phase-4.md` và `docs/retro.md`.
- **Đã giúp ai:** Vá `_cook_plan` (Lát 3–4), rà lỗi `gather.py`, `bench.gd`, `bench.sh`, `game.contract.json` và chuyển fixture test cho cả nhóm.
- **AI sai ở đâu:** P1 AI nhầm đề L3; P2 AI sửa lấn file lát khác; P4 `qa_stability_suite.py` so `== "1.2"` bỏ sót `"1.3"`. Phát hiện qua kiểm thử thực tế và `git diff`.
- **Bài học:** Test hộp đen sớm + khóa phạm vi file theo vai giúp nhóm 6 người tích hợp nhanh, không xung đột.
