https://source.android.com/docs/setup/start?hl=zh-tw#hardware-requirements

```
sudo apt-get install git-core gnupg flex bison build-essential zip curl zlib1g-dev libc6-dev-i386 x11proto-core-dev libx11-dev lib32z1-dev libgl1-mesa-dev libxml2-utils xsltproc unzip fontconfig
```

```
sudo apt-get install repo
```

```
mkdir aosp
cd aosp
```




```
~/aosp$ repo init --partial-clone -b android-latest-release -u https://android.googlesource.com/platform/manifest
Downloading Repo source from https://gerrit.googlesource.com/git-repo
remote: Total 9443 (delta 5029), reused 9443 (delta 5029)

Your identity is: alanhc <alanhc.tseng1999@gmail.com>
If you want to change this, please re-run 'repo init' with --config-name

repo has been initialized in /home/alanhc/aosp

```

```
.
├── TRACE_FILE
├── manifest.xml
├── manifests
├── manifests.git
└── repo

4 directories, 2 files
```
![alt text](<assets/截圖 2025-11-05 晚上7.24.58.png>)
![alt text](<assets/截圖 2025-11-05 晚上7.24.21.png>)
![[Pasted image 20251105192430.png]]
![[Pasted image 20251105192502.png]]

$ repo sync -c -j1 --fail-fast
Syncing: 100% (987/987), done in 41m53.124s
repo sync has finished successfully.

```
$m
#### build completed successfully (14:53 (mm:ss)) ####
```


```
# 1) 先裝建套件所需工具
sudo apt-get update
sudo apt-get install -y git devscripts equivs config-package-dev debhelper-compat golang curl

# 2) 抓 host 套件原始碼
git clone https://github.com/google/android-cuttlefish
cd android-cuttlefish

# 3) 一鍵建出並安裝 Debian 套件（會產生 cuttlefish-base_* 與 cuttlefish-user_*）
tools/buildutils/build_packages.sh

# 4) 依序安裝兩個套件（有相依問題會自動補）
sudo dpkg -i ./cuttlefish-base_*_*64.deb || sudo apt-get install -f
sudo dpkg -i ./cuttlefish-user_*_*64.deb || sudo apt-get install -f

# 5) 把自己加到需要的群組（套件會建立 cvdnetwork 群組與 udev 規則）
sudo usermod -aG kvm,cvdnetwork,render "$USER"

# 6) 建議重新開機，讓模組/udev 規則與群組生效
sudo reboot

```


```
which launch_cvd
launch_cvd --help
id -nG | grep -E '(^| )kvm( |$|.*cvdnetwork|.*render)' || echo "群組尚未生效，請重新登入/重開機"
ls -l /dev/kvm /dev/net/tun /dev/dri/renderD*  # 權限應分別屬於 kvm / cvdnetwork / render

```

https://source.android.com/docs/core/architecture/bootloader
![[Pasted image 20251022212501.png]]
## 詞彙表
- Kernel
	- _Android Common Kernel (ACK)_
	- _Generic Kernel Image (GKI) kernel_
- Vendor Native Development Kit (VNDK)
- Partitions


- Android 10, the root file system is no longer included in `ramdisk.img` and is instead merged into `system.img`