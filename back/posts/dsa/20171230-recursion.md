---
title: 20171230-recursion
date: 2017-12-30
tags:
  - recursion
up:
  - "[[coding]]"
---
[#心得](https://www.facebook.com/hashtag/%E5%BF%83%E5%BE%97?__eep__=6&__cft__[0]=AZUi9EhO1AxvWuev5lfYQ9vH7eoB8iEMbdW9cLr_Av60-iI0R-KRUjCqlnrHK8Jcup_TLJQPnghkZmmSE34oonc79XBLjQaHA_drRrHWfTEEp_6tYObuga490V3AcvHD6crvaeAmGo5QmBDt8rgxbXvBo0f6MDRIMEhGBiWsbKfPRAmJoFlIj99BFlckWwMyXUw&__tn__=*NK-R) [#遞迴](https://www.facebook.com/hashtag/%E9%81%9E%E8%BF%B4?__eep__=6&__cft__[0]=AZUi9EhO1AxvWuev5lfYQ9vH7eoB8iEMbdW9cLr_Av60-iI0R-KRUjCqlnrHK8Jcup_TLJQPnghkZmmSE34oonc79XBLjQaHA_drRrHWfTEEp_6tYObuga490V3AcvHD6crvaeAmGo5QmBDt8rgxbXvBo0f6MDRIMEhGBiWsbKfPRAmJoFlIj99BFlckWwMyXUw&__tn__=*NK-R) [#無限呼叫](https://www.facebook.com/hashtag/%E7%84%A1%E9%99%90%E5%91%BC%E5%8F%AB?__eep__=6&__cft__[0]=AZUi9EhO1AxvWuev5lfYQ9vH7eoB8iEMbdW9cLr_Av60-iI0R-KRUjCqlnrHK8Jcup_TLJQPnghkZmmSE34oonc79XBLjQaHA_drRrHWfTEEp_6tYObuga490V3AcvHD6crvaeAmGo5QmBDt8rgxbXvBo0f6MDRIMEhGBiWsbKfPRAmJoFlIj99BFlckWwMyXUw&__tn__=*NK-R)

最近在寫遞迴的時候，發現常常會寫到當機(終止條件沒有設好)

最近想到個方法，

解決方法：

設一個變數去計算我到底呼叫他幾次，

若呼叫次數大於某個值，就回傳error，可避免無限呼叫。

![](https://i.imgur.com/HGMwQQh.jpg)
## Ref
- https://www.facebook.com/groups/363494050740833/permalink/387029151720656/

