# Báo Cáo Kiểm Thử Ổn Định & Hiệu Năng (QA Stability Suite)

- **Thời điểm chạy:** 2026-11-22 00:05:58
- **Môi trường:** Windows 11 · Python 3.13.3
- **Cấu hình Fuzz:** 4 seeds x 2 modes (`gather`, `quan`) x 1200 ticks/run

## 1. Fuzz / Monkey Testing & Invariant Checking
**Kết quả:** `8/8` kịch bản đạt (không crash, 0 vi phạm bất biến).

| Mode | Seed | Trạng thái | Thời gian (ms) | Ghi chú / Vi phạm |
|---|---:|---|---:|---|
| `gather` | 1 | PASS | 268.1 | OK (0 vi phạm) |
| `gather` | 2 | PASS | 262.8 | OK (0 vi phạm) |
| `gather` | 3 | PASS | 268.6 | OK (0 vi phạm) |
| `gather` | 4 | PASS | 214.3 | OK (0 vi phạm) |
| `quan` | 1 | PASS | 792.6 | OK (0 vi phạm) |
| `quan` | 2 | PASS | 601.6 | OK (0 vi phạm) |
| `quan` | 3 | PASS | 504.9 | OK (0 vi phạm) |
| `quan` | 4 | PASS | 553.8 | OK (0 vi phạm) |

## 2. Determinism (So khớp SHA-256 Từng Byte)
**Kết quả:** `2/2` đạt.

| Mode | Trạng thái | Run 1 (SHA-256) | Run 2 (SHA-256) | Kết luận |
|---|---|---|---|---|
| `gather` | PASS | `b66001ff8242c885` | `b66001ff8242c885` | OK |
| `quan` | PASS | `1f7e764d7765ba96` | `1f7e764d7765ba96` | OK |

## 3. Performance & Memory Soak (Full Ca 180s = 10,800 ticks)

| Mode | Ticks đã chạy | Thời gian (ms) | Tốc độ (ticks/s) | Peak RAM (KB) | Lý do dừng |
|---|---:|---:|---:|---:|---|
| `gather` | 117 | 27.1 | 4316 | 44.8 | `docked` |
| `quan` | 10800 | 14515.4 | 744 | 124.8 | `time` |

## 4. Live HTTP Server Bridge Stress (`chonoi.live`)
- **Trạng thái:** `PASS`
- **GET /state:** `80/80` (200 OK)
- **POST /input:** `20/20` (200 OK)
- **Tắt sạch thread (`server.stop()`):** `True` (tổng thời gian `1223.9 ms`)
