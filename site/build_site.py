#!/usr/bin/env python3
"""Build script for the static Reel site.

Uses standard library only.
Generates:
  - site/reel.zip: zip of core/reel (without __pycache__ or *.pyc)
  - site/examples/: copy of examples/*.reel
  - site/examples.json: JSON list of example file names
"""

import json
from pathlib import Path
import shutil
import zipfile

SITE_DIR = Path(__file__).resolve().parent
ROOT_DIR = SITE_DIR.parent
CORE_REEL_DIR = ROOT_DIR / "core" / "reel"
EXAMPLES_DIR = ROOT_DIR / "examples"

ZIP_PATH = SITE_DIR / "reel.zip"
SITE_EXAMPLES_DIR = SITE_DIR / "examples"
EXAMPLES_JSON_PATH = SITE_DIR / "examples.json"


def build_reel_zip():
    """Package core/reel into site/reel.zip, omitting cache files."""
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()

    file_count = 0
    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for p in sorted(CORE_REEL_DIR.rglob("*")):
            if p.is_dir():
                continue
            # Skip python bytecode and cache folders
            if "__pycache__" in p.parts or p.suffix == ".pyc":
                continue
            arcname = "reel/" + str(p.relative_to(CORE_REEL_DIR))
            zf.write(p, arcname=arcname)
            file_count += 1

    size_kb = ZIP_PATH.stat().st_size / 1024
    print(f"✓ Created {ZIP_PATH.name} ({file_count} files, {size_kb:.1f} KB)")


def copy_examples():
    """Copy examples/*.reel to site/examples/ and generate site/examples.json."""
    if SITE_EXAMPLES_DIR.exists():
        shutil.rmtree(SITE_EXAMPLES_DIR)
    SITE_EXAMPLES_DIR.mkdir(parents=True, exist_ok=True)

    example_files = sorted(EXAMPLES_DIR.glob("*.reel"))
    example_names = []

    for src in example_files:
        shutil.copy2(src, SITE_EXAMPLES_DIR / src.name)
        example_names.append(src.name)

    EXAMPLES_JSON_PATH.write_text(
        json.dumps(example_names, indent=2) + "\n",
        encoding="utf-8"
    )

    print(f"✓ Copied {len(example_names)} examples to site/examples/")
    print(f"✓ Created {EXAMPLES_JSON_PATH.name}")


def main():
    print("Building Reel static site assets...")
    build_reel_zip()
    copy_examples()
    print("Site build complete!")


if __name__ == "__main__":
    main()
