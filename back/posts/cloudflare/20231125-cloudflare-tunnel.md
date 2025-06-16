---
title: 20231125-cloudflare-tunnel
date: 2023-11-25
tags:
  - self-host
  - cloudflare
---
# 方式一 使用 GUI
## run service
e.g. `docker run -p 80:80 -d nginx`
## cloudflare 設定
https://dash.cloudflare.com/
dash > Zerotrust
![](https://i.imgur.com/C3QMcBJ.png)
![](https://i.imgur.com/h1tR17V.png)
![](https://i.imgur.com/DtY5i1w.png)
## 機器下載
註：windows 需要使用msi，用wsl 使用 docker會有問題
![](https://i.imgur.com/BVdQu81.png)
## 設定service位址

![](https://i.imgur.com/3swAtw9.png)

## 結果
訪問 前一個步驟設定的網址，成功🎉
![](https://i.imgur.com/QPcQh08.png)

# 方式2 使用 docker compose
TOKEN 為
```yaml
version: "3.9"  
services:  
nginx:  
image: nginx:latest  
expose:  
- 80  
cloudflared:  
image: cloudflare/cloudflared:latest  
command: tunnel run  
environment:  
- TUNNEL_TOKEN={TOKEN}
```
public host 設定 
`docker-compose up -d`
## Ref
