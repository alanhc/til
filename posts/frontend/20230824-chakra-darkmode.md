---
title: "部落格暗黑模式"
date: "2023-08-24"
tag: ["blog", "chakra ui"]
---

1. 新增 theme.ts

```js
import { extendTheme, type ThemeConfig } from "@chakra-ui/react";

// 2. Add your color mode config

const config: ThemeConfig = {
  initialColorMode: "light",

  useSystemColorMode: false,
};

// 3. extend the theme

const theme = extendTheme({ config });

export default theme;
```

2. 新增\_document.tsx

```js
import { ColorModeScript } from "@chakra-ui/react";
import theme from "./theme";
```
render的部分：
```js
export default class Document extends NextDocument {
	<Html >
	...
          <ColorModeScript initialColorMode={theme.config.initialColorMode} />
          <Main />
	...
    );
  }
}
```

3. 新增切換按鈕

```js
const { colorMode, toggleColorMode } = useColorMode()
...
return (
...
<Button onClick={toggleColorMode}>
        Toggle {colorMode === 'light' ? 'Dark' : 'Light'}
</Button>

)

```

## ref

- https://chakra-ui.com/docs/styled-system/color-mode
