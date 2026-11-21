"""File kho (Contract G). Bên đọc chọn schema theo `contract_version`:

- v1.0 / v1.1 — kho đếm:     {"items": {kind: số nguyên >= 0}}
- v1.2+      — kho cá thể:   {"items": [{"id": "I1", "kind": "ca_linh", "fresh": 100}, ...]}
  id chuỗi duy nhất khác rỗng, kind thuộc danh mục, fresh hữu hạn trong [0, 100]. Kho rỗng {"items": []}.
  v1.2 gặp file kho đếm / sai schema -> mã 2.

Ghi: qua file tạm cùng thư mục rồi thay thế (nguyên tử), byte-ổn-định. Kho cá thể ghi theo id, fresh giữ
đủ độ chính xác (không làm tròn như JSONL) để đọc lại vẫn giữ giá trị và nhánh ở ngưỡng 30.

Adapter cho các lát: `items_from_counts`, `counts_of`, `is_item_schema`, `uses_item_schema(version)`.
"""

import json
import math
import os
import tempfile

from .ids import sort_by_id

from .errors import BadInput

KINDS_P1 = ("ca_loc", "ca_linh", "ca_keo", "bong_dien_dien", "bong_sung", "keo_neo")
KINDS_V11 = KINDS_P1


def validate_items(items, kinds=KINDS_P1):
    if not isinstance(items, dict):
        raise BadInput("items phải là object")
    out = {}
    for k, v in items.items():
        if k not in kinds:
            raise BadInput(f"nguyên liệu lạ: {k}")
        if isinstance(v, bool) or not isinstance(v, int) or v < 0:
            raise BadInput(f"số lượng không hợp lệ cho {k}: {v!r}")
        if v > 0:
            out[k] = v
    return out


def uses_item_schema(version) -> bool:
    """True nếu contract_version >= 1.2 (kho cá thể)."""
    try:
        major, minor = (int(x) for x in str(version).split(".")[:2])
    except ValueError:
        return False
    return (major, minor) >= (1, 2)


def is_item_schema(items) -> bool:
    return isinstance(items, list)


def validate_item_list(items, kinds=KINDS_P1, name="items") -> list:
    """Kiểm mảng cá thể v1.2; trả bản sao (giữ thứ tự)."""
    if not isinstance(items, list):
        raise BadInput(f"{name} phải là mảng cá thể {{id, kind, fresh}} (contract v1.2)")
    seen, out = set(), []
    for i, it in enumerate(items):
        if not isinstance(it, dict) or set(it) != {"id", "kind", "fresh"}:
            raise BadInput(f"{name}[{i}] phải có đúng các khóa id, kind, fresh")
        iid, kind, fresh = it["id"], it["kind"], it["fresh"]
        if not isinstance(iid, str) or not iid:
            raise BadInput(f"{name}[{i}].id phải là chuỗi khác rỗng")
        if iid in seen:
            raise BadInput(f"{name}: id trùng {iid}")
        seen.add(iid)
        if kind not in kinds:
            raise BadInput(f"{name}[{i}]: nguyên liệu lạ {kind!r}")
        if isinstance(fresh, bool) or not isinstance(fresh, (int, float)) or not math.isfinite(fresh)                 or not 0 <= fresh <= 100:
            raise BadInput(f"{name}[{i}].fresh phải là số hữu hạn trong [0, 100]")
        out.append({"id": iid, "kind": kind, "fresh": fresh})
    return out


def items_from_counts(counts: dict, ids, fresh=100) -> list:
    """Adapter kho đếm -> kho cá thể (theo id nguyên liệu, id mới từ IdAllocator họ 'I')."""
    return [{"id": ids.new("I"), "kind": k, "fresh": fresh} for k in sorted(counts) for _ in range(counts[k])]


def counts_of(items) -> dict:
    """Kho cá thể (hoặc mảng kind) -> object đếm, sắp theo id nguyên liệu."""
    if isinstance(items, dict):
        return {k: items[k] for k in sorted(items) if items[k] > 0}
    return hold_to_items(items)


def read_inventory(path: str, kinds=KINDS_P1, version="1.1"):
    """Đọc file kho theo schema của `version` (kho đếm dict hoặc kho cá thể list)."""
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        raise BadInput(f"không đọc được file kho {path}: {e}")
    if not isinstance(data, dict) or set(data.keys()) != {"items"}:
        raise BadInput("file kho chỉ được có khóa gốc 'items'")
    if uses_item_schema(version):
        return validate_item_list(data["items"], kinds)
    return validate_items(data["items"], kinds)


def hold_to_items(hold: list) -> dict:
    """Khoang (mảng id theo thứ tự nhặt) -> object đếm, sắp theo id nguyên liệu."""
    counts = {}
    for k in hold:
        kind = k["kind"] if isinstance(k, dict) else k
        counts[kind] = counts.get(kind, 0) + 1
    return {k: counts[k] for k in sorted(counts)}


def write_inventory(path: str, items):
    """Ghi kho đếm (dict) hoặc kho cá thể (list, sắp theo id), nguyên tử."""
    if is_item_schema(items):
        items = [{"id": it["id"], "kind": it["kind"], "fresh": it["fresh"]} for it in sort_by_id(items)]
    else:
        items = {k: items[k] for k in sorted(items) if items[k] > 0}
    d = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(prefix=".inv-", suffix=".tmp", dir=d)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            json.dump({"items": items}, f, ensure_ascii=False, separators=(",", ":"))
            f.write("\n")
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise
