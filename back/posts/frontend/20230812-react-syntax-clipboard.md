---
title: '使用react syntax highlighter及useClipboard強化程式碼區塊'
date: '2023-08-12'
tag: ['blog', 'react', 'chakra ui']
---
# react syntax highlighter + clipboard

1. 先去讀 postsDirectory 的markdownfile交給matter將markdown轉成object
  ```md
  ---
  title: Hello
  slug: home
  ---
  # Hello world!
  ```
結果
  ```js
  {
    content: '# Hello world!',
    data: { 
      title: 'Hello', 
      slug: 'home' 
    }
  }
  ```

  ```js
  const fullPath = path.join(postsDirectory, `${id}.md`);
  const fileContents = fs.readFileSync(fullPath, 'utf8');
  const matterResult = matter(fileContents);
  ...
  ```
2. 將matterResult的markdown語法顯示出來
  註：remarkGfm 讓他可以接受github的神奇markdown語法
  ```jsx
  import remarkGfm from 'remark-gfm'
  import ReactMarkdown from "react-markdown";
  ...
  <ReactMarkdown components={components} remarkPlugins={[remarkGfm]}>
      {postData.contentHtml}
  </ReactMarkdown>
  ```
3. 讓產生出來的程式需要有顏色的語法提示及複製功能
註：這裡是透過指定ReactMarkdown的components及使用chakra ui的useClipboard hook，如果codeblock有指定的程式語言就使用react-syntax-highlighter將他顯示語法提示
```jsx
import { Container, Heading, Link, Code, useClipboard, Flex, Button } from "@chakra-ui/react";
import { PrismAsync as SyntaxHighlighter } from "react-syntax-highlighter";


function CodeBlock({ node, inline, className, children, ...props }: any)  {
  const { onCopy, value, setValue, hasCopied } = useClipboard(children);
  const match = /language-(\w+)/.exec(className || '');
  return !inline && match ? (
    <Flex mb={2}>
      <SyntaxHighlighter
        style={darcula as { [key: string]: CSSProperties }}
        language={match[1]}
        PreTag="div"
        {...props}
      >
        {String(children).replace(/\n$/, '')}
      </SyntaxHighlighter>
      <Button ml={2} onClick={onCopy}colorScheme='blue' variant='outline'>{hasCopied ? "Copied!" : "Copy"}</Button>
    </Flex>
  ) : (
    <Flex mb={2}>
      <Code {...props} colorScheme="blackAlpha">
        {children}
      </Code>
      <Button ml={2} onClick={onCopy} colorScheme='blue' variant='outline'>{hasCopied ? "Copied!" : "Copy"}</Button>
    </Flex>
  );
}
const components = {
  code: CodeBlock,
};
```

![](https://hackmd.io/_uploads/ryNnKSrh3.png)

## ref:
- https://npm.io/package/gray-matter
- https://www.npmjs.com/package/react-markdown
- https://www.npmjs.com/package/remark-gfm