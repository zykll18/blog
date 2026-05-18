# Blog Source Repository

This repository is the source of truth for blog posts published to Hashnode through Hashnode's official GitHub integration.

## Workflow

1. The writer shares ideas in Chinese.
2. The assistant turns those ideas into an English candidate post.
3. The assistant prepares a root-level Markdown article with Hashnode frontmatter.
4. Nothing is published until the writer explicitly says `发这篇`, `发布`, or `post it`.
5. After that release command, the assistant validates the article and pushes it to GitHub.
6. Hashnode syncs the root-level article file and publishes it.

## Target repository layout

- root-level `*.md`: publishable posts
- `templates/`: reusable writing templates
- `scripts/`: validation utilities
- `tests/`: validator tests
- `docs/`: setup notes and process docs
- `.github/workflows/`: CI validation only

## Release gate

These phrases allow publishing:

- `发这篇`
- `发布`
- `post it`

These phrases do not allow publishing:

- `先存着`
- `先整理`
- `先别发`

## Local validation

When the validator tooling is present, run:

```bash
python3 -m unittest -v
python3 scripts/validate_hashnode_posts.py .
```
