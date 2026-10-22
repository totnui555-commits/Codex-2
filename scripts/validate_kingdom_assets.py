"""Validate original GLB packs without Blender, GPU or third-party services."""

import hashlib
import json
import struct
from pathlib import Path

REQUIRED = {
    "keep",
    "guild",
    "workshop",
    "atelier",
    "alchemy",
    "market",
    "treasury",
    "lighthouse",
    "library",
    "post",
    "shipyard",
    "commons",
}
ROOT = Path(__file__).resolve().parents[1]


def validate():
    result = {}
    for name in ("island", "island-balanced", "island-low", "citizen"):
        path = ROOT / "apps/web/public/kingdom" / (name + ".glb")
        raw = path.read_bytes()
        magic, version, length = struct.unpack("<III", raw[:12])
        assert magic == 0x46546C67 and version == 2 and length == len(raw)
        json_length, kind = struct.unpack("<II", raw[12:20])
        assert kind == 0x4E4F534A
        data = json.loads(raw[20 : 20 + json_length])
        assert not any(b.get("uri") for b in data.get("buffers", []))
        assert not data.get("images"), "Current pack must be self-contained original materials"
        triangles = sum(
            data["accessors"][p["indices"]]["count"] // 3 for m in data["meshes"] for p in m["primitives"]
        )
        if name.startswith("island"):
            ids = {n.get("extras", {}).get("landmark_id") for n in data["nodes"]}
            assert REQUIRED <= ids
        else:
            assert {"Tunic", "Face", "Hat", "LegLeft", "LegRight", "ArmLeft", "ArmRight"} <= {
                n["name"] for n in data["nodes"]
            }
        assert 0 < len(raw) < 12_000_000 and triangles > 1000
        result[name] = {
            "sha256": hashlib.sha256(raw).hexdigest(),
            "bytes": len(raw),
            "meshes": len(data["meshes"]),
            "triangles": triangles,
        }
    assert (
        result["island-low"]["triangles"]
        < result["island-balanced"]["triangles"]
        < result["island"]["triangles"]
        < 300000
    )
    return {
        "world_version": "kingdom-2.0.0",
        "original_assets": True,
        "landmarks_verified": len(REQUIRED),
        "packs": result,
        "external_asset_dependencies": 0,
    }


if __name__ == "__main__":
    print(json.dumps(validate(), indent=2))
