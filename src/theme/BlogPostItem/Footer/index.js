import React from 'react';
import OriginalFooter from '@theme-original/BlogPostItem/Footer';
import GiscusComponent from '@site/src/components/GiscusComponent';

export default function FooterWrapper(props) {
  return (
    <>
      <OriginalFooter {...props} />
      <GiscusComponent />
    </>
  );
}
