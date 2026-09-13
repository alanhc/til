# Repository Guidelines

## Project Structure & Module Organization
- `docs/` holds the primary knowledge base (Markdown/MDX). Group topics in folders; store images in `docs/assets/` or `static/` and link with relative paths.
- `blog/` contains dated posts with frontmatter (`title`, `date`, `slug`, `tags`).
- `src/` includes React customizations: `src/components/` shared blocks, `src/theme/` Docusaurus overrides, `src/css/` global styles, `src/pages/` ad-hoc routes, `src/data/` helper content.
- `static/` serves raw assets at the site root. `build/` is generated output—do not edit by hand.
- `sidebars.js`, `docusaurus.config.js`, and `docs/**/_category_.json` control navigation and metadata.

## Build, Test, and Development Commands
- Install: `yarn` (Node >=18 required).
- Local dev: `yarn start` (hot reload, watches docs/blog/src).
- Production build check: `yarn build` (fails on broken links; enables Markdown warnings).
- Preview built output: `yarn serve`.
- Cleanup caches: `yarn clear`.
- Deploy to GitHub Pages: `yarn deploy` (respects `USE_SSH` and `GIT_USER` env vars).
- `yarn sync` copies `docs/` to a local Obsidian path; run only if that path exists.

## Coding Style & Naming Conventions
- Prefer Markdown/MDX with clear frontmatter; use kebab-case filenames in `docs/` and `blog/`.
- Keep headings concise and ordered; favor short paragraphs and bullet lists.
- React/JS follows the existing style: import sorting is manual, semicolons omitted, and double quotes in config files—match surrounding code.
- For styles, extend `src/css/custom.css`; avoid inlining large CSS inside MDX.

## Testing Guidelines
- No automated test suite is configured. Validate changes with `yarn start` for live QA and `yarn build` to catch broken links/markdown before pushing.
- For new pages, manually click through nav/sidebar and search to confirm labels and paths resolve.

## Commit & Pull Request Guidelines
- Commit messages follow Conventional Commits seen in history (`type(scope): summary`, e.g., `docs(docs): Add GPTs documentation`). Use present tense and a scoped type when possible.
- Keep commits focused; include relevant assets in the same commit.
- PRs should summarize user-facing changes, list affected sections (`docs/*`, `blog/*`, `src/*`), and include screenshots/gifs for visual updates.
- Reference related issues when applicable and note any manual validation performed (`yarn build`, link checks).
