https://gemini.google.com/app/342fdad855ec58d8?hl=zh-TW

adb reboot bootloader

fastboot flashing unlock

- Root 權限
	- **Magisk** 或 **KernelSU**
adb shell
su
insmod


```
sudo apt-get update
sudo apt-get install git-core gnupg flex bison build-essential zip curl zlib1g-dev libc6-dev-i386 x11proto-core-dev libx11-dev lib32z1-dev libgl1-mesa-dev libxml2-utils xsltproc unzip fontconfig
# 安裝 repo 工具
mkdir -p ~/.bin
PATH="${HOME}/.bin:${PATH}"
curl https://storage.googleapis.com/git-repo-downloads/repo > ~/.bin/repo
chmod a+rx ~/.bin/repo
```
