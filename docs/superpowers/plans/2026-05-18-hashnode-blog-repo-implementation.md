# Hashnode Blog Repository Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a lightweight repository for drafting English Hashnode posts from Chinese conversations, validating publishable Markdown, and publishing through Hashnode's official GitHub integration only after an explicit release command.

**Architecture:** Keep supporting files in folders, but store publishable article Markdown in the repository root because current Hashnode GitHub publishing requires root-level Markdown files. Use one small Python stdlib validator for frontmatter and content checks, and run it both locally and in GitHub Actions before any publish-triggering push.

**Tech Stack:** Markdown, Python 3 standard library, GitHub Actions, Git

---

### Task 1: Reconcile The Spec With Current Hashnode Constraints

**Files:**
- Modify: `docs/superpowers/specs/2026-05-18-hashnode-blog-workflow-design.md`
- Create: `docs/hashnode-github-integration.md`

- [ ] **Step 1: Update the approved spec so implementation matches current Hashnode behavior**

Replace the repository-shape section in `docs/superpowers/specs/2026-05-18-hashnode-blog-workflow-design.md` with:

```md
## Repository Design

The repository should act as a content source repository, not as a full blog engine.

Planned structure:

- root-level `*.md` files for publishable Hashnode posts
- `templates/` for reusable article templates
- `scripts/` for helper utilities such as validation
- `.github/workflows/` for validation-only workflows
- `docs/` for process documents and operating rules
- `README.md` for a concise explanation of how writing and publishing works

Implementation note:

- current Hashnode GitHub publishing expects Markdown posts in the repository root rather than a nested `posts/` directory
```

- [ ] **Step 2: Write the Hashnode integration guide**

Create `docs/hashnode-github-integration.md` with:

```md
# Hashnode GitHub Integration Guide

This repository publishes through Hashnode's official GitHub integration.

## Current external constraints

- Hashnode GitHub publishing supports Markdown files only.
- Publishable post files must live in the repository root.
- Required frontmatter keys are `title`, `slug`, `tags`, and `domain`.
- Committing an updated file with the same `slug` updates the existing post.
- A single commit should keep the number of changed files low. Hashnode documents a maximum of 10 respected file changes per commit.

## Setup steps

1. Open the Hashnode dashboard for the target publication.
2. Go to `Dashboard -> GitHub`.
3. Click `Connect now`.
4. Install the Hashnode GitHub app for the repository.
5. Authorize the repository.
6. Confirm the publication is connected to this repository.

## Publishing rules for this repository

- Only root-level article Markdown is synced to Hashnode.
- Supporting files under `docs/`, `templates/`, `scripts/`, and `.github/` are not publishable posts.
- The assistant should only push a new article after the user gives an explicit release command such as `发这篇`, `发布`, or `post it`.

## Operational notes

- If a pushed article does not appear on Hashnode, check the GitHub integration logs in the Hashnode dashboard first.
- To prevent accidental publication for a sample file, set `ignorePost: true`.
- Newsletter scheduling is not supported by this GitHub publishing path.
```

- [ ] **Step 3: Verify the documentation now describes root-level publishing**

Run:

```bash
rg -n "root-level|root rather than a nested|Required frontmatter keys" docs/superpowers/specs/2026-05-18-hashnode-blog-workflow-design.md docs/hashnode-github-integration.md
```

Expected:

```text
docs/superpowers/specs/2026-05-18-hashnode-blog-workflow-design.md:...: - root-level `*.md` files for publishable Hashnode posts
docs/hashnode-github-integration.md:...:- Required frontmatter keys are `title`, `slug`, `tags`, and `domain`.
```

- [ ] **Step 4: Commit the documentation alignment**

Run:

```bash
git add docs/superpowers/specs/2026-05-18-hashnode-blog-workflow-design.md docs/hashnode-github-integration.md
git commit -m "docs: align Hashnode workflow with root-level publishing"
```

Expected:

```text
[main ...] docs: align Hashnode workflow with root-level publishing
```

### Task 2: Add The Repository Operating Guide And Article Template

**Files:**
- Create: `README.md`
- Create: `templates/opinion-post.md`

- [ ] **Step 1: Write the repository README**

Create `README.md` with:

