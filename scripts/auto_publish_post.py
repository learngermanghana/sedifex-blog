#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
QUEUE_DIR = ROOT / "_scheduled_posts"
POSTS_DIR = ROOT / "_posts"


def slug_from_name(path: Path) -> str:
    name = path.stem.lower().strip()
    return "-".join(part for part in name.replace("_", "-").split("-") if part)


def main() -> int:
    parser = argparse.ArgumentParser(description="Publish one scheduled blog post")
    parser.add_argument("--dry-run", action="store_true", help="Show actions without moving files")
    args = parser.parse_args()

    if not QUEUE_DIR.exists():
        print(f"Queue directory not found: {QUEUE_DIR}")
        return 0

    queue_files = sorted([p for p in QUEUE_DIR.glob("*.md") if p.is_file()])
    if not queue_files:
        print("No scheduled posts found.")
        return 0

    next_post = queue_files[0]
    today = date.today().isoformat()
    slug = slug_from_name(next_post)
    destination = POSTS_DIR / f"{today}-{slug}.md"

    if destination.exists():
        print(f"Destination already exists: {destination}")
        return 1

    print(f"Publishing: {next_post.name} -> {destination.relative_to(ROOT)}")
    if args.dry_run:
        return 0

    POSTS_DIR.mkdir(parents=True, exist_ok=True)
    shutil.move(str(next_post), str(destination))
    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
