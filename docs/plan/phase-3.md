# Kế hoạch Phase 3 — TICKET-03 "Mùa Nước Nổi" (Test Contract v1.2)

> 35 phút (1:55–2:30). Tag `phase-3` trên `main` trước 2:30. Nhóm 6 người → **≥ 2 mở rộng**.

## Tác động (breaking change: kho đếm → kho cá thể `{id, kind, fresh}`)
| Module | File cần đổi | Test bị ảnh hưởng | Người phụ trách |
|---|---|---|---|
| Schema / adapter kho | `chonoi/inventory.py`, `chonoi/scenario.py`, `chonoi/contract.py`, `game.contract.json` (`1.2`, `freshness`) | Test đọc/ghi file kho (đổi sang mảng cá thể); thêm test kho đếm → mã 2 | **Hoàng Vũ** (`hoangvu1806`) + Nhật Nguyên duyệt |
| Lặn | `chonoi/sim/gather.py` | Giỏ LIFO, `monster_hit.lost`, `faint.lost` (thành mảng cá thể); thêm test hao 0.5/s, `spoiled` ở ngưỡng 30 | Nguyễn An (hao tươi, `spoiled`, cấp id `I1…`) · Từ Huy Bảo (LIFO khi mất hàng, ghi kho khi `gather_end`) |
| Quán | `chonoi/sim/quan.py` | Giữ chỗ (lượng → id), giá cố định → giá theo tươi; thêm test giữ lại khi vừa ươn, chốt `base_price` | Hoàng Vũ (giữ chỗ theo id, nhả và giữ lại khi ươn, `unfulfillable`) · Hà Anh (hao 0.25/s kho quán, `cook_started.items`, `base_price`, boa) |
| day | `chonoi/sim/day.py` | Bàn giao trong bộ nhớ giữ id/fresh, không hao thêm ở tick chuyển pha | Hoàng Vũ |
| HUD | `godot/` | — (bằng chứng ảnh chụp) | Trần Gia Bảo — hiện độ tươi/nhãn "ươn" ở giỏ và kho |
| QA | `tests/`, `CHANGELOG.md`, `docs/proof/phase-3/`, `docs/verification/phase-3.md` | Regression P1–P2 còn hiệu lực; smoke ngưỡng (`fresh:30` → `spoiled` tick 1); smoke bàn giao file | Nhật Nguyên |

## Thứ tự tích hợp (giữ `main` chạy được)
1. Phút 0–7: chốt schema, tách nhánh `feat/p3-*` từ `dev`.
2. Vũ làm adapter trước (đọc/ghi mảng cá thể, chọn schema theo `contract_version`) + fixture mới; push sớm để Lặn/Quán dùng.
3. Lặn và Quán làm song song trên adapter; HUD theo schema snapshot.
4. Phút 20: smoke bàn giao kho (gather `fresh:100` + `interact` frame 0 → `quan --inventory --ticks 0`), standup.
5. Phút 25–32: bật `1.2`, smoke file + `day`, regression, `CHANGELOG.md`, verification; merge `dev` → `main`, Vũ gắn tag `phase-3`.

## Mở rộng (chọn 2)
| Mở rộng | Người | Lý do |
|---|---|---|
| `current` (Dòng nước lũ) | Nguyễn An | Chỉ cộng lực vào bơi của người chơi, nằm gọn trong gather |
| `reservations` (Khách đặt trước) | Hà Anh + Hoàng Vũ | Nối tiếp luật khách/bếp đã làm |

## Rủi ro
- Ngưỡng 30 và `floor` sai do số thực → dùng đơn vị nguyên (240 đơn vị/điểm tươi: gather −2/tick, quán −1/tick).
- Đổi schema làm vỡ test P1–P2 → sửa test kèm lý do trong commit và `CHANGELOG.md`.
