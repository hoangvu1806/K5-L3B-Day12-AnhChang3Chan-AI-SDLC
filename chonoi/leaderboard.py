"""Top 10 địa phương; thứ tự ghi là tiêu chí phụ khi bằng điểm."""

import json
import os
import tempfile
from pathlib import Path

from .errors import BadInput
from .runner import score_of

LIMIT = 10
STANDARD_DAYS = 5


def default_store():
    data = Path(os.environ.get("LOCALAPPDATA" if os.name == "nt" else "XDG_DATA_HOME")
                or Path.home() / ".local/share")
    return data / "chonoi" / "leaderboard.json"


def player_name(value):
    if not value.strip():
        raise BadInput("tên người chơi phải là chuỗi khác rỗng")
    return value.strip()


def read_entries(path):
    try:
        with Path(path).open(encoding="utf-8") as stream:
            data = json.load(stream)
    except FileNotFoundError:
        return []
    except ValueError as error:
        raise BadInput(f"file bảng xếp hạng sai JSON: {error}") from error
    if not isinstance(data, dict) or set(data) != {"entries"} or not isinstance(data["entries"], list):
        raise BadInput("file bảng xếp hạng phải có mảng entries")
    for entry in data["entries"]:
        if (not isinstance(entry, dict) or set(entry) != {"name", "score", "days_completed", "seed"}
                or not isinstance(entry["name"], str) or not entry["name"].strip()
                or type(entry["score"]) is not int or type(entry["seed"]) is not int
                or type(entry["days_completed"]) is not int or entry["days_completed"] != STANDARD_DAYS):
            raise BadInput("mục bảng xếp hạng phải có name, score, days_completed và seed hợp lệ")
    return sorted(data["entries"], key=lambda entry: -entry["score"])[:LIMIT]


def _write_entries(path, entries):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as stream:
        temp = Path(stream.name)
        try:
            json.dump({"entries": entries}, stream, ensure_ascii=False, separators=(",", ":"))
            stream.write("\n")
            stream.close()
            temp.replace(path)
        finally:
            temp.unlink(missing_ok=True)


def export_entries(store, out):
    if Path(store).resolve() == Path(out).resolve():
        raise BadInput("đường dẫn xuất phải khác file bảng xếp hạng")
    _write_entries(out, read_entries(store))


def record_completed(store, name, seed, sim, tuning):
    if sim.mode != "day" or sim.reason != "days_complete" or sim.days_completed != STANDARD_DAYS:
        return
    # Atomic replacement protects readers. Lock the whole read/update so two
    # finished sessions sharing a store cannot overwrite each other's entry.
    store = Path(store).resolve()
    store.parent.mkdir(parents=True, exist_ok=True)
    with store.with_name(store.name + ".lock").open("a+b") as lock:
        if os.name == "nt":
            from msvcrt import LK_LOCK, locking
            lock.seek(0)
            locking(lock.fileno(), LK_LOCK, 1)
        else:
            from fcntl import LOCK_EX, flock
            flock(lock.fileno(), LOCK_EX)
        entries = read_entries(store)
        entries.append({"name": name, "score": score_of(sim, tuning), "days_completed": STANDARD_DAYS, "seed": seed})
        entries.sort(key=lambda entry: -entry["score"])
        _write_entries(store, entries[:LIMIT])
