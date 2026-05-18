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
