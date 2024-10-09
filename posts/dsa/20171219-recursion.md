---
title: 20171219-recursion
date: 2017-12-19
tags:
  - recursion
up:
  - "[[coding]]"
---
[#心得](https://www.facebook.com/hashtag/%E5%BF%83%E5%BE%97?__eep__=6&__cft__[0]=AZWzwA7_EE8Lu_6n-_UF_2L4gT4ATh_NW2y2_m8yqNOtrKsUC_GDq6nlu87zIRv-ovrCT33tbUYmA9s_WInaULKkqTDB6N4ewNAHsu3o140la4X_irZgzHZdh2WphWhGBgfph1T33dtKfJ9Mq8R4wO4Pqe31FV1uV2iNgYYQeBm-PnO8eu5EHsA6Egx3Jf6DZz4&__tn__=*NK-R) [#除錯](https://www.facebook.com/hashtag/%E9%99%A4%E9%8C%AF?__eep__=6&__cft__[0]=AZWzwA7_EE8Lu_6n-_UF_2L4gT4ATh_NW2y2_m8yqNOtrKsUC_GDq6nlu87zIRv-ovrCT33tbUYmA9s_WInaULKkqTDB6N4ewNAHsu3o140la4X_irZgzHZdh2WphWhGBgfph1T33dtKfJ9Mq8R4wO4Pqe31FV1uV2iNgYYQeBm-PnO8eu5EHsA6Egx3Jf6DZz4&__tn__=*NK-R) [#遞迴](https://www.facebook.com/hashtag/%E9%81%9E%E8%BF%B4?__eep__=6&__cft__[0]=AZWzwA7_EE8Lu_6n-_UF_2L4gT4ATh_NW2y2_m8yqNOtrKsUC_GDq6nlu87zIRv-ovrCT33tbUYmA9s_WInaULKkqTDB6N4ewNAHsu3o140la4X_irZgzHZdh2WphWhGBgfph1T33dtKfJ9Mq8R4wO4Pqe31FV1uV2iNgYYQeBm-PnO8eu5EHsA6Egx3Jf6DZz4&__tn__=*NK-R) [#等比數列](https://www.facebook.com/hashtag/%E7%AD%89%E6%AF%94%E6%95%B8%E5%88%97?__eep__=6&__cft__[0]=AZWzwA7_EE8Lu_6n-_UF_2L4gT4ATh_NW2y2_m8yqNOtrKsUC_GDq6nlu87zIRv-ovrCT33tbUYmA9s_WInaULKkqTDB6N4ewNAHsu3o140la4X_irZgzHZdh2WphWhGBgfph1T33dtKfJ9Mq8R4wO4Pqe31FV1uV2iNgYYQeBm-PnO8eu5EHsA6Egx3Jf6DZz4&__tn__=*NK-R) [#PART1](https://www.facebook.com/hashtag/part1?__eep__=6&__cft__[0]=AZWzwA7_EE8Lu_6n-_UF_2L4gT4ATh_NW2y2_m8yqNOtrKsUC_GDq6nlu87zIRv-ovrCT33tbUYmA9s_WInaULKkqTDB6N4ewNAHsu3o140la4X_irZgzHZdh2WphWhGBgfph1T33dtKfJ9Mq8R4wO4Pqe31FV1uV2iNgYYQeBm-PnO8eu5EHsA6Egx3Jf6DZz4&__tn__=*NK-R)

情況：

想試著用遞迴的方式來檢查是否輸入兩數可以寫成等比數列。

Ex:

input： 125 5

output：true 125 25 5 1

input： 10 3

output：false

敘述：

原本一直出現 segmentation fault，後來加上紅色註解的下一行就過。

原因：

1234 / 321 = 3

3 / 321 = 0

0 /321 = 0

...

他會一直呼叫自己，導致無限呼叫(沒有回傳)

導致記憶體超出配置範圍

結論：

寫遞迴真的條件要想的很清楚，要不然會發生很可怕的結果![😂](https://static.xx.fbcdn.net/images/emoji.php/v9/t6f/2/16/1f602.png)

![](https://i.imgur.com/lhoPFft.jpg)

## Ref
- https://www.facebook.com/groups/363494050740833/permalink/382582158832022/