#!/usr/bin/env python3
from __future__ import annotations

from datetime import date
import json
import os
from pathlib import Path
import re
import sys
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
POSTS_DIR = ROOT / "_posts"
SOCIAL_DIR = ROOT / "_social"
POSTED_STATE = SOCIAL_DIR / "linkedin-posted.json"
LINKEDIN_POSTS_URL = "https://api.linkedin.com/rest/posts"
DEFAULT_LINKEDIN_VERSION = "202510"
DEFAULT_BLOG_BASE_URL = "https://blog.sedifex.com"


def load_state() -> dict[str, str]:
    if not POSTED_STATE.exists():
        return {}
    try:
        return json.loads(POSTED_STATE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_state(state: dict[str, str]) -> None:
    SOCIAL_DIR.mkdir(parents=True, exist_ok=True)
    POSTED_STATE.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def linkedin_url_for_post(post_id: str) -> str:
    if not post_id:
        return ""
    return f"https://www.linkedin.com/feed/update/{post_id}/"


def normalize_author_urn(value: str) -> str:
    cleaned = value.strip().strip('"').strip("'")
    if not cleaned:
        return ""
    if cleaned.startswith("urn:"):
        return cleaned
    if cleaned.startswith("li:person:"):
        return f"urn:{cleaned}"
    if cleaned.startswith("person:"):
        return f"urn:li:{cleaned}"
    if cleaned.startswith("organization:"):
        return f"urn:li:{cleaned}"
    return f"urn:li:person:{cleaned}"


def read_front_matter_value(post_path: Path, key: str) -> str:
    try:
        content = post_path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""
    pattern = re.compile(rf"^{re.escape(key)}:\s*(.+?)\s*$")
    for line in content.splitlines():
        match = pattern.match(line.strip())
        if match:
            return match.group(1).strip().strip('"')
    return ""


def find_today_seo_post(today_iso: str) -> Path | None:
    for post_path in sorted(POSTS_DIR.glob(f"{today_iso}-*.md")):
        if read_front_matter_value(post_path, "source_agent") == "sedifex-ai-seo-agent":
            return post_path
    return None


def find_today_seo_caption(today_iso: str) -> Path | None:
    captions = sorted(SOCIAL_DIR.glob(f"{today_iso}-*.txt"))
    seo_captions = [path for path in captions if "daily-product" not in path.name]
    return seo_captions[0] if seo_captions else None


def blog_url_for_post(post_path: Path, blog_base_url: str) -> str:
    base = blog_base_url.rstrip("/")
    permalink = read_front_matter_value(post_path, "permalink")
    if permalink:
      return f"{base}/{permalink.lstrip('/')}"

    match = re.match(r"^(\d{4})-(\d{2})-(\d{2})-(.+)\.md$", post_path.name)
    if not match:
        return base
    year, month, day, slug = match.groups()
    return f"{base}/{year}/{month}/{day}/{slug}.html"


def build_commentary(caption_path: Path, post_url: str) -> str:
    caption = caption_path.read_text(encoding="utf-8", errors="ignore").strip()
    if post_url and post_url not in caption:
        caption = f"{caption}\n\nRead more: {post_url}"
    return caption[:2800]


def post_to_linkedin(commentary: str) -> str:
    token = os.environ.get("LINKEDIN_ACCESS_TOKEN", "").strip()
    author = normalize_author_urn(os.environ.get("LINKEDIN_AUTHOR_URN", ""))
    version = os.environ.get("LINKEDIN_VERSION", DEFAULT_LINKEDIN_VERSION).strip()

    if not token:
        raise RuntimeError("LINKEDIN_ACCESS_TOKEN is not configured")
    if not author:
        raise RuntimeError("LINKEDIN_AUTHOR_URN is not configured")

    print(f"Using LinkedIn author type: {'organization' if ':organization:' in author else 'person'}")

    payload = {
        "author": author,
        "commentary": commentary,
        "visibility": "PUBLIC",
        "distribution": {
            "feedDistribution": "MAIN_FEED",
            "targetEntities": [],
            "thirdPartyDistributionChannels": [],
        },
        "lifecycleState": "PUBLISHED",
        "isReshareDisabledByAuthor": False,
    }

    request = urllib.request.Request(
        LINKEDIN_POSTS_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Linkedin-Version": version,
            "X-Restli-Protocol-Version": "2.0.0",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            post_id = response.headers.get("x-restli-id", "")
            if not post_id:
                raise RuntimeError("LinkedIn returned success but no x-restli-id post ID header")
            print(f"LinkedIn post created: {post_id}")
            print(f"LinkedIn post URL: {linkedin_url_for_post(post_id)}")
            return post_id
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"LinkedIn post failed: HTTP {exc.code} {body}") from exc


def main() -> int:
    today_iso = os.environ.get("POST_DATE", date.today().isoformat())
    blog_base_url = os.environ.get("BLOG_BASE_URL", DEFAULT_BLOG_BASE_URL)

    post_path = find_today_seo_post(today_iso)
    caption_path = find_today_seo_caption(today_iso)

    if not post_path or not caption_path:
        print("No SEO article/caption found for today. Skipping LinkedIn post.")
        return 0

    state = load_state()
    state_key = f"linkedin::{caption_path.name}"
    if state.get(state_key):
        print(f"Already posted to LinkedIn: {caption_path.name}")
        print(f"Saved LinkedIn post URL: {linkedin_url_for_post(state[state_key])}")
        return 0

    post_url = blog_url_for_post(post_path, blog_base_url)
    commentary = build_commentary(caption_path, post_url)
    print("Prepared LinkedIn post:")
    print(commentary)

    if os.environ.get("LINKEDIN_DRY_RUN", "").lower() in {"1", "true", "yes"}:
        print("LINKEDIN_DRY_RUN enabled. Not posting.")
        return 0

    try:
        post_id = post_to_linkedin(commentary)
    except Exception as exc:
        print(str(exc))
        return 1

    state[state_key] = post_id
    save_state(state)
    return 0


if __name__ == "__main__":
    sys.exit(main())
