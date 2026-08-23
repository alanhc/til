# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 內容審查（這是公開網站）

**這個 repo 是公開的，push 到 `main` 就是發佈。** 沒有「先 commit、之後再挑時間手動發佈」的緩衝，
所以敏感內容的檢查必須在 push 之前做完。

`.githooks/pre-push` 會先跑一道**機密關鍵字掃描**（掃這次要推的新增行，比對
`.githooks/secret-patterns.txt` 與本機的 `secret-patterns.local.txt`），命中就中止 push 並列出
`檔案:行號`。誤判就到 `.githooks/secret-allow.txt` 加例外並註明原因。**那道掃描只認得清單上的字，
判斷力還是在這一節。**

寫入或改寫 `docs/` 時，預設就要做去識別化，不用等人提醒；事後在回覆裡說明哪幾處做了處理即可。

- **不寫廠商專屬的識別細節**：非公開的原始碼樹路徑、內部檔名、函式名與呼叫順序、log prefix、
  內部工具與 build 步驟。
- **改用通用層級敘述**：講「BL2 的平台初始化職責」而不是某家的具體函式名。技術價值幾乎不會流失。
- **不指路**：不要寫「最準的來源是某某內部 source／某某 pack 工具」——指出非公開答案在哪裡，
  本身就是內部知識的證據。
- **不用暗示職務經驗的措辭**：「內部 review」「公司內部流程」「內部可驗」。
- **點名客戶、專案代號、未公開產品資訊**：發現就明講並建議中性化，不要默默保留、也不要默默刪掉
  （那是作者的內容，由他決定）。
- **例外：查證後真的公開的，就正常寫並附來源連結**（上游 coreboot、AOSP、u-boot、LineageOS
  device tree 等）。**先查證再決定刪或標**，不要把公開資訊也一起抹掉。

判斷標準是觀感，不是免責聲明——標「[推論]／未經官方核對」對作者沒有保護力。

改文章時連 `docs/0.map/` 的 index 與 glossary 一起改，那裡常複製同樣的名詞。
若敏感內容已經 push：剛推的用 `git commit --amend` + `git push --force-with-lease`；
已隔數個 commit 的要衡量效益（舊 commit 仍可用 SHA 從 GitHub 取得，要真的清掉得找 GitHub Support）。

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
- Hosted on GitHub Pages at https://alanhc.github.io/til/
- Organization: alanhc
- Base URL: /til/
- **Deploys automatically on push to `main`** via `.github/workflows/deploy.yml`,
  which runs `yarn lint:md` → `yarn build` → `actions/deploy-pages`.
  There is no manual deploy step — pushing to `main` publishes the site.
- A `yarn deploy` script still exists in package.json but is legacy: it runs
  `docusaurus deploy` (pushes to a `gh-pages` branch), which is not how the site
  is served anymore. Don't use it.
- `git push` is gated by a pre-push hook running `yarn preflight`
  (`yarn lint:md && yarn build`). Bypass with `--no-verify` only if you mean it.

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

本機補充（若存在，內容不進版控）：@.claude/context.local.md
