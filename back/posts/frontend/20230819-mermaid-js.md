---
title: '讓部落格可以顯示markdown的流程圖'
date: '2023-08-19'
tag: ["blog", "mermaid js"]
---
code如下

```
mermaid
graph TD;
    A-->B;
    A-->C;
    B-->D;
    C-->D;
```



## 修改CodeBlock

```js
function CodeBlock({ language, node, inline, className, children, ...props }: any) {
  const { onCopy, value, setValue, hasCopied } = useClipboard(children);
  const match = /language-(\w+)/.exec(className || '');
  
  if (inline || !match) { //只有一行的code
    return (<Flex mb={2}>
      <Code {...props} colorScheme="blackAlpha">
        {children}
      </Code>
      <Button ml={2} onClick={onCopy} colorScheme='blue' variant='outline'>{hasCopied ? "Copied!" : "Copy"}</Button>
    </Flex>)
  } else if (match![1] ==='mermaid') {
    return (<Box className='mermaid'>{children}</Box>)
  } else {
    return (
      <Flex mb={2}>
        <SyntaxHighlighter
          style={darcula as { [key: string]: CSSProperties }}
          language={match![1] }
          PreTag="div"
          {...props}
        >
          {String(children).replace(/\n$/, '')}
        </SyntaxHighlighter>
        <Button ml={2} onClick={onCopy} colorScheme='blue' variant='outline'>{hasCopied ? "Copied!" : "Copy"}</Button>
      </Flex>
    )
  }
}
```
## render新增
```js
<Script
  id="mermaidjs"
  type="module"
  strategy="afterInteractive"
  dangerouslySetInnerHTML={{
    __html: `
    import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
    mermaid.initialize({ startOnLoad: true });
    mermaid.contentLoaded();
    `,
  }}
/>
```
## 成功
以下圖是使用 mermaidjs渲染出來的
```mermaid
graph TD;
    A-->B;
    A-->C;
    B-->D;
    C-->D;
```
- https://github.blog/2022-02-14-include-diagrams-markdown-files-mermaid/
- https://nextjs.org/docs/pages/api-reference/components/script
- http://mermaid.js.org/