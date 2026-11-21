"""Ghi JSONL tất định: làm tròn 3 chữ số khi XUẤT (tính toán dùng giá trị chính xác)."""

import json
import os
import tempfile


def _clean(v):
    if isinstance(v, float):
        r = round(v, 3)
        return 0.0 if r == 0 else r  # tránh -0.0
    if isinstance(v, dict):
        return {k: _clean(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [_clean(x) for x in v]
    return v


def dumps(obj) -> str:
    return json.dumps(_clean(obj), ensure_ascii=False, separators=(",", ":"))


class JsonlWriter:
    def __init__(self, path: str):
        self.path = path
        self._f = tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n",
                                              dir=os.path.dirname(os.path.abspath(path)), delete=False)

    def __enter__(self):
        return self

    def write(self, obj):
        self._f.write(dumps(obj) + "\n")

    def __exit__(self, exc_type, exc_value, traceback):
        try:
            self._f.close()
            if exc_type is None:
                os.replace(self._f.name, self.path)
        finally:
            if os.path.exists(self._f.name):
                os.unlink(self._f.name)
