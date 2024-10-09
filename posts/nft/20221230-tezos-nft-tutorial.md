---
title: '使用smartpy撰寫tezos的nft程式'
date: '2022-12-30'
tag: ['notes', 'tezos']
---
## 撰寫nft合約
- 到 [smartpy ide](https://smartpy.io/ide) 輸入
```python
import smartpy as sp
FA2 = sp.io.import_template("FA2.py")

class NFT(FA2.FA2):
   pass

@sp.add_test(name="tests")
def test():
  jerry = sp.test_account("Jerry")
  tom = sp.test_account("Tom")
  admin = sp.address("tz1aV2DuPYXEK2mEVc4VBhP9o4gguFGxBky4")
  scenario = sp.test_scenario()
  scenario.h1("tutorial tests")
  nft = NFT(FA2.FA2_config(non_fungible=True), admin=admin, metadata= sp.utils.metadata_of_url("https://alanhc.github.io/nft/tezos-contract-example.json")
  scenario += nft
```
## 部署合約
- 更改admin為自己的地址、按下執行(左上)，並按下deploy contract
![](https://i.imgur.com/qLG96GS.png)
- 選擇測試鏈（ghostnet），並選擇estimate gas
![](https://i.imgur.com/tRzRx3P.png)
![](https://i.imgur.com/BEyHnAN.png)
- 將 token metadata (hex) 輸入，可使用 [string2hex](https://codebeautify.org/string-hex-converter)
    - 範例：(hex)`697066733a2f2f6261666b7265696833366d336434796662707974656c75766e7475706835787962777467786476796b736267796736366573343464726b34687179`，原文(string)：`ipfs://bafkreih36m3d4yfbpyteluvntuph5xybwtgxdvyksbgyg66es44drk4hqy`
![](https://i.imgur.com/5W1GHKA.png)
## 查看nft
- 到 [tzkt](https://ghostnet.tzkt.io/) >balance 查看是否有nft
![](https://i.imgur.com/vhoA46K.png)


## 參考
- https://learn.figment.io/tutorials/mint-nfts-on-tezos