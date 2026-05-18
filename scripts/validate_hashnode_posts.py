import re
import sys
from pathlib import Path

REQUIRED_KEYS = ("title", "slug", "tags", "domain")
SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
TAG_PATTERN = re.compile(r"^[a-z0-9-]+$")
HOSTNAME_LABEL_PATTERN = re.compile(r"^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$")
ALWAYS_FAIL_PLACEHOLDER_LINE_PATTERN = re.compile(
    r"^\s*(?:\[\[fill-me\]\]|<replace.+?>)\s*$",
    re.IGNORECASE,
)
TEMPLATE_PLACEHOLDER_LINE_PATTERN = re.compile(r"^\s*\{\{.+?\}\}\s*$", re.IGNORECASE)


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
    if domain and not _is_valid_domain(domain):
        errors.append("domain must be a bare hostname such as example.hashnode.dev")

    if not body:
        errors.append("post body must not be empty")
    elif _contains_placeholder_line(body):
        errors.append("body contains placeholder text")

    return errors


def iter_root_markdown_files(repo_root: Path) -> list[Path]:
    return sorted(path for path in repo_root.glob("*.md") if path.name != "README.md")


def _is_valid_domain(domain: str) -> bool:
    if "://" in domain:
        return False

    labels = domain.split(".")
    if len(labels) < 2:
        return False

    return all(HOSTNAME_LABEL_PATTERN.fullmatch(label) for label in labels)


def _contains_placeholder_line(body: str) -> bool:
    substantive_lines: list[str] = []
    template_placeholder_lines: list[str] = []
    in_fenced_code_block = False

    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            in_fenced_code_block = not in_fenced_code_block
            continue
        if in_fenced_code_block or not stripped:
            continue
        if ALWAYS_FAIL_PLACEHOLDER_LINE_PATTERN.fullmatch(line):
            return True
        if TEMPLATE_PLACEHOLDER_LINE_PATTERN.fullmatch(line):
            template_placeholder_lines.append(stripped)
        else:
            substantive_lines.append(stripped)

    return bool(template_placeholder_lines) and not substantive_lines


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
