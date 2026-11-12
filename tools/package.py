#!/usr/bin/env python3
"""Pack the mod into the files Horizon loads.

    python3 tools/package.py

Writes into dist/:
  useful_armory-<version>.hmod        the content mod (content/), for horizon-mods/

The content package is a deterministic zip in the layout Horizon's docs/api/mod-files.md describes.
"""
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


if __name__ == "__main__":
    DIST.mkdir(exist_ok=True)
    content_mod()


