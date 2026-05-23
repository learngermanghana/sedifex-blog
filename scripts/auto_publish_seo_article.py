#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import date
from html import unescape
import json
import os
from pathlib import Path
import random
import re
import sys
from textwrap import dedent
import urllib.request
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
POSTS_DIR = ROOT / "_posts"
SOCIAL_DIR = ROOT / "_social"

GOOGLE_MERCHANT_FEED_URL = "https://www.sedifexmarket.com/api/google-merchant-feed.xml"
OPENAI_CHAT_COMPLETIONS_URL = "https://api.openai.com/v1/chat/completions"
DEFAULT_MODEL = "gpt-4.1-mini"

SEO_TOPICS = [
    {
        "angle": "buyer_guide",
        "title_hint": "How to buy products online in Ghana and get an instant receipt",
        "audience": "buyers in Ghana who want a simple way to shop online",
    },
    {
        "angle": "seller_education",
        "title_hint": "How small shops in Ghana can sell online with Sedifex Market",
        "audience": "shop owners, salons, boutiques, and local sellers",
    },
    {
        "angle": "inventory_automation",
        "title_hint": "Why online sales should update inventory automatically",
        "audience": "business owners who struggle with stock tracking",
    },
    {
        "angle": "pay_sedifex",
        "title_hint": "How customers can search a store or product and pay online with Pay Sedifex",
        "audience": "customers and stores using pay.sedifex.com",
    },
    {
        "angle": "beauty_business",
        "title_hint": "How beauty shops can sell products, services, and courses online",
        "audience": "beauty shops, spas, salons, and training schools",
    },
    {
        "angle": "marketplace_trust",
        "title_hint": "Why Sedifex Market helps buyers and stores complete orders faster",
        "audience": "buyers and store owners who need trust and speed",
    },
]


def slugify(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text or "")
    text = unescape(text).strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-{2,}", "-", text).strip("-")
    return text or "sedifex-seo-article"


def squash_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", unescape(text or "")).strip()


def xml_text(item: ET.Element, *tags: str) -> str:
    for tag in tags:
        node = item.find(tag)
        if node is not None and node.text and node.text.strip():
            return node.text.strip()
    return ""


def first_non_empty(*values: str | None) -> str:
    for value in values:
        cleaned = squash_whitespace(value or "")
        if cleaned:
            return cleaned
    return ""


