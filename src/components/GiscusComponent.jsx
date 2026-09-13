import React, { useEffect } from 'react';

export default function GiscusComponent() {
  useEffect(() => {
    // 避免重複插入 script
    if (document.getElementById('giscus-script')) return;

    const script = document.createElement('script');
    script.src = 'https://giscus.app/client.js';
    script.setAttribute('data-repo', 'alanhc/til');
    script.setAttribute('data-repo-id', 'R_kgDOM9zAcQ');
    script.setAttribute('data-category', 'General');
    script.setAttribute('data-category-id', 'DIC_kwDOM9zAcc4Cx0hz');
    script.setAttribute('data-mapping', 'pathname');
    script.setAttribute('data-strict', '0');
    script.setAttribute('data-reactions-enabled', '1');
    script.setAttribute('data-emit-metadata', '0');
    script.setAttribute('data-input-position', 'bottom');
    script.setAttribute('data-theme', 'preferred_color_scheme');
    script.setAttribute('data-lang', 'zh-TW');
    script.crossOrigin = 'anonymous';
    script.async = true;
    script.id = 'giscus-script';

    document.body.appendChild(script);
  }, []);

  // Giscus 的渲染容器
  return <div className="giscus" style={{ marginTop: '2rem' }} />;
}
