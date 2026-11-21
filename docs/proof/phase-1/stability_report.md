# Báo Cáo Kiểm Thử Ổn Định & Hiệu Năng (QA Stability Suite)

- **Thời điểm chạy:** 2026-11-21 10:33:58
- **Môi trường:** Windows 11 · Python 3.13.3
- **Cấu hình Fuzz:** 5 seeds x 2 modes (`gather`, `quan`) x 1800 ticks/run

## 1. Fuzz / Monkey Testing & Invariant Checking
**Kết quả:** `10/10` kịch bản đạt (không crash, 0 vi phạm bất biến).

| Mode | Seed | Trạng thái | Thời gian (ms) | Ghi chú / Vi phạm |
|---|---:|---|---:|---|
| `gather` | 1 | PASS | 76.1 | OK (0 vi phạm) |
| `gather` | 2 | PASS | 77.8 | OK (0 vi phạm) |
| `gather` | 3 | PASS | 73.0 | OK (0 vi phạm) |
| `gather` | 4 | PASS | 73.3 | OK (0 vi phạm) |
| `gather` | 5 | PASS | 70.3 | OK (0 vi phạm) |
| `quan` | 1 | PASS | 101.3 | OK (0 vi phạm) |
| `quan` | 2 | PASS | 82.5 | OK (0 vi phạm) |
| `quan` | 3 | PASS | 82.4 | OK (0 vi phạm) |
| `quan` | 4 | PASS | 83.7 | OK (0 vi phạm) |
| `quan` | 5 | PASS | 85.5 | OK (0 vi phạm) |

## 2. Determinism (So khớp SHA-256 Từng Byte)
**Kết quả:** `2/2` đạt.

| Mode | Trạng thái | Run 1 (SHA-256) | Run 2 (SHA-256) | Kết luận |
|---|---|---|---|---|
| `gather` | PASS | `4f7a355fa6e585bf` | `4f7a355fa6e585bf` | OK |
| `quan` | PASS | `8fb439e3aac982a3` | `8fb439e3aac982a3` | OK |

## 3. Performance & Memory Soak (Full Ca 180s = 10,800 ticks)

| Mode | Ticks đã chạy | Thời gian (ms) | Tốc độ (ticks/s) | Peak RAM (KB) | Lý do dừng |
|---|---:|---:|---:|---:|---|
| `gather` | 117 | 3.1 | 37998 | 31.7 | `docked` |
| `quan` | 10800 | 244.9 | 44096 | 120.4 | `time` |

## 4. Live HTTP Server Bridge Stress (`chonoi.live`)
- **Trạng thái:** `PASS`
- **GET /state:** `80/80` (200 OK)
- **POST /input:** `20/20` (200 OK)
- **Tắt sạch thread (`server.stop()`):** `True` (tổng thời gian `1282.2 ms`)
