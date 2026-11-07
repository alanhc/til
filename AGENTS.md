# Repository Guidelines

這是本 repo 給所有 coding agent 的單一指引來源（`CLAUDE.md` 只是轉指到這裡）。

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

---

## Deployment

- **Deploys automatically within ~5 minutes of a push to `main`**, built on a
  self-hosted Mac mini (not GitHub Actions). There is no manual deploy step —
  pushing to `main` publishes the site.
  - GitHub Pages serves the **`gh-pages` branch** (Settings → Pages → Deploy from a branch).
  - On the Mac mini, launchd (`~/Library/LaunchAgents/io.github.alanhc.til-deploy.plist`)
    runs `~/til-deploy/deploy.sh` every 5 minutes: if `origin/main` moved, it runs
    `yarn lint:md` → `yarn build` and pushes `build/` to `gh-pages` with a repo-scoped
    deploy key. Commits whose subject starts with `vault backup:` are skipped.
  - Logs: `~/til-deploy/deploy.log` (runs) and `~/til-deploy/last-build.log` (last build).
    Force a rebuild: `ssh macmini ~/til-deploy/deploy.sh --force`.
- `.github/workflows/deploy.yml` (Actions → `actions/deploy-pages`) is **disabled**
  (`gh workflow disable deploy.yml`); builds run on the self-hosted machine instead of
  GitHub Actions. To switch back: set Pages source to "GitHub Actions",
  `gh workflow enable deploy.yml`, and unload the Mac mini launchd job.
- Don't use `yarn deploy` (`docusaurus deploy`); `gh-pages` is owned by the Mac mini
  job, and two writers would race.
- `git push` is gated by a pre-push hook running `yarn preflight`
  (`yarn lint:md && yarn build`). Bypass with `--no-verify` only if you mean it.

---

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
- Deploy: none by hand — pushing to `main` publishes the site (see Deployment). `yarn deploy` is legacy; don't use it.
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

---

## Theme customization

Swizzled components under `src/theme/` must import and wrap the original component rather than replacing it entirely.

---

本機補充（若存在，內容不進版控）：@.claude/context.local.md
