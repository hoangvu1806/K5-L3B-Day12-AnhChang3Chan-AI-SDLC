# Day 12 — AI SDLC: Quán Ăn Chợ Nổi
[Video gameplay](https://drive.google.com/file/d/1LRdNh1QsiARKVQeRwvBJWVufNE6kW5vt/view?usp=sharing)

> **Làm theo nhóm 4–6 người** · Dùng AI để xây game 2D qua **4 phase** trong **3 giờ**: Út Sen lặn bắt cá, hái rau trên mặt nước rồi tối mở quán phục vụ khách.
> **Yêu cầu từng phase mở đúng mốc giờ tại lab board:** **[Chợ Nổi Lab](https://claude.ai/artifact/E35v787wSx2wDgPTNhMVDg)** (cần đăng nhập claude.ai; có trợ giảng AI cho từng phase).

## Bắt buộc (chỉ có thế)

Cách làm việc kỹ thuật là **tự do** (push thẳng, nhánh + PR, pair, có hay không CI…). Cái bắt buộc:

1. **Một repo chung:** trưởng nhóm **fork** repo này, đặt tên `K5-L3B-LAB-Day12-AI-SDLC-<ten-nhom>`, thêm mọi thành viên làm collaborator (*Settings → Collaborators*, quyền Write) và để repo **public** (giảng viên xem được, không cần mời).
2. **Cả nhóm cùng commit** bằng tài khoản GitHub của mình, mỗi người **≥ 3 commit có nội dung** (làm cặp thì ghi `Co-authored-by:`).
3. **Điền [`TEAM.md`](TEAM.md):** danh sách thành viên + thỏa thuận làm việc nhóm; sửa `team_size` trong [`game.contract.json`](game.contract.json). Commit của người không có trong `TEAM.md` không được tính.
4. **Gắn tag** `phase-1` … `phase-4` đúng hạn; chạy được tại từng tag.
5. **Ghi chép tối thiểu:** `docs/verification/phase-n.md`, `docs/clarify.md`, `docs/ai-usage-log.md`, `docs/retro.md`, `docs/members/<handle>.md`.

## Bắt đầu nhanh

```bash
git clone <fork-của-nhóm> && cd <fork-của-nhóm>
bash tools/play.sh
```

Game cần chế độ **headless** theo Test Contract (`python3 -m chonoi.headless --mode gather|quan …`) để được chạy và chấm tự động. **Công nghệ không ràng buộc**: khung Python trong `chonoi/` chỉ là gợi ý, chi tiết ở [`docs/STARTER.md`](docs/STARTER.md).

## Chạy project Godot

Trên macOS hoặc Linux, cần Bash, Python 3 và [Godot 4.5.1 Standard](https://godotengine.org/download/archive/4.5.1-stable/) trên PATH. Có thể đặt `GODOT_BIN` thành đường dẫn tới Godot. Từ gốc repo, `bash tools/play.sh` import tài sản, chạy mô phỏng 5 Ngày và mở game. Đóng Godot sẽ dừng server mô phỏng.

Khi phát triển, có thể mở hai tiến trình bằng hai terminal.

```bash
python3 -m chonoi.live --mode day --days 5 --presentation
godot --path godot
```

Server phải tiếp tục chạy trong lúc chơi và có thể dừng bằng Ctrl+C. Dùng WASD hoặc phím mũi tên để di chuyển, E để hái/cập bến/nấu/bưng/phục vụ, Space để bắt cá, Esc hoặc P để tạm dừng, H để bật tương phản cao và M để tắt tiếng cảnh báo. Phụ đề vẫn hoạt động khi tắt tiếng. Ở Shop dùng 1 hoặc 2 để mua nâng cấp và Enter để sang Ngày tiếp theo. R chơi lại khi tạm dừng hoặc kết thúc. Có thể chạy riêng `--mode gather` hoặc `--mode quan` (quán nhận kho qua `--inventory <file>`).

Từ thư mục gốc của repo, dùng lệnh sau để kiểm tra project và tải scene với Godot trên PATH.

```bash
godot --headless --path godot --quit-after 5
```

Không có server thì client chỉ hiển thị cảnh xem trước. Logic và dữ liệu chơi nằm ở server Python; client đọc snapshot và gửi đầu vào.

```bash
PYTHONPATH=tests:. python3 -m unittest discover -s tests -v
python3 -m chonoi.headless --mode gather --seed 1 --ticks 600 --out out.jsonl
python3 -m chonoi.soak --seed 7 --days 10 --out soak.json
bash tools/bench.sh --seed 42 --duration 30 --out bench.json
```

Benchmark cần cửa sổ đồ họa và Godot trên PATH (hoặc đặt `GODOT_BIN`). Manifest khai Test Contract v1.3; kho dùng mảng cá thể `{id, kind, fresh}` từ v1.2, không đọc kho đếm của v1.1. Kết quả benchmark & soak đã được kiểm chứng thực tế trên GPU (`docs/proof/phase-4/bench-godot-4.7.2.json`, `docs/proof/phase-4/bench.json`, `docs/proof/phase-4/soak-v13.json`) cùng toàn bộ **148/148 bài test PASS** (`docs/verification/phase-4.md`).

## Sáng tạo của nhóm (`AnhChang3Chan`)

Nhóm giữ nguyên 100% lõi mô phỏng Python tất định (`chonoi/`) tương thích Test Contract `v1.3` cho chấm tự động headless, đồng thời mở rộng các điểm sáng tạo sau:
- **Lớp trình diễn Godot 3D bối cảnh Tây Nam Bộ (`godot/`):** Cảnh lặn 2.5D (`DiveUnderwater`) có nước shader, đàn cá bơi, cụm bông súng nở, thủy quái tuần tra/truy đuổi và quán bè nổi 3D (`FloatingShop`) với nhân vật có hoạt ảnh đi/ngồi, đèn lồng, tín hiệu bếp/khách 3D và xử lý va chạm hiển thị không xuyên bàn/bếp.
- **Mở rộng Phase 2:** Cháy món (`burn`) khi để món chín quá lâu trên bếp và Rắn Hổ Mây (`snake`, M3) truy đuổi dưới nước. Có bộ test trong `tests/test_p2_v11_suite.py`.
- **Cảnh báo HUD cấu hình bằng dữ liệu & Khả năng tiếp cận:** Ngưỡng cảnh báo thủy quái gần (`detect_radius`), oxy thấp, khách sắp giận nằm trong `tuning.hud_alerts` gửi qua `meta.alerts` của `chonoi.live` (không ảnh hưởng JSONL headless), kèm chế độ **Tương phản cao** (phím `H`).
- **Bộ công cụ QA tự động hóa (`tools/qa_stability_suite.py`):** Kiểm thử Fuzz + Invariant, so sánh SHA-256 từng byte cho Determinism và kiểm tải 100 request liên tục lên server `chonoi.live`.

## Mở rộng Phase 3

- **Dòng nước lũ (`current`)** báo trước 2 giây, hoạt động 8 giây mỗi 30 giây. Từ độ sâu 10 m, dòng đẩy Út Sen ngang 1,5 m/s. HUD hiện hướng dòng và báo trước bằng chữ, biểu tượng, âm thanh.
- **Khách đặt trước (`reservations`)** công bố hai đơn mỗi Ngày. HUD báo bàn, món và thời điểm khách đến tính từ lúc mở quán. Đơn giao thành công nhân giá đã chốt theo độ tươi với 1,5 trước khi tính boa.

```bash
PYTHONPATH=tests:. python3 -m unittest test_gather_current test_reservations -v
```

## Mở rộng Phase 4

- **Bảng xếp hạng (`leaderboard`)** lưu 10 kết quả cao nhất của các lượt chuẩn hoàn tất 5 Ngày. `bash tools/play.sh --player-name "Út Sen"` đặt tên cho lượt chơi. Xuất bằng `bash tools/play.sh --export-leaderboard top.json` và thêm `--leaderboard store.json` nếu dùng file riêng. Headless mode day nhận cặp `--leaderboard store.json --player-name "Út Sen"`.
- **Phụ đề hiệu ứng âm thanh** hiện khi thủy quái đến gần, oxy thấp, khách sắp giận hoặc dòng lũ sắp tới. Thử bằng phím H và M để bật tương phản cao và tắt tiếng.

Xem cách chạy test và kết quả tại [kiểm chứng Phase 4](docs/verification/phase-4.md).

## Tự do sáng tạo

Ngoài phần đề yêu cầu, nhóm được **thêm** nhân vật, loài cá/cây, sinh vật, món, bản đồ, cơ chế, câu chuyện, đồ họa, âm nhạc… với ba điều kiện: **không phá phần cố định** (tắt ở headless), ghi mục **"Sáng tạo của nhóm"** trong README của nhóm, và **làm lõi đúng trước**.

## Lịch 3 giờ

| Mốc | Phase | Hạn tag |
|---|---|---|
| 0:00 | Phase 1 (PRD-0) | `phase-1` trước 1:00 |
| 1:00 | Phase 2 | `phase-2` trước 1:55 |
| 1:55 | Phase 3 | `phase-3` trước 2:30 |
| 2:30 | Phase 4 | `phase-4` + Release `v1.0.0` trước 3:00 |

Hết giờ mỗi phase thì gắn tag rồi đi tiếp; chỗ chưa xong ghi trung thực trong bằng chứng.

## Đánh giá (100 điểm)

| Hạng mục | Điểm |
|---|---|
| Test tự động ẩn (headless, gồm kiểm tra lại phase trước) | 25 |
| Làm việc nhóm (một repo chung, chia việc, tích hợp, đổi yêu cầu) | 25 |
| Kiểm chứng & bằng chứng | 15 |
| Harness AI (AGENTS.md, skill, nhật ký dùng AI) | 10 |
| Đánh giá & retro | 10 |
| Chất lượng sản phẩm (đúng yêu cầu, mở rộng/sáng tạo) | 10 |
| Demo | 5 |

## Quy định

- Dùng AI thoải mái; **không sao chép repo của nhóm khác**; bằng chứng phải thật.
- Nhân vật, bối cảnh là bản gốc của lab; asset ngoài chỉ dùng CC0/CC-BY/MIT hoặc tự tạo, ghi nguồn trong `CREDITS.md`. Không commit API key, token, `.env`.
