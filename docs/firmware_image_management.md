

QA 在 XTS 期間可能要image，但一個專案無時無刻要有人上code，要怎麼去透過自動化機制去管理，這就是 會有正式image可以比較嚴謹給QA使用以及用於提前找出問題讓 system integration team 在正式image 前就發現問題
因此 firmware image 會有分成 正式與非正式

你描述的其實正好對應到幾個成熟的軟體工程概念,大公司(包含 FAANG)都有對等的做法。核心對照如下。

**1. Release Channels(發布通道)—最直接的對應**
你講的「正式 vs 非正式 image」就是 release channel 的概念。最經典是 Google Chrome 的四通道:Canary → Dev → Beta → Stable。越前面越新、越不穩定、給內部/早期測試找問題;越後面越嚴謹、給正式驗證。你的情境:

- 非正式 image ≈ Canary / Nightly build,給 system integration team 提前踩雷
- 正式 image ≈ Beta / RC(Release Candidate)/ Stable,才交給 QA 做 XTS 這種嚴謹驗證

**2. Build Promotion / Artifact Promotion(建置晉升)**
自動化管理的關鍵機制。同一個 build artifact 不重新編譯,而是「一路晉升」通過各個 gate:通過自動測試 → 晉升成候選 → 通過整合測試 → 晉升成正式 image。這保證「QA 拿到的正式 image」和「之前測過的」是位元層級相同的東西(build once, promote many)。CI/CD pipeline(Jenkins、GitLab CI 等)就是幹這個的。

**3. Nightly Build + Trunk-Based Development**
「一個專案無時無刻要有人上 code」對應的是持續整合。Google、Meta 都用 trunk-based development + 每日/每晚自動出 build。原則是 **"master/trunk is always green"**——主線隨時可出 build,靠自動化擋掉壞的 commit,所以任何時刻都能產生一個非正式 image 給人測。

**4. Shift-Left Testing(測試左移)**
你說的「提前找出問題,讓 integration team 在正式 image 前就發現」就是 shift-left 的核心精神:把測試/整合往開發流程的前段推,越早發現 bug 修復成本越低。非正式 image 就是實現 shift-left 的載體。

**5. Release Candidate(RC)機制**
半導體/韌體業界最貼近你講的「正式 image」的正式術語。從 release branch 切出來、凍結功能(feature freeze)、只修 bug、經過完整 regression 才 sign-off 給 QA。這也解釋了為什麼要「分正式與非正式」:非正式來自 main/develop 分支的每日建置,正式來自被凍結的 release 分支。

**整理成一句話:** 你們自然演化出來的做法 = **release channels + build promotion pipeline + shift-left**,而讓兩種 image 能自動化管理的骨幹就是 **CI/CD + 分支策略(trunk 出 nightly、release branch 出 RC)**。

如果你想更具體,我可以幫你畫一張這套流程的 pipeline 圖(commit → nightly image → 整合測試 → RC → XTS 正式 image),或整理成一頁給團隊看的說明文件。要哪個?