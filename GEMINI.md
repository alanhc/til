# Project Overview

This is a personal "Today I Learned" (TIL) website built with Docusaurus. It serves as a knowledge base and blog for various topics, primarily in Chinese (zh-Hant) with some content in English.

The project is structured as a standard Docusaurus v3 website with a blog, documentation pages, and custom components. It uses Markdown for content and is configured to support KaTeX for math typesetting and Mermaid for diagrams.

## Key Technologies

*   **Framework:** [Docusaurus](https://docusaurus.io/)
*   **Language:** Markdown, MDX, JavaScript, React
*   **Styling:** CSS
*   **Search:** Algolia DocSearch
*   **Deployment:** GitHub Pages

## Building and Running

### Installation

Install the dependencies using `yarn`:

```bash
yarn
```

### Local Development

Run the local development server:

```bash
yarn start
```

This will open a browser window at `http://localhost:3000` with live reloading.

### Build

To create a production build, run:

```bash
yarn build
```

The static files will be generated in the `build` directory.

## Development Conventions

*   **Content:** The main content is located in the `docs` and `blog` directories.
*   **Structure:** The documentation sidebar is auto-generated from the file and directory structure in `docs`.
*   **Customization:** The site's theme can be customized by editing the files in `src/css` and `src/theme`. The main Docusaurus configuration is in `docusaurus.config.js`.
*   **Custom Scripts:** There is a custom `sync` script in `package.json` that copies the `docs` directory to an Obsidian vault. This is likely for personal use and not part of the main development workflow.
