---
title: "加入GA"
date: "2023-08-30"
tag: ["nextjs", "blog", "seo"]
---

https://analytics.google.com/analytics/web/ 裡面 拿到GA_MEASUREMENT_ID應該會是`G-{...}`



在_app.tsx 加入
```js
const GA_MEASUREMENT_ID = process.env.NEXT_PUBLIC_GOOGLE_ANALYTICS;
return (
<>
<Script
	src={`https://www.googletagmanager.com/gtag/js?id=${GA_MEASUREMENT_ID}`}
	strategy="afterInteractive"
	/>
	<Script id="google-analytics" strategy="afterInteractive">
	{`
	window.dataLayer = window.dataLayer || [];
	function gtag(){window.dataLayer.push(arguments);}
	gtag('js', new Date());
	gtag('config', '${GA_MEASUREMENT_ID}');
	`}
</Script>
```

## Ref
