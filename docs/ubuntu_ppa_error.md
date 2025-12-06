
有時候會看到類似
```
https://ppa.launchpadcontent.net/webupd8team/java/ubuntu noble Release 404 Not Found [IP: 185.125.190.80 443]
```

這時可以看 sources.list 裡面的 PPA 是否還存在，或是已經被移除/更名了。
```
grep -r webupd8team /etc/apt/sources.list.d/ /etc/apt/sources.list
```

再更新一次應該就可以了
```
sudo apt update

```
