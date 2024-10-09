---
title: 20211027-虛擬人課堂筆記3-unity-facecapture
date: 2021-10-27
tags:
  - unity
  - medium
  - select
---

去上禮拜[ReadyPlayerMe](https://readyplayer.me/)下載glb模型檔
![](https://i.imgur.com/FWWnEgg.png)

1.  打開Blender，按右鍵刪除方塊

2\. File>import>.glb

3\. 選擇角色跟骨架

3\. 全選模型> File>Export>照著下面紅框做>Export(匯出)

![](https://i.imgur.com/nRAbmXM.png)


打開Unity(2020.3.20以上)>選擇3D project

window>package manager>+>Add package by name>com.unity.live-capture

點開sample>import

![](https://i.imgur.com/SfGFKsp.png)


到project區域>Assets>Samples>Live Camera>1.0.1>ARKit Face Sample>FaceCaptureSample.unity

![](https://i.imgur.com/hqBxXXO.png)

拖曳剛剛下載的模型.fbx到中間檔案區

把人物丟到Scene

點場景SampleHead>Inspector>SampleHead旁邊勾勾取消

點場景Camera>Inspector>Camera旁邊勾勾取消

Hierarchy>右鍵>Live Capture>Virtual Camera Actor

調整Camera視角

Hierarchy>我的模型>Incepetor>Add component>ARkit Face Actor

在Project>Create>Live Capture>ARKit Face Capture>Mapper

改名成myMapper

拖曳Hierarchy>我的模型拖曳到Project>點選Original Prefab

點一下myMapper，再點myMapper>拖曳Rig Prefab

![](https://i.imgur.com/VUuhLVQ.png)



拖曳模型的左眼右眼頭等等（參考下圖)

![](https://i.imgur.com/CaA0QZt.png)

Inspector>Add Render

然後點選Hierarchy>TakeRecorder>NewFaceDevice，照下面設定


![](https://i.imgur.com/dY8WLi5.png)


點選我的模型，把myMapper加入Inspector>Mapper


![](https://i.imgur.com/nAxNye7.png)


點選上面tab window>Live Capture>connections>Create Server>按下start

打開Iphone/Ipad，使用剛剛下載的Unity Face Capture


![](https://i.imgur.com/OOfz8L1.png)


點模型>Hierarchy>TakeRecorder ，點選點Inceptor>Live

看到模型隨著表情動拉🎉
![](https://i.imgur.com/PK2Jrue.png)


Ready Player me in Animaze(2021/10/28 WINDOWS ONLY)

從ReadyPlayerMe下載全身的.glb

Steam打開視窗 勾選工具，打開Animaze Editor

上方Assets>import 3D Objects

點模型，按右鍵>bundle

![](https://i.imgur.com/HiqDWFC.png)


回到Animax點+

![](https://i.imgur.com/HwY5Zqy.png)

Setting>Video Graphic>webcam旁邊選取connect to iphone

![](https://i.imgur.com/LcMqqSh.png)

可以開始做怪表情拉🎉

![](https://i.imgur.com/BLVMddV.png)

## Ref
- https://medium.com/@alanhc/%E8%99%9B%E6%93%AC%E4%BA%BA%E8%AA%B2%E5%A0%82%E7%AD%86%E8%A8%983-unity-facecapture-1f1ce16935d8