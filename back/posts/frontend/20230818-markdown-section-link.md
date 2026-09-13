---
title: '實作markdown section link'
date: '2023-08-18'
tag: ["blog"]
---
## Toc部分

```js
import markdownToc from 'markdown-toc';
const tocMarkdown = await markdownToc(markdownContent);
```
```js
<UnorderedList>
  {postData.tocMarkdown.json.map((heading: any) => (
    <ListItem key={heading.content}>
      <Link href={`#${heading.content}`}>
        {heading.content}
      </Link>
    </ListItem>
  ))}
</UnorderedList>
```
## 修改react markdown所需要的component
```js
function SectionBlock({ node, inline, className, children, id, ...props }: any) {
  const router = useRouter()
  const origin =
    typeof window !== 'undefined' && window.location.origin
      ? window.location.origin
      : '';
  const URL = `${origin}${router.asPath}`;
  const { onCopy, value, setValue, hasCopied } = useClipboard(URL + "#" + children);
  const [isHovering, setIsHovering] = useState(false);

  return (
    <Link href={`#${children}`} id={children} onClick={onCopy} onMouseEnter={() => setIsHovering(true)} onMouseLeave={() => setIsHovering(false)}>
      <Heading  {...props}>
        {children} {isHovering && "🔗"}
      </Heading>
    </Link>
  );
}
const components = {
  code: CodeBlock,
  h1: ({ node, ...props }: any) => <SectionBlock as="h1" size='xl' {...props} />,
  h2: ({ node, ...props }: any) => <SectionBlock as="h2" size='lg' {...props} />,
  h3: ({ node, ...props }: any) => <SectionBlock as="h3" size='md' {...props} />,
  h4: ({ node, ...props }: any) => <SectionBlock as="h4" size='sm' {...props} />,
  h5: ({ node, ...props }: any) => <SectionBlock as="h5" size='xs' {...props} />,
  a: ({ node, ...props }: any) => <Link  {...props} />,
};
```