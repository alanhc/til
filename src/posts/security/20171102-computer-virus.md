---
title: 20171102-computer-virus
date: 2017-11-02
tags:
  - security
up:
  - "[[security]]"
---
[#心得](https://www.facebook.com/hashtag/%E5%BF%83%E5%BE%97?__eep__=6&__cft__[0]=AZXlbna_XcYPEnTgUyFmv6FgCIqAGu7QIsZOZsHZ8LrivarNzUGQvOPIRkej2uMiTT4hDLX-m08EQOR3GZUVcEK_sopLfRnMln4-TrkS5YONUVbzPGpCRDRLYAtP_Hz4yq9xMA51IKHwHtU_x4Nl5o3X7zB95bsxkbDCNoTrVCbkoNsGsZRER9-fsqwNk2B88Aw&__tn__=*NK-R) [#debug](https://www.facebook.com/hashtag/debug?__eep__=6&__cft__[0]=AZXlbna_XcYPEnTgUyFmv6FgCIqAGu7QIsZOZsHZ8LrivarNzUGQvOPIRkej2uMiTT4hDLX-m08EQOR3GZUVcEK_sopLfRnMln4-TrkS5YONUVbzPGpCRDRLYAtP_Hz4yq9xMA51IKHwHtU_x4Nl5o3X7zB95bsxkbDCNoTrVCbkoNsGsZRER9-fsqwNk2B88Aw&__tn__=*NK-R) [#電腦中毒](https://www.facebook.com/hashtag/%E9%9B%BB%E8%85%A6%E4%B8%AD%E6%AF%92?__eep__=6&__cft__[0]=AZXlbna_XcYPEnTgUyFmv6FgCIqAGu7QIsZOZsHZ8LrivarNzUGQvOPIRkej2uMiTT4hDLX-m08EQOR3GZUVcEK_sopLfRnMln4-TrkS5YONUVbzPGpCRDRLYAtP_Hz4yq9xMA51IKHwHtU_x4Nl5o3X7zB95bsxkbDCNoTrVCbkoNsGsZRER9-fsqwNk2B88Aw&__tn__=*NK-R)

這幾天遇到的問題，

我把問 [葉正聖 （Jeng-Sheng Yeh）](https://www.facebook.com/groups/363494050740833/user/100000084969969/?__cft__[0]=AZXlbna_XcYPEnTgUyFmv6FgCIqAGu7QIsZOZsHZ8LrivarNzUGQvOPIRkej2uMiTT4hDLX-m08EQOR3GZUVcEK_sopLfRnMln4-TrkS5YONUVbzPGpCRDRLYAtP_Hz4yq9xMA51IKHwHtU_x4Nl5o3X7zB95bsxkbDCNoTrVCbkoNsGsZRER9-fsqwNk2B88Aw&__tn__=-]K-R)老師教的做個簡單的小整理：

遇到的問題：

Codeblocks 無法compile

思考過程：

1. codeblocks按F9 compile ( fail )

error: cannot open the output file

2. 以cmd檢查是否可以用gcc直接compile檔案

存取被拒

3. 以系統參數更改output檔名的方式 ( succeed )

代表有人把untitle.exe *1* 鎖住了

4. 以 系統管理員 進入 procexp 找 " 沒有公司名子的檔案 "

找到有個Arduino_的檔案 **常駐** ，進去propreties找

**TCP/IP** 找是否有對外的*2* 通道( 有發現 )

結論：電腦中毒

有可能是這個電腦病毒看到Untitle的檔名就去保護他導致我檔案被鎖，無法存取(刪除、修改)。

解決方法：追查問題檔案目錄及檢查登入目錄程式是否有相關檔案存在，若有，直接在登入目錄修改檔名，使電腦病毒無法呼叫他需要的檔案。

*1*：原本的檔案叫untitle.c，codeblocks會自己把執行檔編譯成 your_name.exe

*2*：因為電腦病毒的特性可能有

1. 常駐在背景

2. 檔案很小

3. 藏在很隱密的地方

4. 名子跟正常很像但目錄不對

5. 開通道傳資料( TCP/IP )
## Ref
- https://www.facebook.com/groups/363494050740833/permalink/365709920519246/