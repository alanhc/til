# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a personal "Today I Learned" (TIL) documentation site built with Docusaurus 3.8.1, deployed to GitHub Pages at https://alanhc.github.io/til/. The site contains technical notes and learning resources primarily in Traditional Chinese (zh-Hant) with English support.

## Essential Commands

### Development
```bash
yarn install          # Install dependencies
yarn start           # Start local development server (with live reload)
yarn build           # Build static site to build/ directory
yarn serve           # Serve the production build locally
```

### Package Management
This project uses `yarn` as the primary package manager (lockfile: yarn.lock), though pnpm-lock.yaml also exists. When adding dependencies, use `yarn add <package>`.

### Content Management
```bash
yarn sync            # Sync docs to iCloud/Obsidian (personal workflow)
```

### Docusaurus Utilities
```bash
yarn swizzle         # Customize theme components
yarn clear           # Clear Docusaurus cache
```

## Architecture

### Content Structure
- **`/docs`**: Main documentation directory (100+ markdown files)
  - Auto-generated sidebar from folder structure (configured in sidebars.js)
  - Categories: Android, BMC, DSA, Embedded, Linux, and various topics (AI, career, productivity, investment)
  - Images stored in `/docs/assets` and `/docs/images`

### Custom Components & Theme
- **`/src/components/GiscusComponent.jsx`**: Comment system integration using Giscus
  - Configured for repo: alanhc/til
  - Uses GitHub Discussions as backend
  - Language: zh-TW, theme: preferred_color_scheme

- **`/src/theme/DocItem/Footer`**: Swizzled component that wraps original Docusaurus footer with Giscus comments
  - Pattern: Import original component, wrap with custom additions

### Configuration Files
- **`docusaurus.config.js`**: Main configuration
  - Bilingual site (zh-Hant default, English available)
  - Algolia search integration (App ID: 87B0UMILN7)
  - Math support via remark-math and rehype-katex
  - Mermaid diagrams enabled
  - GitHub edit links point to main branch

- **`sidebars.js`**: Sidebar auto-generated from docs folder structure

### Deployment
- Hosted on GitHub Pages
- Organization: alanhc
- Base URL: /til/
- Deploy with: `yarn deploy` or `USE_SSH=true yarn deploy`

## Development Patterns

### Adding Documentation
1. Create markdown files in `/docs` directory or subdirectories
2. Sidebar automatically updates based on folder structure
3. Use front matter for metadata (title, sidebar_position, etc.)
4. Images should be placed in `/docs/assets` or `/docs/images`

### Customizing Theme
- Use `yarn swizzle` to eject theme components into `/src/theme`
- Example: DocItem/Footer is already swizzled to add Giscus
- Always import and wrap original components rather than replacing entirely

### Math & Diagrams
- Math expressions supported via KaTeX (already configured)
- Mermaid diagrams supported (already configured)
- Use standard markdown code blocks with appropriate language identifiers

### Internationalization
- Default locale: zh-Hant (Traditional Chinese)
- Secondary locale: en (English)
- Configured in docusaurus.config.js i18n section

## Repository Context

- Main branch: `main` (used for PR base and edit links)
- GitHub org/user: alanhc
- Node.js requirement: >=18.0
- The site has Algolia search with facet filters for both languages
