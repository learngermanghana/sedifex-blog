# Saturday Auto-Posting Agent

This repository now includes an automated publishing agent for blog content.

## How it works

- Source queue: `_scheduled_posts/*.md`
- Published destination: `_posts/YYYY-MM-DD-<slug>.md`
- Runner script: `scripts/auto_publish_post.py`
- Schedule: `.github/workflows/saturday-auto-post.yml` (every Saturday at 08:00 UTC)

On each Saturday run, the workflow:

1. Picks the oldest markdown file (alphabetical order) from `_scheduled_posts`.
2. Moves it into `_posts` using the current date as Jekyll filename prefix.
3. Commits and pushes the published post automatically.

## Manual test

```bash
python scripts/auto_publish_post.py --dry-run
```

## Notes

- Keep future content in `_scheduled_posts`.
- Ensure each queued markdown file has valid Jekyll front matter.
- If no files are in the queue, the workflow exits cleanly without a commit.