def fetch_feed_products(feed_url: str, max_items: int = 12) -> list[dict[str, str]]:
    req = urllib.request.Request(
        feed_url,
        headers={
            "User-Agent": "sedifex-blog-ai-seo-agent/1.0",
            "Accept": "application/rss+xml, application/xml;q=0.9, */*;q=0.8",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        raw = response.read()

    root = ET.fromstring(raw)
    channel = root.find("channel")
    if channel is None:
        return []

    ns_g = "{http://base.google.com/ns/1.0}"
    products: list[dict[str, str]] = []
    for item in channel.findall("item"):
        title = first_non_empty(xml_text(item, f"{ns_g}title"), xml_text(item, "title"))
        if not title:
            continue
        products.append(
            {
                "id": first_non_empty(xml_text(item, f"{ns_g}id"), slugify(title)),
                "title": title,
                "description": first_non_empty(xml_text(item, f"{ns_g}description"), xml_text(item, "description")),
                "link": first_non_empty(xml_text(item, f"{ns_g}link"), xml_text(item, "link"), "https://www.sedifexmarket.com"),
                "image": first_non_empty(xml_text(item, f"{ns_g}image_link")),
                "brand": first_non_empty(xml_text(item, f"{ns_g}brand"), "Sedifex Market"),
                "price": first_non_empty(xml_text(item, f"{ns_g}price")),
                "category": first_non_empty(xml_text(item, f"{ns_g}product_type")),
            }
        )

    return products[:max_items]


def existing_ai_post_for_today(today_iso: str) -> Path | None:
    for post_path in sorted(POSTS_DIR.glob(f"{today_iso}-*.md")):
        try:
            content = post_path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if "source_agent: sedifex-ai-seo-agent" in content:
            return post_path
    return None


def escape_yaml(text: str) -> str:
    return text.replace('"', '\\"')


def clean_markdown_body(body: str) -> str:
    body = body.strip()
    if body.startswith("---"):
        parts = body.split("---", 2)
        if len(parts) == 3:
            body = parts[2].strip()
    return body


def choose_topic(today: date) -> dict[str, str]:
    return SEO_TOPICS[today.toordinal() % len(SEO_TOPICS)]


def build_prompt(topic: dict[str, str], products: list[dict[str, str]], today_iso: str) -> list[dict[str, str]]:
    product_context = products[:8]
    system = (
        "You are a Ghana-focused SEO blog writer for Sedifex and Sedifex Market. "
        "Write useful, practical, honest content for buyers and small businesses. "
        "Do not claim a product is available unless it is listed in the provided product feed. "
        "Do not mention restricted products, medicines, supplements, gambling, alcohol, nicotine, weapons, adult products, or anything unsafe. "
        "Return only valid JSON with keys: title, slug, excerpt, body_markdown, social_caption."
    )
    user = {
        "date": today_iso,
        "topic": topic,
        "required_links": {
            "Sedifex Market": "https://www.sedifexmarket.com",
            "Pay Sedifex": "https://pay.sedifex.com",
            "Sedifex": "https://www.sedifex.com",
        },
        "product_examples_from_feed": product_context,
        "writing_rules": [
            "Write 800 to 1100 words.",
            "Use Markdown headings.",
            "Make the title SEO-friendly and natural, not robotic.",
            "Include practical steps for readers.",
            "Mention instant receipts, online checkout, store order visibility, and inventory updates where relevant.",
            "Include a short section for buyers and another for sellers.",
            "Use clear Ghana context without overpromising delivery or payment guarantees.",
            "End with a strong call-to-action linking to Sedifex Market, Pay Sedifex, and Sedifex.",
            "The social_caption should be Instagram-friendly, under 120 words, and include: Search Sedifex Market on Google or DM SHOP for the link.",
        ],
    }
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": json.dumps(user, ensure_ascii=False)},
    ]


def call_openai(messages: list[dict[str, str]], model: str) -> dict[str, str]:
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")

    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.8,
        "response_format": {"type": "json_object"},
    }
    req = urllib.request.Request(
        OPENAI_CHAT_COMPLETIONS_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=90) as response:
        raw = response.read().decode("utf-8")

    data = json.loads(raw)
    content = data["choices"][0]["message"]["content"]
    parsed = json.loads(content)

    required = ["title", "slug", "excerpt", "body_markdown", "social_caption"]
    missing = [key for key in required if not str(parsed.get(key, "")).strip()]
    if missing:
        raise ValueError(f"OpenAI response missing required fields: {', '.join(missing)}")

    return {key: squash_whitespace(parsed[key]) if key != "body_markdown" else clean_markdown_body(str(parsed[key])) for key in required}


