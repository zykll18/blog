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
            overlong_label = "a" * 64
            overlong_hostname = ".".join(["a" * 63, "b" * 63, "c" * 63, "d" * 62, "com"])

            for index, domain in enumerate(
                (
                    "example..hashnode.dev",
                    "-bad.hashnode.dev",
                    "bad-.hashnode.dev",
                    "127.0.0.1",
                    f"{overlong_label}.hashnode.dev",
                    overlong_hostname,
                ),
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

    def test_prose_with_fill_me_placeholder_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            post = self.write_file(
                repo,
                "fill-me-draft.md",
                """
                ---
                title: Fill Me Draft
                slug: fill-me-draft
                tags: python
                domain: example.hashnode.dev
                ---

                Introductory prose for the draft.

                [[fill-me]]

                Closing note that the draft is not done yet.
                """,
            )

            errors = validate_post_file(post)

            self.assertIn("body contains placeholder text", errors)

    def test_prose_with_replace_placeholder_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            post = self.write_file(
                repo,
                "replace-draft.md",
                """
                ---
                title: Replace Draft
                slug: replace-draft
                tags: python
                domain: example.hashnode.dev
                ---

                This article still needs a full walkthrough.

                <replace-body>

                The introduction and conclusion have already been outlined.
                """,
            )

            errors = validate_post_file(post)

            self.assertIn("body contains placeholder text", errors)

    def test_prose_with_compact_template_placeholder_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            post = self.write_file(
                repo,
                "compact-template-draft.md",
                """
                ---
                title: Compact Template Draft
                slug: compact-template-draft
                tags: python
                domain: example.hashnode.dev
                ---

                Introductory prose for the draft.

                {{headline}}

                Outro text that should not hide the draft marker.
                """,
            )

            errors = validate_post_file(post)

            self.assertIn("body contains placeholder text", errors)

    def test_unedited_opinion_template_scaffold_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            post = self.write_file(
                repo,
                "template-copy.md",
                """
                ---
                title: Replace with the article title
                slug: replace-with-the-article-slug
                tags: tag-one, tag-two
                domain: example.hashnode.dev
                subtitle: Replace with a one-line supporting idea
                hideFromHashnodeCommunity: false
                disableComments: false
                saveAsDraft: true
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

    def test_fenced_code_block_with_template_syntax_does_not_fail(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            post = self.write_file(
                repo,
                "fenced-code-example.md",
                """
                ---
                title: Fenced Code Example
                slug: fenced-code-example
                tags: python
                domain: example.hashnode.dev
                ---

                The template syntax below is part of the article example.

                ```jinja
                {{ user.name }}
                ```

                Continue with the explanation after the snippet.
                """,
            )

            errors = validate_post_file(post)

            self.assertNotIn("body contains placeholder text", errors)
            self.assertEqual(errors, [])

    def test_longer_backtick_fence_not_closed_by_shorter_backticks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            post = self.write_file(
                repo,
                "long-backtick-fence.md",
                """
                ---
                title: Long Backtick Fence
                slug: long-backtick-fence
                tags: python
                domain: example.hashnode.dev
                ---

                The code sample below uses four-backtick fences:

                ````md
                ```
                [[fill-me]]
                ````

                The placeholder token is still inside the longer fenced code example.
                """,
            )

            errors = validate_post_file(post)

            self.assertNotIn("body contains placeholder text", errors)
            self.assertEqual(errors, [])

    def test_longer_matching_closing_fence_closes_block_and_later_placeholder_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            post = self.write_file(
                repo,
                "longer-closing-fence.md",
                """
                ---
                title: Longer Closing Fence
                slug: longer-closing-fence
                tags: python
                domain: example.hashnode.dev
                ---

                The code sample below closes with a longer backtick run:

                ```md
                {{ user.name }}
                ````

                [[fill-me]]
                """,
            )

            errors = validate_post_file(post)

            self.assertIn("body contains placeholder text", errors)

    def test_backtick_fenced_block_with_literal_tilde_fence_does_not_fail(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            post = self.write_file(
                repo,
                "mixed-fence-example.md",
                """
                ---
                title: Mixed Fence Example
                slug: mixed-fence-example
                tags: python
                domain: example.hashnode.dev
                ---

                The code sample below includes a literal tilde fence marker:

                ```md
                ~~~
                [[fill-me]]
                ```

                The placeholder token is inside the backtick-fenced code example.
                """,
            )

            errors = validate_post_file(post)

            self.assertNotIn("body contains placeholder text", errors)
            self.assertEqual(errors, [])

    def test_tilde_fenced_code_block_with_placeholder_tokens_does_not_fail(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            post = self.write_file(
                repo,
                "tilde-fenced-example.md",
                """
                ---
                title: Tilde Fenced Example
                slug: tilde-fenced-example
                tags: python
                domain: example.hashnode.dev
                ---

                The example below uses tilde fences:

                ~~~jinja
                [[fill-me]]
                {{ user.name }}
                ~~~

                The post should not fail because the tokens are part of code.
                """,
            )

            errors = validate_post_file(post)

            self.assertNotIn("body contains placeholder text", errors)
            self.assertEqual(errors, [])

    def test_indented_code_block_with_placeholder_tokens_does_not_fail(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            post = self.write_file(
                repo,
                "indented-code-example.md",
                """
                ---
                title: Indented Code Example
                slug: indented-code-example
                tags: python
                domain: example.hashnode.dev
                ---

                The following indented example shows draft-like tokens as literals:

                    [[fill-me]]
                    {{ user.name }}

                These lines are example code, not unfinished article content.
                """,
            )

            errors = validate_post_file(post)

            self.assertNotIn("body contains placeholder text", errors)
            self.assertEqual(errors, [])

    def test_later_line_in_indented_code_block_with_placeholder_tokens_does_not_fail(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            post = self.write_file(
                repo,
                "indented-code-later-line.md",
                """
                ---
                title: Indented Code Later Line
                slug: indented-code-later-line
                tags: python
                domain: example.hashnode.dev
                ---

                The example below spans multiple indented code lines:

                    print("hello")
                    [[fill-me]]

                The draft marker appears only inside example code.
                """,
            )

            errors = validate_post_file(post)

            self.assertNotIn("body contains placeholder text", errors)
            self.assertEqual(errors, [])

    def test_standalone_example_line_with_surrounding_explanation_does_not_fail(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            post = self.write_file(
                repo,
                "standalone-example.md",
                """
                ---
                title: Standalone Example Line
                slug: standalone-example-line
                tags: python
                domain: example.hashnode.dev
                ---

                The next line is an example token for readers to customize:

                {{ project.slug }}

                Replace it in your own app configuration and keep reading.
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
