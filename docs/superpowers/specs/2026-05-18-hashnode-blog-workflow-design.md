# Hashnode Blog Workflow Design

Date: 2026-05-18
Status: Approved

## Goal

Create a lightweight GitHub-backed writing and publishing workflow for Hashnode where the user can think in Chinese, collaborate conversationally, and publish polished English posts only after an explicit release instruction.

## Scope

This design covers:

- content collaboration rules
- repository shape
- publication trigger rules
- Hashnode integration strategy
- validation strategy

This design does not cover:

- implementing the repository scaffolding
- building custom Hashnode API publishing logic
- analytics, newsletter, or multi-platform syndication

## Users And Audience

Primary writer:

- the user, speaking informally in Chinese

Target readers:

- developers
- technical enthusiasts

## Core Workflow

The default workflow is:

1. The user shares ideas in Chinese, either as loose notes or a structured outline.
2. The assistant extracts the topic, central argument, and likely article shape.
3. The assistant drafts an English candidate post in a voice optimized for opinionated technical essays.
4. The assistant fills in publication metadata, including title, summary, slug, and tags.
5. The post remains unpublished unless the user gives an explicit release instruction such as `发这篇`, `发布`, or `post it`.
6. After an explicit release instruction, the assistant writes the Markdown file into the repository and pushes it to GitHub.
7. Hashnode's official GitHub integration detects the new or updated file and publishes the post.

## Publication Strategy

Recommended strategy:

- use Hashnode's official GitHub integration as the publication mechanism
- do not use a custom GitHub Action as the primary publishing path
- allow GitHub Actions only for validation and quality checks

Reasons:

- lower maintenance than a custom API publishing pipeline
- aligned with Hashnode's documented frontmatter and file-based workflow
- easier to update posts by changing the same Markdown source
- fewer moving parts and fewer credentials to maintain

## Collaboration Rules

Default collaboration rules:

- the user speaks Chinese
- the assistant writes publishable English
- the default article style is an opinion-led technical essay
- article length is determined by the material, with medium-length posts as the default tendency
- the assistant may ask follow-up questions, but only when they materially improve the article
- the assistant should stop weak or underdeveloped ideas from being published

Release gate:

- no content is published unless the user explicitly instructs release
- normal brainstorming, drafting, summarizing, or saving a candidate post is not a release instruction

Non-release phrases include examples such as:

- `先存着`
- `先整理`
- `先别发`

## Repository Design

The repository should act as a content source repository, not as a full blog engine.

Planned structure:

- root-level article `*.md` files intended for Hashnode publishing
- `templates/` for reusable article templates
- `scripts/` for helper utilities such as validation
- `.github/workflows/` for validation-only workflows
- `docs/` for process documents and operating rules
- `README.md` for a concise explanation of how writing and publishing works

Implementation note:

- current Hashnode GitHub publishing expects Markdown posts in the repository root rather than a nested `posts/` directory
- root-level Markdown should therefore be treated cautiously and reserved for article files that are intentionally prepared for Hashnode

## Content Model

Each article should be stored as a standalone Markdown file with Hashnode-compatible frontmatter.

Expected metadata fields include:

- title
- slug
- tags
- brief or summary fields required by the active Hashnode format
- publication state fields only if needed by Hashnode integration settings

The exact frontmatter schema should be validated against current Hashnode documentation during implementation.

## Assistant Responsibilities

For each publishable candidate, the assistant should be able to:

- identify whether the conversation contains a viable article
- choose an article angle and narrative shape
- draft a publishable English post from Chinese source material
- produce metadata suitable for Hashnode ingestion
- preserve strong original opinions when they improve authenticity
- reduce repetition, filler, and spoken-language noise from the source conversation

## Data Flow

The high-level data flow is:

1. conversational Chinese input
2. internal structuring and drafting
3. English Markdown candidate
4. metadata enrichment
5. explicit release confirmation
6. repository write
7. GitHub push
8. Hashnode sync and publish

## Error Handling

Potential failure cases and required behavior:

- If the content is not mature enough, the assistant should refuse release and explain what is missing.
- If Hashnode frontmatter requirements change, validation should fail before publish.
- If GitHub push fails, the assistant should preserve the local Markdown and report the failure clearly.
- If Hashnode sync fails after push, the assistant should diagnose whether the issue is metadata, integration setup, or repository state.
- If the user's instruction is ambiguous, the assistant should not treat it as a release command.

## Validation Strategy

Validation should happen before any publish-triggering push.

Recommended checks:

- required frontmatter fields exist
- slug format is valid
- title length is reasonable
- tags are present and normalized
- Markdown structure is syntactically sound
- obvious empty placeholders are rejected

Validation should be implemented via GitHub Actions or local helper scripts, but those checks should not replace the explicit user release gate.

## Success Criteria

This workflow is successful when:

- the user can think and discuss in Chinese without formatting overhead
- the assistant consistently converts source material into readable English posts
- publishing requires a clear, intentional release instruction
- the repository remains simple and maintainable
- Hashnode publishing works through the official GitHub integration rather than a fragile custom pipeline

## Implementation Boundary

Implementation should begin with:

1. repository scaffolding
2. README and operating rules
3. post template creation
4. validation workflow setup
5. sample post creation
6. Hashnode integration configuration guidance

The implementation phase should not start until the user reviews and approves this spec.
