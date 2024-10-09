---
title: 超簡單! 一文理解如何使用私有大型語言模型LLM - Ollama＋Open WebUI篇
date: 2024-10-03
tags:
  - llm
updated: 2024-10-0316:01
up:
  - "[[llm]]"
---

## 步驟

![](https://i.imgur.com/jycGc1B.png)
1. 安裝 Docker Desktop
2. 使用wsl2
3. 使用 docker compose


## 2 使用WSL2
打開命令提示字元或Terminal，鍵入: `wsl --install`
## 3 使用 docker compose 安裝
### 3.1 安裝  NVIDIA Container Toolkit讓GPU可以使用
```shell
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg \
  && curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
    sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
    sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit

# Configure NVIDIA Container Toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker

# Test GPU integration
docker run --gpus all nvidia/cuda:11.5.2-base-ubuntu20.04 nvidia-smi
```

**後續步驟有影片可以對照參考：[200 秒內帶你進入私有大型語言模型LLM的世界 - Ollama + Open WebUI](https://youtu.be/2NGVNUjdoe0?si=-IQvk7y2x583ysY6)**
### 3.2.1 clone repo
`git clone https://github.com/valiantlynx/ollama-docker.git`
### 3.2.2 進入repo
`cd ollama-docker`
### 3.3 使用docker compose 跑服務
`docker-compose -f docker-compose-ollama-gpu.yaml up -d`
![](https://i.imgur.com/GJKhDG5.png)
看到這就跑起來啦
## 4 使用
### 4.1 下載模型
打開瀏覽器: http://localhost:8080/，點選左下角使用者>設定

![](https://i.imgur.com/jbDwuxS.png)

![](https://i.imgur.com/R6uBbGk.png)
請按照1. 2. 3. 順序點選，2可以先輸入使用微軟製作的小模型 phi3:3.8b
### 4.2 可以開始玩拉 
![](https://i.imgur.com/0Mipwj2.png)
### 5 關閉
`docker compose down`
—來自Alan Tseng發佈於Alan Tseng的沙龍 https://vocus.cc/article/669aba96fd89780001daf87d