```md
# Blog Source Repository

This repository is the source of truth for blog posts published to Hashnode through Hashnode's official GitHub integration.

## Workflow

1. The writer shares ideas in Chinese.
2. The assistant turns those ideas into an English candidate post.
3. The assistant prepares a root-level Markdown article with Hashnode frontmatter.
4. Nothing is published until the writer explicitly says `发这篇`, `发布`, or `post it`.
5. After that release command, the assistant validates the article and pushes it to GitHub.
6. Hashnode syncs the root-level article file and publishes it.

## Repository layout

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

Run:

```bash
python3 -m unittest -v
python3 scripts/validate_hashnode_posts.py .
```
```

- [ ] **Step 2: Write the opinion-post template**

Create `templates/opinion-post.md` with:

```md
---
title: Replace with the article title
slug: replace-with-the-article-slug
tags: tag-one, tag-two
domain: your-publication.hashnode.dev
subtitle: Replace with a one-line supporting idea
hideFromHashnodeCommunity: false
disableComments: false
enableToc: true
---

# Replace with the article title

Open with the core opinion in one or two sentences.

## What I think is happening

Explain the shift, mistake, or pattern you want to argue about.

## Why that matters

Connect the opinion to engineering practice, team behavior, or product outcomes.

## The trade-off people miss

Surface the tension instead of pretending the answer is obvious.

## Where I land

End with a clear position, not a summary that says nothing.
```

- [ ] **Step 3: Verify the docs and template are readable**

Run:

```bash
sed -n '1,220p' README.md
sed -n '1,220p' templates/opinion-post.md
```

Expected:

```text
The README shows the Chinese-to-English workflow and explicit release gate.
The template shows valid Hashnode-style frontmatter and opinion-essay section headings.
```

- [ ] **Step 4: Commit the operating guide and template**

Run:

```bash
git add README.md templates/opinion-post.md
git commit -m "docs: add blog repo operating guide and template"
```

Expected:

```text
[main ...] docs: add blog repo operating guide and template
```

### Task 3: Implement The Validator With Unit Tests

**Files:**
- Create: `.gitignore`
- Create: `scripts/validate_hashnode_posts.py`
- Create: `tests/test_validate_hashnode_posts.py`

- [ ] **Step 1: Write the failing unit tests first**

Create `tests/test_validate_hashnode_posts.py` with:

```python
import tempfile
import textwrap
import unittest
from pathlib import Path

from scripts.validate_hashnode_posts import validate_post_file, validate_repository


class ValidateHashnodePostsTests(unittest.TestCase):
    def write_file(self, directory: Path, name: str, contents: str) -> Path:
        path = directory / name
        path.write_text(textwrap.dedent(contents).lstrip(), encoding="utf-8")
        return path

    def test_valid_post_passes_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            post = self.write_file(
                repo,
                "valid-post.md",
                """
                ---
                title: A Valid Title
                slug: a-valid-title
                tags: python, testing
                domain: example.hashnode.dev
                ---

                # A Valid Title

                This is a finished post body.
                """,
            )

            errors = validate_post_file(post)

            self.assertEqual(errors, [])

    def test_missing_required_frontmatter_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            post = self.write_file(
                repo,
                "missing-slug.md",
                """
                ---
                title: Missing Slug
                tags: python, testing
                domain: example.hashnode.dev
                ---

                Body
                """,
            )

            errors = validate_post_file(post)

            self.assertIn("missing required frontmatter: slug", errors)

    def test_invalid_slug_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            post = self.write_file(
                repo,
                "bad-slug.md",
                """
                ---
                title: Bad Slug
                slug: Bad Slug
                tags: python, testing
                domain: example.hashnode.dev
                ---

                Body
                """,
            )

            errors = validate_post_file(post)

            self.assertIn("slug must match ^[a-z0-9]+(?:-[a-z0-9]+)*$", errors)

    def test_more_than_five_tags_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            post = self.write_file(
                repo,
                "too-many-tags.md",
                """
                ---
                title: Too Many Tags
                slug: too-many-tags
                tags: one, two, three, four, five, six
                domain: example.hashnode.dev
                ---

                Body
                """,
            )

            errors = validate_post_file(post)

            self.assertIn("tags must contain between 1 and 5 comma-separated values", errors)

    def test_placeholder_body_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            post = self.write_file(
                repo,
                "placeholder.md",
                """
                ---
                title: Placeholder
                slug: placeholder
                tags: python
                domain: example.hashnode.dev
                ---

                [[fill-me]]
                """,
            )

            errors = validate_post_file(post)

            self.assertIn("body contains placeholder text", errors)

    def test_repository_validation_only_scans_root_markdown_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self.write_file(
                repo,
                "valid-post.md",
                """
                ---
                title: Valid Root Post
                slug: valid-root-post
                tags: python
                domain: example.hashnode.dev
                ---

                Valid body.
                """,
            )
            nested = repo / "docs"
            nested.mkdir()
            self.write_file(nested, "ignored.md", "# Not a post")
            self.write_file(repo, "README.md", "# Root readme")

            results = validate_repository(repo)

            self.assertEqual(list(results.keys()), [repo / "valid-post.md"])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests and confirm they fail because the validator does not exist yet**

Run:

```bash
python3 -m unittest tests/test_validate_hashnode_posts.py -v
```

Expected:

```text
ERROR: Failed to import test module: test_validate_hashnode_posts
...
ModuleNotFoundError: No module named 'scripts.validate_hashnode_posts'
```

- [ ] **Step 3: Add the validator implementation and ignore file**

Create `.gitignore` with:

```gitignore
__pycache__/
.pytest_cache/
```

Create `scripts/validate_hashnode_posts.py` with:

```python
import re
import sys
from pathlib import Path

