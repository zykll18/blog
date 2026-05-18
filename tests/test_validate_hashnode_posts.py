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

    def test_invalid_domain_hostname_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)

            for index, domain in enumerate(
                ("example..hashnode.dev", "-bad.hashnode.dev", "bad-.hashnode.dev"),
                start=1,
            ):
                post = self.write_file(
                    repo,
                    f"bad-domain-{index}.md",
                    f"""
                    ---
                    title: Bad Domain
                    slug: bad-domain
                    tags: python
                    domain: {domain}
                    ---

                    Body
                    """,
                )

                errors = validate_post_file(post)

                self.assertIn(
                    "domain must be a bare hostname such as example.hashnode.dev",
                    errors,
                )

    def test_placeholder_style_standalone_tokens_fail(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            for index, body in enumerate(("[[fill-me]]", "{{headline}}", "<replace-body>"), start=1):
                post = self.write_file(
                    repo,
                    f"placeholder-{index}.md",
                    f"""
                    ---
                    title: Placeholder
                    slug: placeholder
                    tags: python
                    domain: example.hashnode.dev
                    ---

                    {body}
                    """,
                )

                errors = validate_post_file(post)

                self.assertIn("body contains placeholder text", errors)

    def test_inline_template_syntax_in_normal_body_does_not_fail(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            post = self.write_file(
                repo,
                "template-syntax.md",
                """
                ---
                title: Template Syntax Example
                slug: template-syntax-example
                tags: python
                domain: example.hashnode.dev
                ---

                Use `{{ user.name }}` in your template, and document the `<replace-me>`
                token inline as part of the example code instead of treating it as a draft note.
                """,
            )

            errors = validate_post_file(post)

            self.assertNotIn("body contains placeholder text", errors)
            self.assertEqual(errors, [])

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
