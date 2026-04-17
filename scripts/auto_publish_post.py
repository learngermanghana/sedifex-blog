#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import date
from html import unescape
from pathlib import Path
import re
import sys
from textwrap import dedent
import urllib.request
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
POSTS_DIR = ROOT / "_posts"

RSS_FEED_URL = "https://www.sedifexmarket.com/api/feeds/google-merchant-rss"
DEFAULT_IMAGE_URL = (
    "https://storage.googleapis.com/sedifeximage/stores/vrwe9dieCqchfhxqMc3UiaU2qSJ3/"
    "products/draft-ed9225c8-42d0-4be9-afe4-f3342367bea2-1.jpg?v=1776178401704"
)


def slugify(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text or "")
    text = unescape(text).strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-{2,}", "-", text).strip("-")
    return text or "product"


def squash_whitespace(text: str) -> str:
    text = re.sub(r"\s+", " ", unescape(text or "")).strip()
    return text


def first_non_empty(*values: str | None) -> str:
    for value in values:
        cleaned = squash_whitespace(value or "")
        if cleaned:
            return cleaned
    return ""


def xml_text(item: ET.Element, *tags: str) -> str:
    for tag in tags:
        node = item.find(tag)
        if node is not None and node.text and node.text.strip():
            return node.text.strip()
    return ""