REQUIRED_KEYS = ("title", "slug", "tags", "domain")
SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
TAG_PATTERN = re.compile(r"^[a-z0-9-]+$")
DOMAIN_PATTERN = re.compile(r"^(?!https?://)[a-z0-9.-]+\.[a-z]{2,}$")
PLACEHOLDER_PATTERN = re.compile(r"\[\[fill-me\]\]|{{.+?}}|<replace.+?>", re.IGNORECASE)


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---\n"):
        raise ValueError("frontmatter must start the file")

    parts = text.split("\n---\n", 1)
    if len(parts) != 2:
        raise ValueError("frontmatter must be closed with ---")

    raw_frontmatter = parts[0].removeprefix("---\n")
    body = parts[1].strip()
    frontmatter: dict[str, str] = {}

    for line in raw_frontmatter.splitlines():
        if not line.strip():
            continue
        if ":" not in line:
            raise ValueError(f"invalid frontmatter line: {line}")
        key, value = line.split(":", 1)
        frontmatter[key.strip()] = value.strip()

    return frontmatter, body


def validate_post_file(path: Path) -> list[str]:
    errors: list[str] = []

    try:
        frontmatter, body = parse_frontmatter(path.read_text(encoding="utf-8"))
    except ValueError as exc:
        return [str(exc)]

    missing = [key for key in REQUIRED_KEYS if not frontmatter.get(key)]
    if missing:
        errors.extend(f"missing required frontmatter: {key}" for key in missing)

    title = frontmatter.get("title", "")
    if title and len(title) > 100:
        errors.append("title must be 100 characters or fewer")

    slug = frontmatter.get("slug", "")
    if slug and not SLUG_PATTERN.fullmatch(slug):
        errors.append("slug must match ^[a-z0-9]+(?:-[a-z0-9]+)*$")

    tags_value = frontmatter.get("tags", "")
    if tags_value:
        tags = [tag.strip() for tag in tags_value.split(",") if tag.strip()]
        if not 1 <= len(tags) <= 5:
            errors.append("tags must contain between 1 and 5 comma-separated values")
        invalid_tags = [tag for tag in tags if not TAG_PATTERN.fullmatch(tag)]
        if invalid_tags:
            errors.append(f"invalid tag slugs: {', '.join(invalid_tags)}")

    domain = frontmatter.get("domain", "")
    if domain and not DOMAIN_PATTERN.fullmatch(domain):
        errors.append("domain must be a bare hostname such as example.hashnode.dev")

    if not body:
        errors.append("post body must not be empty")
    elif PLACEHOLDER_PATTERN.search(body):
        errors.append("body contains placeholder text")

    return errors


def iter_root_markdown_files(repo_root: Path) -> list[Path]:
    return sorted(
        path
        for path in repo_root.glob("*.md")
        if path.name != "README.md"
    )


def validate_repository(repo_root: Path) -> dict[Path, list[str]]:
    results: dict[Path, list[str]] = {}
    for path in iter_root_markdown_files(repo_root):
        results[path] = validate_post_file(path)
    return results


