---
title: "加入import別名讓import更好看"
date: "2023-08-26"
tag: ["blog"]
---
## 設定
- tsconfig.json
```js
{
	"compilerOptions": {
	...
	"baseUrl": ".",
	"paths": {
		"@/components/*": ["src/components/*"],
	...
	}
}
```
- 使用
```js
import Profile from "@/components/partial/Profile";
```
## ref
- https://nextjs.org/docs/app/building-your-application/configuring/absolute-imports-and-module-aliases