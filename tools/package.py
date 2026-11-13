#!/usr/bin/env python3
"""Pack the mod into the files Horizon loads.

    python3 tools/package.py

Writes into dist/:
  useful_armory-<version>.hmod        the content mod (content/), for horizon-mods/
  useful_armory_native-<version>.hnmod   the native half (native/useful_armory/): the glow, set
                                      bonuses, tool abilities and weapon effects, for
                                      horizon-native-mods/

Both are deterministic zips in the layout Horizon's docs/api/mod-files.md describes. The native
half has its own id, useful_armory_native: the registry lists each file under one id.
"""
import hashlib
import json
import tomllib
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"


def write_zip(out, files):
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, content in sorted(files.items()):
            info = zipfile.ZipInfo(name, (2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, content)
    print(f"{out.relative_to(ROOT)}  ({len(files)} files, {out.stat().st_size} bytes)")


def content_mod():
    root = ROOT / "content"
    manifest = tomllib.loads((root / "horizon-mod.toml").read_text())
    files = {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*") if p.is_file()}
    write_zip(DIST / f"{manifest['id']}-{manifest['version']}.hmod", files)


def native_mod():
    root = ROOT / "native" / "useful_armory"
    compat = json.loads((root / "compatibility.json").read_text())
    bundle = next(p for p in (root / "mixins").iterdir() if (p / "horizon-mixin.toml").is_file())
    mixin = tomllib.loads((bundle / "horizon-mixin.toml").read_text())
    mod_id, version = mixin["mod"]["id"], mixin["mod"]["version"]
    if mixin["compatibility"]["horizon_revision"] != compat["horizon_revision"]:
        raise SystemExit("horizon-mixin.toml and compatibility.json pin different Horizon commits")
    manifest = {"schema": 1, "id": mod_id, "version": version, "game": compat["game"],
                "horizon": compat["horizon_revision"], "mixins": compat["horizon_mixins_revision"]}
    files = {"horizon-native.json": (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode()}
    # The bundle's sources and, under api/, the package that registers with Armory Lib.
    for path in sorted(bundle.rglob("*")):
        if path.is_file() and path.suffix in (".rs", ".toml") and "target" not in path.parts:
            files[f"mixins/{mod_id}/{path.relative_to(bundle).as_posix()}"] = path.read_bytes()
    write_zip(DIST / f"{mod_id}-{version}.hnmod", files)


if __name__ == "__main__":
    DIST.mkdir(exist_ok=True)
    content_mod()
    native_mod()
    packages = sorted(p for p in DIST.iterdir() if p.suffix in (".hmod", ".hnmod"))
    (DIST / "SHA256SUMS.txt").write_text(
        "".join(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}\n" for p in packages))


