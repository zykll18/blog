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
