# 資料中心叢集架構

資料中心以 **cluster（叢集）** 為單位組織大量伺服器，透過高速網路把多台機器組成一個運算/儲存整體。常見的節點角色分工如下：

cluster
- headnode
- compute node
- storage node

## 各節點角色

- **headnode（管理/登入節點）**：又稱 management node 或 login node，負責使用者登入、作業排程（job scheduler，如 Slurm/PBS）、監控與部署，是進入叢集的入口，通常不跑重負載運算。
- **compute node（運算節點）**：實際執行運算工作的主力機器，數量最多。通常無狀態（stateless），由 headnode 統一開機與派工。
- **storage node（儲存節點）**：提供共享儲存，常搭配分散式/平行檔案系統（如 Ceph、Lustre、NFS），讓各 compute node 共用同一份資料。

## 與 BMC 的關係

每個節點通常都內建 **BMC**，透過 out-of-band 管理網路（IPMI/Redfish）進行遠端開關機、感測器監控與韌體更新，讓管理者不必實體接觸機器即可維運整座叢集。
