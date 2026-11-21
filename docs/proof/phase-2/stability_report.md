# Báo Cáo Kiểm Thử Ổn Định & Hiệu Năng (QA Stability Suite)

- **Thời điểm chạy:** 2026-11-21 11:46:59
- **Môi trường:** Windows 11 · Python 3.13.3
- **Cấu hình Fuzz:** 4 seeds x 2 modes (`gather`, `quan`) x 1200 ticks/run

## 1. Fuzz / Monkey Testing & Invariant Checking
**Kết quả:** `8/8` kịch bản đạt (không crash, 0 vi phạm bất biến).

| Mode | Seed | Trạng thái | Thời gian (ms) | Ghi chú / Vi phạm |
|---|---:|---|---:|---|
| `gather` | 1 | PASS | 73.1 | OK (0 vi phạm) |
| `gather` | 2 | PASS | 72.0 | OK (0 vi phạm) |
| `gather` | 3 | PASS | 76.3 | OK (0 vi phạm) |
| `gather` | 4 | PASS | 77.4 | OK (0 vi phạm) |
| `quan` | 1 | PASS | 97.2 | OK (0 vi phạm) |
| `quan` | 2 | PASS | 87.3 | OK (0 vi phạm) |
| `quan` | 3 | PASS | 89.1 | OK (0 vi phạm) |
| `quan` | 4 | PASS | 89.7 | OK (0 vi phạm) |

## 2. Determinism (So khớp SHA-256 Từng Byte)
**Kết quả:** `2/2` đạt.

| Mode | Trạng thái | Run 1 (SHA-256) | Run 2 (SHA-256) | Kết luận |
|---|---|---|---|---|
| `gather` | PASS | `7f4cab0712d5af4a` | `7f4cab0712d5af4a` | OK |
| `quan` | PASS | `b94d1728ede7ea77` | `b94d1728ede7ea77` | OK |

## 3. Performance & Memory Soak (Full Ca 180s = 10,800 ticks)

| Mode | Ticks đã chạy | Thời gian (ms) | Tốc độ (ticks/s) | Peak RAM (KB) | Lý do dừng |
|---|---:|---:|---:|---:|---|
| `gather` | 117 | 15.1 | 7756 | 41.4 | `docked` |
| `quan` | 10800 | 388.8 | 27778 | 112.3 | `time` |

## 4. Live HTTP Server Bridge Stress (`chonoi.live`)
- **Trạng thái:** `PASS`
- **GET /state:** `80/80` (200 OK)
- **POST /input:** `20/20` (200 OK)
- **Tắt sạch thread (`server.stop()`):** `True` (tổng thời gian `1400.5 ms`)
