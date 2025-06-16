---
title: '將部落格加入sitemap功能'
date: '2023-08-17'
tag: ["blog"]
---
指令下：`pnpm add -D next-sitemap`
next.config.js新增
SITE_URL="https://example.com"
新增 next-sitemap.config.js
```js
/** @type {import('next-sitemap').IConfig} */
module.exports = {
  siteUrl:  'https://example.com',
  generateRobotsTxt: true, // (optional)
  // ...other options
}
```
在package.json > script
新增 `"postbuild": "next-sitemap"`
使用pnpm需要新增 `.npmrc`
```
enable-pre-post-scripts=true
```
在public/看到 sitemap.xml 、robots.txt、sitemap-0.xml成功🎉

去[http://www.google.com/webmasters/tools/](http://www.google.com/webmasters/tools/) 驗證網域
會要下載一個 googleOOOOO.js ，放在public

提交sitemap：`https://www.google.com/ping?sitemap=https://alanhc.github.io/sitemap.xml`
## ref
- https://www.npmjs.com/package/next-sitemap
