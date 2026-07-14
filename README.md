# Website

This website is built using [Docusaurus](https://docusaurus.io/), a modern static website generator.

## Installation

```bash
yarn
```

## Local Development

```bash
yarn start
```

This command starts a local development server and opens up a browser window. Most changes are reflected live without having to restart the server.

## Build

```bash
yarn build
```

This command generates static content into the `build` directory and can be served using any static contents hosting service.

## Quality checks

- `yarn lint:md` — Markdown lint (only rules that catch broken Markdown; config in `.markdownlint.jsonc`).
- `yarn preflight` — runs `lint:md` + `build`; the same checks CI runs before deploy.

### Pre-push hook (one-time setup)

A versioned git hook in `.githooks/` runs `yarn preflight` before every push so
broken links/build errors are caught locally instead of failing CI. Enable it
once per clone:

```bash
git config core.hooksPath .githooks
```

Bypass for a single push with `git push --no-verify`.

## Deployment

Using SSH:

```bash
USE_SSH=true yarn deploy
```

Not using SSH:

```bash
GIT_USER=<Your GitHub username> yarn deploy
```

If you are using GitHub pages for hosting, this command is a convenient way to build the website and push to the `gh-pages` branch.