def parse_feed(feed_url: str) -> list[dict[str, str]]:
    req = urllib.request.Request(
        feed_url,
        headers={
            "User-Agent": "sedifex-blog-auto-publisher/1.0",
            "Accept": "application/rss+xml, application/xml;q=0.9, */*;q=0.8",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        raw = response.read()

    root = ET.fromstring(raw)
    channel = root.find("channel")
    if channel is None:
        return []

    products: list[dict[str, str]] = []
    ns_g = "{http://base.google.com/ns/1.0}"

    for item in channel.findall("item"):
        title = first_non_empty(xml_text(item, "title"), "Featured product")
        product_id = first_non_empty(
            xml_text(item, f"{ns_g}id"),
            xml_text(item, "guid"),
            slugify(title),
        )
        product_link = first_non_empty(xml_text(item, "link"), "https://www.sedifexmarket.com")
        description = first_non_empty(xml_text(item, f"{ns_g}description"), xml_text(item, "description"))
        image_link = first_non_empty(xml_text(item, f"{ns_g}image_link"))
        brand = first_non_empty(xml_text(item, f"{ns_g}brand"), "Sedifex Market")
        price = first_non_empty(xml_text(item, f"{ns_g}price"), "")
        condition = first_non_empty(xml_text(item, f"{ns_g}condition"), "")
        availability = first_non_empty(xml_text(item, f"{ns_g}availability"), "")

        products.append(
            {
                "id": product_id,
                "title": title,
                "slug": slugify(title),
                "link": product_link,
                "description": description,
                "image": image_link,
                "brand": brand,
                "price": price,
                "condition": condition,
                "availability": availability,
            }
        )

    return products


def escape_yaml(text: str) -> str:
    return text.replace('"', '\\"')


def existing_product_ids() -> set[str]:
    ids: set[str] = set()
    if not POSTS_DIR.exists():
        return ids

    pattern = re.compile(r"^source_product_id:\s*(.+?)\s*$")
    for post_file in POSTS_DIR.glob("*.md"):
        try:
            content = post_file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for line in content.splitlines():
            match = pattern.match(line.strip())
            if match:
                ids.add(match.group(1).strip())
                break
    return ids


def read_post_metadata(post_path: Path) -> dict[str, str]:
    metadata: dict[str, str] = {}
    pattern = re.compile(r"^(source_product_id|source_feed|title):\s*(.+?)\s*$")
    try:
        content = post_path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return metadata

    for line in content.splitlines():
        match = pattern.match(line.strip())
        if not match:
            continue
        metadata[match.group(1)] = match.group(2).strip().strip('"')
    return metadata


def find_today_post(today_iso: str) -> Path | None:
    matches = sorted(POSTS_DIR.glob(f"{today_iso}-*.md"))
    return matches[0] if matches else None


def find_today_product_post(today_iso: str) -> Path | None:
    for post_path in sorted(POSTS_DIR.glob(f"{today_iso}-*.md")):
        metadata = read_post_metadata(post_path)
        if metadata.get("source_product_id"):
            return post_path
    return None


def unique_destination(base_path: Path) -> Path:
    if not base_path.exists():
        return base_path

    stem = base_path.stem
    suffix = base_path.suffix
    parent = base_path.parent
    counter = 2
    while True:
        candidate = parent / f"{stem}-{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def pick_product(products: list[dict[str, str]], used_ids: set[str], today: date) -> dict[str, str]:
    if not products:
        raise ValueError("No products found in feed")

    start_index = today.toordinal() % len(products)
    for offset in range(len(products)):
        product = products[(start_index + offset) % len(products)]
        if product["id"] not in used_ids:
            return product

    # If everything has been used, rotate anyway so posting can continue.
    return products[start_index]


def build_post(today_iso: str, product: dict[str, str], fallback_image: str) -> str:
    product_image = product["image"] or fallback_image
    post_image = product_image
    inline_image = product_image
    excerpt_base = product["description"] or f"Discover {product['title']} on Sedifex Market."
    excerpt = squash_whitespace(excerpt_base)[:160]

    details = []
    if product["brand"]:
        details.append(f"- **Brand:** {product['brand']}")
    if product["price"]:
        details.append(f"- **Price:** {product['price']}")
    if product["condition"]:
        details.append(f"- **Condition:** {product['condition']}")

    details_block = "\n".join(details) if details else "- Product details are available on the product page."

    body = dedent(
        f"""\
---
layout: post
title: "Daily Product Spotlight: {escape_yaml(product['title'])}"
date: {today_iso}
categories: [Marketing, Products]
tags: [sedifex market, product spotlight, merchant promo, ecommerce]
excerpt: "{escape_yaml(excerpt)}"
image: {post_image}
source_product_id: {escape_yaml(product['id'])}
source_feed: {RSS_FEED_URL}
---

Today's featured pick from Sedifex Market is **{product['title']}**.

{squash_whitespace(product['description']) or 'This product is now being promoted as part of our daily merchant spotlight series.'}

{details_block}

![{product['title']}]({inline_image})

## Why we are spotlighting this product

Sedifex Market helps merchants gain visibility by promoting one product every day. This keeps the catalog fresh, helps shoppers discover new listings, and gives stores consistent exposure.

👉 View product: [{product['title']}]({product['link']})

👉 Explore more products: [Sedifex Market](https://www.sedifexmarket.com)
"""
    ).strip() + "\n"

    return body


def main() -> int:
    parser = argparse.ArgumentParser(description="Publish one daily product spotlight post from RSS")
    parser.add_argument("--dry-run", action="store_true", help="Show actions without writing files")
    parser.add_argument("--feed-url", default=RSS_FEED_URL, help="RSS feed URL")
    parser.add_argument("--fallback-image", default=DEFAULT_IMAGE_URL, help="Fallback image URL")
    args = parser.parse_args()

    today = date.today()
    today_iso = today.isoformat()

    try:
        products = parse_feed(args.feed_url)
    except Exception as exc:
        print(f"Failed to parse feed: {exc}")
        print("Skipping publish for this run.")
        return 0

    if not products:
        print("No products found in RSS feed.")
        return 0

    today_post = find_today_post(today_iso)
    today_product_post = find_today_product_post(today_iso)
    product: dict[str, str] | None = None
    destination: Path
    slug: str

    if today_product_post is not None:
        print(f"Daily product post already exists for today: {today_product_post.relative_to(ROOT)}")
        return 0

    if today_post is not None:
        destination = today_post
        slug = today_post.stem.removeprefix(f"{today_iso}-")
        metadata = read_post_metadata(today_post)
        source_product_id = metadata.get("source_product_id", "")
        if source_product_id:
            product = next((p for p in products if p["id"] == source_product_id), None)
        if product is None and slug:
            product = next((p for p in products if p["slug"] == slug), None)

        if not metadata.get("source_product_id"):
            used_ids = existing_product_ids()
            product = pick_product(products, used_ids, today)
            slug = slugify(product["title"])
            destination = unique_destination(POSTS_DIR / f"{today_iso}-daily-product-{slug}.md")
    else:
        used_ids = existing_product_ids()
        product = pick_product(products, used_ids, today)
        slug = slugify(product["title"])
        destination = unique_destination(POSTS_DIR / f"{today_iso}-daily-product-{slug}.md")

    if product is None:
        print("Could not map today's post to a current feed item; using first feed product.")
        product = products[0]
        slug = slugify(product["title"])

    if destination.exists():
        print(f"Post already exists for today: {destination.relative_to(ROOT)}")
        return 0

    content = build_post(today_iso, product, args.fallback_image)

    print(f"Selected product: {product['title']} (id={product['id']})")
    print(f"Publishing to: {destination.relative_to(ROOT)}")

    if args.dry_run:
        return 0

    POSTS_DIR.mkdir(parents=True, exist_ok=True)
    destination.write_text(content, encoding="utf-8")
    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
