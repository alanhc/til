// @ts-check
// `@type` JSDoc annotations allow editor autocompletion and type checking
// (when paired with `@ts-check`).
// There are various equivalent ways to declare your Docusaurus config.
// See: https://docusaurus.io/docs/api/docusaurus-config
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import {themes as prismThemes} from 'prism-react-renderer';
import {nativeIdealImageRemarkPlugin} from 'docusaurus-plugin-native-ideal-image';

// This runs in Node.js - Don't use client-side code here (browser APIs, JSX...)

const baseUrl = '/til/';

// plugin-sitemap 的 ignorePatterns 是拿 route.path 去比對，而 route.path 一律
// 含 baseUrl（例如 /til/docs/map），所以這裡的 pattern 必須自己帶上 /til 前綴，
// 不然一條都不會命中。
const withBaseUrl = (p) => `${baseUrl}${p.replace(/^\//, '')}`;

/** @type {import('@docusaurus/types').Config} */
const config = {
  title: 'alanhc\'s TIL',
  tagline: 'Today I Learned',
  favicon: 'img/favicon.ico',

  // Future flags, see https://docusaurus.io/docs/api/docusaurus-config#future
  future: {
    v4: true, // Improve compatibility with the upcoming Docusaurus v4
  },

  // Set the production url of your site here
  url: 'https://alanhc.github.io',
  // Set the /<baseUrl>/ pathname under which your site is served
  // For GitHub pages deployment, it is often '/<projectName>/'
  baseUrl,

  // GitHub pages deployment config.
  // If you aren't using GitHub pages, you don't need these.
  organizationName: 'alanhc', // Usually your GitHub org/user name.
  projectName: 'til', // Usually your repo name.
  trailingSlash: false,
  
  onBrokenLinks: 'throw',

  // Even if you don't use internationalization, you can use this field to set
  // useful metadata like html lang. For example, if your site is Chinese, you
  // may want to replace "en" with "zh-Hans".
  i18n: {
    defaultLocale: 'zh-Hant',
    locales: ['zh-Hant'],
  },

  presets: [
    [
      'classic',
      /** @type {import('@docusaurus/preset-classic').Options} */
      ({
        docs: {
          sidebarPath: './sidebars.js',
          // Please change this to your repo.
          // Remove this to remove the "edit this page" links.
          editUrl:
            'https://github.com/alanhc/til/tree/main/',
          remarkPlugins: [remarkMath, [nativeIdealImageRemarkPlugin, {}]],
          rehypePlugins: [rehypeKatex],
        },
        blog: {
          showReadingTime: true,
          feedOptions: {
            type: ['rss', 'atom'],
            xslt: true,
          },
          // Please change this to your repo.
          // Remove this to remove the "edit this page" links.
          editUrl:
            'https://github.com/alanhc/til/tree/main/',
          // Useful options to enforce blogging best practices
          onInlineTags: 'warn',
          onInlineAuthors: 'warn',
          onUntruncatedBlogPosts: 'warn',
        },
        theme: {
          customCss: './src/css/custom.css',
        },
        // sitemap 只放真正有內容的頁。tag / author / archive 這類導覽頁沒有獨立
        // 內容價值，搜尋頁更是 crawl trap；全部塞進 sitemap 只會稀釋整站評分。
        sitemap: {
          ignorePatterns: [
            '/search',
            '/docs/tags',
            '/docs/tags/**',
            '/blog/tags',
            '/blog/tags/**',
            '/blog/authors',
            '/blog/authors/**',
            '/blog/archive',
            // Docusaurus 預設範例文章，還沒換成真內容前不主動送索引
            '/blog/first-post',
          ].map(withBaseUrl),
        },
      }),
    ],
  ],

  plugins: [
    // 圖片壓縮成 webp/jpeg + responsive srcset + 低畫質 placeholder。
    // build/assets/images 原本 154MB（單張最大 11MB），全部直送讀者。
    // 註：官方 @docusaurus/plugin-ideal-image 只吃 <IdealImage> component，
    // 對 markdown 的 ![](...) 無效，所以改用這個有 remark plugin 的版本。
    [
      'docusaurus-plugin-native-ideal-image',
      {
        presets: {
          default: {
            formats: ['webp', 'jpeg'],
            sizes: [640, 1280, 1920],
            lqip: true,
          },
        },
        // dev 模式跳過壓縮，不然 hot reload 會很痛苦
        disableInDev: true,
      },
    ],
    // 舊網址導向。這些是從 git rename 史撈出來的，搬檔前的連結不要變 404。
    [
      '@docusaurus/plugin-client-redirects',
      {
        redirects: [
          {from: '/docs/Android/Android', to: '/docs/android'},
          {from: '/docs/Android/build', to: '/docs/android_build_project'},
          {from: '/docs/OpenBMC/openbmc', to: '/docs/BMC/openbmc'},
          {from: '/docs/OpenBMC/debug', to: '/docs/BMC/debug'},
          {from: '/docs/OpenBMC/hardwate', to: '/docs/BMC/hardware'},
          {from: '/docs/DSA/linked_list_101', to: '/docs/DSA/Linked_List/linked_list'},
          {from: '/docs/dsa_Boyer-Moore', to: '/docs/DSA/Boyer-Moore'},
          {from: '/docs/google_ai', to: '/docs/ai_google_ai'},
          {from: '/docs/google_ai_studio', to: '/docs/ai_google_ai_studio'},
          {from: '/docs/google_notebook_lm', to: '/docs/ai_google_notebook_lm'},
          {from: '/docs/n8n', to: '/docs/automation'},
          {from: '/docs/ubuntu/ppa_error', to: '/docs/ubuntu_ppa_error'},
          {from: '/docs/money/money', to: '/docs/money'},
          {from: '/docs/money/投資', to: '/docs/投資'},
          // 已移除的 Docusaurus 預設範例頁，一律導回知識地圖，不要留 404
          {
            to: '/docs/map',
            from: [
              '/docs/intro',
              '/docs/markdown-features',
              '/docs/tutorial-basics/markdown-features',
              '/docs/tutorial-basics/congratulations',
              '/docs/tutorial-basics/create-a-blog-post',
              '/docs/tutorial-basics/create-a-document',
              '/docs/tutorial-basics/create-a-page',
              '/docs/tutorial-basics/deploy-your-site',
              '/docs/tutorial-extras/manage-docs-versions',
              '/docs/tutorial-extras/translate-your-site',
              '/markdown-page',
            ],
          },
        ],
      },
    ],
    // 產生 llms.txt / llms-full.txt，讓 AI 抓得到整站筆記
    [
      'docusaurus-plugin-llms',
      {
        docsDir: 'docs',
        generateLLMsTxt: true,
        generateLLMsFullTxt: true,
        includeBlog: true,
      },
    ],
    // 點圖放大（medium-zoom）
    'docusaurus-plugin-image-zoom',
    // 離線可讀。plugin-pwa 在 dev 會自我停用，但 registerSw 仍會被 bundle 而噴
    // "Can't resolve '@theme/PwaReloadPopup'"，所以乾脆只在 production 掛上。
    process.env.NODE_ENV === 'production' && [
      '@docusaurus/plugin-pwa',
      {
        debug: false,
        offlineModeActivationStrategies: [
          'appInstalled',
          'standalone',
          'queryString',
        ],
        pwaHead: [
          {tagName: 'link', rel: 'icon', href: '/til/img/logo.svg'},
          {tagName: 'link', rel: 'manifest', href: '/til/manifest.json'},
          {tagName: 'meta', name: 'theme-color', content: '#2e8555'},
        ],
      },
    ],
  ],

  themeConfig:
    /** @type {import('@docusaurus/preset-classic').ThemeConfig} */
    ({
      // 點圖放大：排除 badge/emoji 這類 inline 小圖
      zoom: {
        selector: '.markdown :not(em) > img',
        background: {
          light: 'rgb(255, 255, 255)',
          dark: 'rgb(50, 50, 50)',
        },
      },
      // Replace with your project's social card
      algolia: {
        appId: '87B0UMILN7',
        apiKey: 'fa70277f5ba8a90d8a5642ade2b3f460',
        indexName: 'alanhcio',
        contextualSearch: true,
        insights: true,
      },
      image: 'img/docusaurus-social-card.jpg',
      navbar: {
        title: 'alanhc\'s TIL',
        logo: {
          alt: 'My Site Logo',
          src: 'img/logo.svg',
        },
        items: [
          {
            type: 'docSidebar',
            sidebarId: 'tutorialSidebar',
            position: 'left',
            label: '筆記',
          },
          {to: '/blog', label: 'Blog', position: 'left'},
          { type: 'search', position: 'right' },
          {
            href: 'https://alanhc.github.io',
            label: 'Homepage',
            position: 'right',
          },
        ],
      },
      footer: {
        style: 'dark',
        links: [
          {
            title: '筆記',
            items: [
              {
                label: '知識地圖',
                to: '/docs/map',
              },
            ],
          },
          {
            title: 'Social Links',
            items: [
              {
                label: 'LinkedIn',
                href: 'https://www.linkedin.com/in/alanhc316/',
              },
              {
                label: 'GitHub',
                href: 'https://github.com/alanhc',
              },
              {
                label: 'Threads',
                href: 'https://www.threads.net/@alanhc316',
              },
            ],
          },
          {
            title: 'More',
            items: [
              {
                label: 'Blog',
                to: '/blog',
              },
            ],
          },
        ],
        copyright: `Copyright © ${new Date().getFullYear()} alanhc.`,
      },
      prism: {
        theme: prismThemes.github,
        darkTheme: prismThemes.dracula,
      },
    }),
   themes: ['@docusaurus/theme-mermaid'],
  // In order for Mermaid code blocks in Markdown to work,
  // you also need to enable the Remark plugin with this option
  markdown: {
    mermaid: true,
    hooks: {
      onBrokenMarkdownLinks: 'throw',
    },
  },
};

export default config;
