
在原本的ubuntu電腦買了一個新硬碟並灌windows後，發現grub被覆蓋掉了，導致無法進入ubuntu系統。
解決方法如下：
進入ubuntu，先找windows的分割區位置
```bash
sudo os-prober
```
會看到類似下面的輸出
```/dev/sda1:Windows 10:Windows:chain
```
接著更新grub
```bash
sudo update-grub
```
重新啟動後就可以看到grub的選單，並且可以選擇進入ubuntu或windows系統了。