# Báo Cáo Kiểm Thử Ổn Định & Hiệu Năng (QA Stability Suite)

- **Thời điểm chạy:** 2026-11-22 02:16:00
- **Môi trường:** Linux 5.15.167.4-microsoft-standard-WSL2 · Python 3.12.3
- **Cấu hình Fuzz:** 4 seeds x 2 modes (`gather`, `quan`) x 1200 ticks/run

## 1. Fuzz / Monkey Testing & Invariant Checking
**Kết quả:** `8/8` kịch bản đạt (không crash, 0 vi phạm bất biến).

| Mode | Seed | Trạng thái | Thời gian (ms) | Ghi chú / Vi phạm |
|---|---:|---|---:|---|
| `gather` | 1 | PASS | 42.1 | OK (0 vi phạm) |
| `gather` | 2 | PASS | 43.2 | OK (0 vi phạm) |
| `gather` | 3 | PASS | 52.5 | OK (0 vi phạm) |
| `gather` | 4 | PASS | 37.0 | OK (0 vi phạm) |
| `quan` | 1 | PASS | 201.5 | OK (0 vi phạm) |
| `quan` | 2 | PASS | 163.5 | OK (0 vi phạm) |
| `quan` | 3 | PASS | 205.4 | OK (0 vi phạm) |
| `quan` | 4 | PASS | 176.4 | OK (0 vi phạm) |

## 2. Determinism (So khớp SHA-256 Từng Byte)
**Kết quả:** `2/2` đạt.

| Mode | Trạng thái | Run 1 (SHA-256) | Run 2 (SHA-256) | Kết luận |
|---|---|---|---|---|
| `gather` | PASS | `8ec39aaa9d9428ef` | `8ec39aaa9d9428ef` | OK |
| `quan` | PASS | `be787a28d5cd75af` | `be787a28d5cd75af` | OK |

## 3. Performance & Memory Soak (Full Ca 180s = 10,800 ticks)

| Mode | Ticks đã chạy | Thời gian (ms) | Tốc độ (ticks/s) | Peak RAM (KB) | Lý do dừng |
|---|---:|---:|---:|---:|---|
| `gather` | 117 | 36.6 | 3195 | 35.1 | `docked` |
| `quan` | 10800 | 3528.8 | 3061 | 127.9 | `time` |

## 4. Live HTTP Server Bridge Stress (`chonoi.live`)
- **Trạng thái:** `PASS`
- **GET /state:** `80/80` (200 OK)
- **POST /input:** `20/20` (200 OK)
- **Tắt sạch thread (`server.stop()`):** `True` (tổng thời gian `623.6 ms`)
