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
COMPACT_TEMPLATE_PLACEHOLDER_PATTERN = re.compile(r"^\s*\{\{[a-z0-9_-]+\}\}\s*$", re.IGNORECASE)
SCAFFOLD_LINES = {
    "replace with the article title",
    "replace with a one-line supporting idea",
    "open with the core opinion in one or two sentences.",
    "explain the shift, mistake, or pattern you want to argue about.",
    "connect the opinion to engineering practice, team behavior, or product outcomes.",
    "surface the tension instead of pretending the answer is obvious.",
    "end with a clear position, not a summary that says nothing.",
}
TEMPLATE_FRONTMATTER_PLACEHOLDERS = {
    "title": "replace with the article title",
    "slug": "replace-with-the-article-slug",
    "domain": "your-publication.hashnode.dev",
    "subtitle": "replace with a one-line supporting idea",
}


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    text = text.removeprefix("\ufeff")
    text = text.replace("\r\n", "\n").replace("\r", "\n")

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

    errors.extend(_validate_template_frontmatter(frontmatter))

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
    else:
        if _has_unclosed_fenced_code_block(body):
            errors.append("markdown contains an unclosed fenced code block")
        if _contains_placeholder_line(body):
            errors.append("body contains placeholder text")

    return errors


def iter_root_markdown_files(repo_root: Path) -> list[Path]:
    return sorted(path for path in repo_root.glob("*.md") if path.name != "README.md")


def _is_valid_domain(domain: str) -> bool:
    if "://" in domain:
        return False
    if len(domain) > 253:
        return False

    labels = domain.split(".")
    if len(labels) < 2:
        return False
    if all(label.isdigit() for label in labels):
        return False
    if any(len(label) > 63 for label in labels):
        return False

    return all(HOSTNAME_LABEL_PATTERN.fullmatch(label) for label in labels)


def _contains_placeholder_line(body: str) -> bool:
    substantive_lines: list[str] = []
    active_fence: tuple[str, int] | None = None
    in_indented_code_block = False
    previous_line_blank = True

    for line in body.splitlines():
        stripped = line.strip()
        if active_fence is None and _is_indented_code_line(line, previous_line_blank, in_indented_code_block):
            in_indented_code_block = True
            previous_line_blank = False
            continue
        fence = _get_fence_marker(stripped)
        if active_fence is None and fence is not None:
            active_fence = fence
            in_indented_code_block = False
            previous_line_blank = False
            continue
        if active_fence is not None and _is_closing_fence(stripped, active_fence):
            active_fence = None
            in_indented_code_block = False
            previous_line_blank = False
            continue
        if active_fence is not None:
            previous_line_blank = not stripped
            continue
        in_indented_code_block = False
        if not stripped:
            previous_line_blank = True
            continue
        if ALWAYS_FAIL_PLACEHOLDER_LINE_PATTERN.fullmatch(line):
            return True
        if _is_scaffold_line(stripped):
            return True
        if TEMPLATE_PLACEHOLDER_LINE_PATTERN.fullmatch(line):
            return True
        else:
            substantive_lines.append(stripped)
        previous_line_blank = False

    return False


def _has_unclosed_fenced_code_block(body: str) -> bool:
    active_fence: tuple[str, int] | None = None
    in_indented_code_block = False
    previous_line_blank = True

    for line in body.splitlines():
        stripped = line.strip()
        if active_fence is None and _is_indented_code_line(line, previous_line_blank, in_indented_code_block):
            in_indented_code_block = True
            previous_line_blank = False
            continue
        fence = _get_fence_marker(stripped)
        if active_fence is None and fence is not None:
            active_fence = fence
            in_indented_code_block = False
            previous_line_blank = False
            continue
        if active_fence is not None and _is_closing_fence(stripped, active_fence):
            active_fence = None
            previous_line_blank = False
            continue
        if active_fence is None:
            in_indented_code_block = False
            previous_line_blank = not stripped
        else:
            previous_line_blank = not stripped

    return active_fence is not None


def _is_indented_code_line(
    line: str,
    previous_line_blank: bool,
    in_indented_code_block: bool,
) -> bool:
    return (previous_line_blank or in_indented_code_block) and (
        line.startswith("    ") or line.startswith("\t")
    )


def _get_fence_marker(stripped_line: str) -> tuple[str, int] | None:
    for fence_char in ("`", "~"):
        if stripped_line.startswith(fence_char * 3):
            fence_length = len(stripped_line) - len(stripped_line.lstrip(fence_char))
            return fence_char, fence_length
    return None


def _is_closing_fence(stripped_line: str, active_fence: tuple[str, int]) -> bool:
    fence = _get_fence_marker(stripped_line)
    if fence is None:
        return False

    marker, length = fence
    if marker != active_fence[0] or length < active_fence[1]:
        return False

    trailing = stripped_line[length:]
    return not trailing.strip()


def _is_scaffold_line(stripped_line: str) -> bool:
    normalized = stripped_line.lower()
    if normalized.startswith("#"):
        normalized = normalized.lstrip("#").strip()
    return normalized in SCAFFOLD_LINES


def _validate_template_frontmatter(frontmatter: dict[str, str]) -> list[str]:
    if _is_true(frontmatter.get("ignorePost", "")):
        return []

    errors: list[str] = []
    for key, placeholder in TEMPLATE_FRONTMATTER_PLACEHOLDERS.items():
        value = frontmatter.get(key, "")
        if value.lower() == placeholder:
            errors.append(f"frontmatter contains template placeholder: {key}")
    return errors


def _is_true(value: str) -> bool:
    return value.strip().lower() == "true"


def validate_repository(repo_root: Path) -> dict[Path, list[str]]:
    results: dict[Path, list[str]] = {}
    for path in iter_root_markdown_files(repo_root):
        raw_text = path.read_text(encoding="utf-8")
        normalized = raw_text.removeprefix("\ufeff").replace("\r\n", "\n").replace("\r", "\n")
        if not normalized.startswith("---\n"):
            continue
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