def main(argv: list[str]) -> int:
    repo_root = Path(argv[1]).resolve() if len(argv) > 1 else Path.cwd()
    results = validate_repository(repo_root)

    if not results:
        print("No root-level markdown posts found.")
        return 0

    has_errors = False
    for path, errors in results.items():
        if errors:
            has_errors = True
            print(f"{path.name}: FAIL")
            for error in errors:
                print(f"  - {error}")
        else:
            print(f"{path.name}: PASS")

    return 1 if has_errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
```

- [ ] **Step 4: Run the tests again and confirm they pass**

Run:

```bash
python3 -m unittest tests/test_validate_hashnode_posts.py -v
```

Expected:

```text
test_invalid_slug_fails ... ok
test_missing_required_frontmatter_fails ... ok
test_more_than_five_tags_fails ... ok
test_placeholder_body_fails ... ok
test_repository_validation_only_scans_root_markdown_files ... ok
test_valid_post_passes_validation ... ok
```

- [ ] **Step 5: Commit the validator**

Run:

```bash
git add .gitignore scripts/validate_hashnode_posts.py tests/test_validate_hashnode_posts.py
git commit -m "feat: add Hashnode post validator"
```

Expected:

```text
[main ...] feat: add Hashnode post validator
```

### Task 4: Add CI Validation And A Safe Sample Post

**Files:**
- Create: `.github/workflows/validate-hashnode.yml`
- Create: `sample-opinion-post.md`

- [ ] **Step 1: Create a non-publishing sample post in the repository root**

Create `sample-opinion-post.md` with:

```md
---
title: Sample Opinion Post
slug: sample-opinion-post
tags: engineering, writing
domain: your-publication.hashnode.dev
subtitle: A safe root-level sample for validator and integration checks
ignorePost: true
hideFromHashnodeCommunity: true
disableComments: false
enableToc: true
---

# Sample Opinion Post

This file is intentionally ignored by Hashnode publishing.

## Why it exists

It proves that root-level article files are shaped correctly for the validator and the GitHub integration.

## How to use it

Replace it with a real article or keep it as a validator fixture. Leave `ignorePost: true` in place unless you intentionally want it published.
```

- [ ] **Step 2: Create the GitHub Actions workflow**

Create `.github/workflows/validate-hashnode.yml` with:

```yaml
name: Validate Hashnode Posts

on:
  pull_request:
  push:
    branches:
      - main

jobs:
  validate:
    runs-on: ubuntu-latest

    steps:
      - name: Check out repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Run unit tests
        run: python3 -m unittest tests/test_validate_hashnode_posts.py -v

      - name: Validate root-level Hashnode posts
        run: python3 scripts/validate_hashnode_posts.py .
```

- [ ] **Step 3: Run the validator locally against the sample post**

Run:

```bash
python3 scripts/validate_hashnode_posts.py .
```

Expected:

```text
sample-opinion-post.md: PASS
```

- [ ] **Step 4: Commit CI validation and the sample post**

Run:

```bash
git add .github/workflows/validate-hashnode.yml sample-opinion-post.md
git commit -m "ci: validate Hashnode posts on push"
```

Expected:

```text
[main ...] ci: validate Hashnode posts on push
```

### Task 5: Run End-To-End Repository Verification

**Files:**
- Modify: none

- [ ] **Step 1: Run the full local verification sequence**

Run:

```bash
python3 -m unittest -v
python3 scripts/validate_hashnode_posts.py .
git status --short
```

Expected:

```text
All unit tests pass.
The sample root-level post passes validation.
git status shows a clean working tree.
```

- [ ] **Step 2: Confirm the implementation covers the spec**

Run:

```bash
rg -n "explicit release|Hashnode|validator|root-level|Chinese|English" README.md docs/hashnode-github-integration.md docs/superpowers/specs/2026-05-18-hashnode-blog-workflow-design.md scripts/validate_hashnode_posts.py .github/workflows/validate-hashnode.yml
```

Expected:

```text
The grep output shows the release gate, Hashnode integration strategy, root-level article rule, and validator coverage in the final repository files.
```

- [ ] **Step 3: Commit any final documentation touch-ups if verification uncovered them**

Run:

```bash
git status --short
```

Expected:

```text
No output. If there is output, fix the remaining issue before creating another commit.
```
