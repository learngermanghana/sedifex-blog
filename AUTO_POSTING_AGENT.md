# Daily Product Auto-Posting Agent

This repository includes an automated publishing agent that creates one product promo post per day.

## How it works

- Source feed: `https://www.sedifexmarket.com/api/google-merchant-feed.xml`
- Runner script: `scripts/auto_publish_post.py`
- Published destination: `_posts/YYYY-MM-DD-<product-slug>.md`
- Schedule: `.github/workflows/saturday-auto-post.yml` (daily at 08:00 UTC)
- Default fallback image used in posts:  
  `https://storage.googleapis.com/sedifeximage/stores/vrwe9dieCqchfhxqMc3UiaU2qSJ3/products/draft-ed9225c8-42d0-4be9-afe4-f3342367bea2-1.jpg?v=1776178401704`

On each run, the script:

1. Reads approved Sedifex Market products from the Google Merchant XML feed.
2. Picks one product for the day (rotating and avoiding products already posted when possible).
3. Generates a Markdown blog post in `_posts` with marketing copy and the product link.
4. Uses the product image from the feed when available, otherwise uses the fallback image.

If a product post for the current date already exists, it exits without creating a duplicate.

The blog no longer maintains a separate `/products/` landing page; publishing is focused on the daily post only.

## Manual test

```bash
python scripts/auto_publish_post.py --dry-run
```

## Notes

- Designed to promote Sedifex Market product listings consistently.
- No external Python dependencies are required.
- You can override the feed or fallback image when testing:

```bash
python scripts/auto_publish_post.py \
  --feed-url "https://www.sedifexmarket.com/api/google-merchant-feed.xml" \
  --fallback-image "https://storage.googleapis.com/.../sample.jpg"
```