def fallback_article(topic: dict[str, str], products: list[dict[str, str]], today_iso: str) -> dict[str, str]:
    title = topic["title_hint"]
    slug = slugify(title)
    product_lines = "\n".join(
        f"- [{product['title']}]({product['link']}) — {product.get('price') or 'price shown on product page'}"
        for product in products[:5]
    ) or "- Explore current listings on [Sedifex Market](https://www.sedifexmarket.com)."
    body = dedent(
        f"""
        ## Why this matters

        Customers in Ghana want a faster way to find products, pay, and receive confirmation. Store owners also need a better way to record orders, update inventory, and keep sales data organized.

        Sedifex connects these needs through Sedifex Market, Pay Sedifex, and the main Sedifex business system.

        ## For buyers

        Instead of waiting for long calls or messages, buyers can search online, open a product or store, and complete checkout. After payment, the business receives the order details and the customer receives a receipt.

        ## For sellers

        Sedifex helps businesses manage products, services, payments, receipts, and stock from one place. When online sales connect to inventory, the business can reduce manual work and keep reports cleaner.

        ## Featured examples from Sedifex Market

        {product_lines}

        ## What to do next

        Buyers can visit [Sedifex Market](https://www.sedifexmarket.com) to search for products, or use [Pay Sedifex](https://pay.sedifex.com) to search for a store and pay online.

        Business owners can visit [Sedifex](https://www.sedifex.com) to learn how to manage inventory, payments, receipts, and customer orders from one system.
        """
    ).strip()
    return {
        "title": title,
        "slug": slug,
        "excerpt": "Learn how Sedifex helps buyers shop online and helps businesses manage payments, receipts, and inventory.",
        "body_markdown": body,
        "social_caption": "Shopping is easier with Sedifex Market 🛒 Search Sedifex Market on Google or DM SHOP for the link.",
    }


def build_post(today_iso: str, article: dict[str, str], model: str, feed_url: str) -> str:
    return dedent(
        f"""\
        ---
        layout: post
        title: "{escape_yaml(article['title'])}"
        date: {today_iso}
        categories: [Sedifex, Business Automation]
        tags: [sedifex, sedifex market, online payments, inventory management, ghana business]
        excerpt: "{escape_yaml(article['excerpt'][:220])}"
        source_agent: sedifex-ai-seo-agent
        source_feed: {feed_url}
        ai_model: {model}
        ---

        {article['body_markdown']}
        """
    ).strip() + "\n"


def write_social_caption(today_iso: str, slug: str, caption: str, dry_run: bool) -> None:
    destination = SOCIAL_DIR / f"{today_iso}-{slug}.txt"
    print(f"Social caption: {destination.relative_to(ROOT)}")
    if dry_run:
        return
    SOCIAL_DIR.mkdir(parents=True, exist_ok=True)
    destination.write_text(caption.strip() + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate one AI SEO article for Sedifex / Sedifex Market")
    parser.add_argument("--dry-run", action="store_true", help="Show actions without writing files")
    parser.add_argument("--feed-url", default=GOOGLE_MERCHANT_FEED_URL, help="Google Merchant XML feed URL")
    parser.add_argument("--model", default=os.environ.get("OPENAI_MODEL", DEFAULT_MODEL), help="OpenAI model")
    parser.add_argument("--allow-fallback", action="store_true", help="Write a template article if AI generation fails")
    args = parser.parse_args()

    today = date.today()
    today_iso = today.isoformat()

    existing = existing_ai_post_for_today(today_iso)
    if existing:
        print(f"AI SEO article already exists for today: {existing.relative_to(ROOT)}")
        return 0

    try:
        products = fetch_feed_products(args.feed_url)
    except Exception as exc:
        print(f"Could not load product feed: {exc}")
        products = []

    topic = choose_topic(today)
    random.shuffle(products)

    try:
        article = call_openai(build_prompt(topic, products, today_iso), args.model)
    except Exception as exc:
        print(f"AI article generation failed: {exc}")
        if not args.allow_fallback:
            print("Skipping publish. Add --allow-fallback to publish a template article when AI fails.")
            return 0
        article = fallback_article(topic, products, today_iso)

    slug = slugify(article.get("slug") or article["title"])
    destination = POSTS_DIR / f"{today_iso}-seo-{slug}.md"
    if destination.exists():
        print(f"Destination already exists: {destination.relative_to(ROOT)}")
        return 0

    content = build_post(today_iso, article, args.model, args.feed_url)

    print(f"Selected SEO topic: {topic['title_hint']}")
    print(f"Publishing to: {destination.relative_to(ROOT)}")

    if not args.dry_run:
        POSTS_DIR.mkdir(parents=True, exist_ok=True)
        destination.write_text(content, encoding="utf-8")

    write_social_caption(today_iso, slug, article["social_caption"], args.dry_run)
    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
