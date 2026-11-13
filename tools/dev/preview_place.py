#!/usr/bin/env python3
"""Build, validate and render ONE place without touching content/.

    python3 -I tools/dev/preview_place.py <module> --out DIR [--schema block_schema.json] [--layers 1,5,9]

<module> is a module name in tools/structures (for example ruined_forge). For each of its
pieces this prints stats and validation problems and writes DIR/<piece>.png (isometric views,
cutaway and floor plans). Exit status 1 if anything fails validation. Use this while working
on a building; tools/gen_phase1.py is the full build and rewrites content/.
"""
import argparse
import importlib
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import structkit  # noqa: E402
import render_nbt  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("module")
    ap.add_argument("--out", required=True)
    ap.add_argument("--schema")
    ap.add_argument("--layers")
    ap.add_argument("--width", type=int, default=1800)
    args = ap.parse_args()
    module = importlib.import_module(f"structures.{args.module}")
    places = module.PLACE if isinstance(module.PLACE, list) else [module.PLACE]
    schema = structkit.load_schema(args.schema) if args.schema else None
    layers = [int(v) for v in args.layers.split(",")] if args.layers else None
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    bad = 0
    for place in places:
        for name, build in place["pieces"].items():
            piece = build()
            piece.finalize()
            print(piece.stats())
            if piece.name != name:
                print(f"  PROBLEM: Piece.name {piece.name!r} differs from its key {name!r}")
                bad += 1
            if schema:
                for problem in piece.validate(schema):
                    print("  PROBLEM:", problem)
                    bad += 1
            target = out / (name.replace("/", "__") + ".png")
            render_nbt.sheet(piece, max_width=args.width, layers=layers).save(target)
            print("  wrote", target)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
