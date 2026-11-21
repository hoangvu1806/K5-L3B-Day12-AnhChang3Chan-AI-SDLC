#!/usr/bin/env python3
"""Bỏ nén KHR_mesh_quantization trong file GLB để Godot import được (chỉ thư viện chuẩn).

python tools/dequantize_glb.py assets            # sửa tại chỗ mọi .glb trong thư mục
POSITION/NORMAL/TANGENT/TEXCOORD_n dạng số nguyên -> float32; transform node giữ nguyên.
"""
import json
import struct
import sys
from pathlib import Path

EXT = "KHR_mesh_quantization"
COMP = {5120: ("b", 1, 127.0), 5121: ("B", 1, 255.0), 5122: ("h", 2, 32767.0), 5123: ("H", 2, 65535.0)}
NCOMP = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}
ATTRS = ("POSITION", "NORMAL", "TANGENT", "TEXCOORD_")


def _pad(b: bytes, fill=b"\0") -> bytes:
    return b + fill * (-len(b) % 4)


def convert(path: Path) -> bool:
    raw = path.read_bytes()
    if raw[:4] != b"glTF":
        return False
    jlen = struct.unpack_from("<I", raw, 12)[0]
    gltf = json.loads(raw[20:20 + jlen])
    if EXT not in gltf.get("extensionsRequired", []) + gltf.get("extensionsUsed", []):
        return False
    if "EXT_meshopt_compression" in gltf.get("extensionsUsed", []):
        raise ValueError("EXT_meshopt_compression chưa hỗ trợ")
    off = 20 + jlen
    blen = struct.unpack_from("<I", raw, off)[0]
    binbuf = bytearray(raw[off + 8:off + 8 + blen])

    targets = set()
    for mesh in gltf.get("meshes", []):
        for prim in mesh.get("primitives", []):
            for group in [prim.get("attributes", {})] + prim.get("targets", []):
                for name, idx in group.items():
                    if name.startswith(ATTRS):
                        targets.add(idx)

    for idx in sorted(targets):
        acc = gltf["accessors"][idx]
        if acc["componentType"] not in COMP or "bufferView" not in acc:
            continue
        fmt, size, scale = COMP[acc["componentType"]]
        norm = acc.get("normalized", False)
        n = NCOMP[acc["type"]]
        bv = gltf["bufferViews"][acc["bufferView"]]
        stride = bv.get("byteStride", size * n)
        base = bv.get("byteOffset", 0) + acc.get("byteOffset", 0)
        out = bytearray()
        for i in range(acc["count"]):
            vals = struct.unpack_from("<" + fmt * n, binbuf, base + i * stride)
            if norm:
                vals = [max(v / scale, -1.0) for v in vals]
            out += struct.pack("<" + "f" * n, *vals)
        start = len(binbuf)
        binbuf += _pad(bytes(out))
        gltf["bufferViews"].append({"buffer": 0, "byteOffset": start, "byteLength": len(out)})
        acc.update(bufferView=len(gltf["bufferViews"]) - 1, componentType=5126, byteOffset=0)
        acc.pop("normalized", None)
        for k in ("min", "max"):
            if k in acc and norm:
                acc[k] = [max(v / scale, -1.0) for v in acc[k]]

    for key in ("extensionsRequired", "extensionsUsed"):
        if key in gltf:
            gltf[key] = [e for e in gltf[key] if e != EXT]
            if not gltf[key]:
                del gltf[key]
    gltf["buffers"][0]["byteLength"] = len(binbuf)
    js = _pad(json.dumps(gltf, separators=(",", ":")).encode(), b" ")
    bb = _pad(bytes(binbuf))
    total = 12 + 8 + len(js) + 8 + len(bb)
    data = (struct.pack("<4sII", b"glTF", 2, total) + struct.pack("<I4s", len(js), b"JSON") + js
            + struct.pack("<I4s", len(bb), b"BIN\0") + bb)
    tmp = path.with_suffix(".glb.part")
    tmp.write_bytes(data)
    tmp.replace(path)
    return True


def main(root: str) -> int:
    done = skipped = 0
    for p in sorted(Path(root).rglob("*.glb")):
        try:
            if convert(p):
                done += 1
        except Exception as e:  # file có extension khác (meshopt...) thì bỏ qua, báo ra
            skipped += 1
            print("SKIP", p, e)
    print(f"dequantized {done} file, skip {skipped}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "assets"))
