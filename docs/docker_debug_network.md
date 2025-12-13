
## 背景
我忘記ollama是跟哪個docker-compose去跑所以我先去檢查

```
docker inspect -f '{{json .NetworkSettings.Networks}}' ollama | jq docker inspect -f '{{json .NetworkSettings.Networks}}' n8n | jq docker inspect -f '{{json .NetworkSettings.Networks}}' open-webui | jq { "open-webui_default": { "IPAMConfig": null, "Links": null, "Aliases": [ "ollama", "ollama" ], "DriverOpts": null, "GwPriority": 0, "NetworkID": "1cfe167fb156ef45ad6eaeb87aa6d2dc96771a30a38dd8ae81860b47f2c6ca74", "EndpointID": "9e9d69ef8ccf2db163dd665b7b86e29ef6196b5f3de26e9769c5c1b8c3554a09", "Gateway": "172.20.0.1", "IPAddress": "172.20.0.2", "MacAddress": "62:09:20:3b:82:c1", "IPPrefixLen": 16, "IPv6Gateway": "", "GlobalIPv6Address": "", "GlobalIPv6PrefixLen": 0, "DNSNames": [ "ollama", "8eaa6f07c73f" ] } } { "n8n_default": { "IPAMConfig": null, "Links": null, "Aliases": [ "n8n", "n8n" ], "DriverOpts": null, "GwPriority": 0, "NetworkID": "11b0037a58a90c1943a219050e502bd9f9c29e170913035e8f0a250448fca17f", "EndpointID": "49b7e45e01efc3ee5ef334d0cc8fa930e0a1915fc37ee04e3a2e9f707fbc62dd", "Gateway": "172.19.0.1", "IPAddress": "172.19.0.2", "MacAddress": "da:09:74:e4:e8:f7", "IPPrefixLen": 16, "IPv6Gateway": "", "GlobalIPv6Address": "", "GlobalIPv6PrefixLen": 0, "DNSNames": [ "n8n", "b146ba4956b8" ] } } { "open-webui_default": { "IPAMConfig": null, "Links": null, "Aliases": [ "open-webui", "open-webui" ], "DriverOpts": null, "GwPriority": 0, "NetworkID": "1cfe167fb156ef45ad6eaeb87aa6d2dc96771a30a38dd8ae81860b47f2c6ca74", "EndpointID": "3bb710da086477263ac10125ed0ba5ab55183f89539881b228562b1024b087a7", "Gateway": "172.20.0.1", "IPAddress": "172.20.0.3", "MacAddress": "26:7d:2c:94:c4:43", "IPPrefixLen": 16, "IPv6Gateway": "", "GlobalIPv6Address": "", "GlobalIPv6PrefixLen": 0, "DNSNames": [ "open-webui", "8cb4dc565e4a" ] } }
```
發現 ollama 及 openwebui都在172.20.0
然後我印象之前是和openwebui一起設定
```
docker inspect open-webui --format '{{json .Config.Labels}}' | jq
```

```
docker inspect open-webui --format '{{json .Config.Labels}}' | jq
{
  "com.docker.compose.config-hash": "7ac5135e913eb6c9fa443470acad7d6a48786cdff0458a32445f4067109f79dc",
  "com.docker.compose.container-number": "1",
  "com.docker.compose.depends_on": "ollama:service_started:false",
  "com.docker.compose.image": "sha256:9173df40b9879b99cd5332d38ec966973f8c0ffb77dbafb2ec96caea2548a8d3",
  "com.docker.compose.oneoff": "False",
  "com.docker.compose.project": "open-webui",
  "com.docker.compose.project.config_files": "/home/alanhc/workspace/open-webui/docker-compose.yaml,/home/alanhc/workspace/open-webui/docker-compose.gpu.yaml",
  "com.docker.compose.project.working_dir": "/home/alanhc/workspace/open-webui",
  "com.docker.compose.service": "open-webui",
  "com.docker.compose.version": "2.40.3",
  "org.opencontainers.image.created": "2025-12-02T22:29:30.612Z",
  "org.opencontainers.image.description": "User-friendly AI Interface (Supports Ollama, OpenAI API, ...)",
  "org.opencontainers.image.licenses": "NOASSERTION",
  "org.opencontainers.image.revision": "6f1486ffd0cb288d0e21f41845361924e0d742b3",
  "org.opencontainers.image.source": "https://github.com/open-webui/open-webui",
  "org.opencontainers.image.title": "open-webui",
  "org.opencontainers.image.url": "https://github.com/open-webui/open-webui",
  "org.opencontainers.image.version": "main"
}
```

接著我去看設定

```
cd /home/alanhc/workspace/open-webui
docker compose -f docker-compose.yaml -f docker-compose.gpu.yaml config
name: open-webui
services:
  ollama:
    container_name: ollama
    deploy:
      resources:
        reservations:
          devices:
            - capabilities:
                - gpu
              driver: nvidia
              count: 1
    image: ollama/ollama:latest
    networks:
      default: null
    pull_policy: always
    restart: unless-stopped
    tty: true
    volumes:
      - type: volume
        source: ollama
        target: /root/.ollama
        volume: {}
  open-webui:
    build:
      context: /home/alanhc/workspace/open-webui
      dockerfile: Dockerfile
    container_name: open-webui
    depends_on:
      ollama:
        condition: service_started
        required: true
    environment:
      OLLAMA_BASE_URL: http://ollama:11434
      WEBUI_SECRET_KEY: ""
      WEBUI_URL: https://openwebui.0xfanslab.com
    extra_hosts:
      - host.docker.internal=host-gateway
    image: ghcr.io/open-webui/open-webui:main
    networks:
      default: null
    ports:
      - mode: ingress
        target: 8080
        published: "8080"
        protocol: tcp
    restart: unless-stopped
    volumes:
      - type: volume
        source: open-webui
        target: /app/backend/data
        volume: {}
networks:
  default:
    name: open-webui_default
volumes:
  ollama:
    name: open-webui_ollama
  open-webui:
    name: open-webui_open-web
```
再看看他的entrypoint在哪？
```
docker inspect open-webui --format 'Entrypoint={{json .Config.Entrypoint}} Cmd={{json .Config.Cmd}}'
Entrypoint=null Cmd=["bash","start.sh"]
```

我知道docker-compose file path: 

我要使用 caddy 當作對外入口這樣可以用token驗證的話
```
:8081 {

  # （可選）讓 OPTIONS preflight 直接過，避免某些前端跨域卡住
  @preflight method OPTIONS
  handle @preflight {
    respond 204
  }

  # Token 驗證：必須完全符合這個 header
  @authed header Authorization "Bearer {env.OLLAMA_PROXY_TOKEN}"

  handle @authed {
    reverse_proxy ollama:11434
  }

  handle {
    respond "Unauthorized" 401
  }
}

```

我去改docker-compose.yaml
```
services:
  ollama:
    volumes:
      - ollama:/root/.ollama
    container_name: ollama
    pull_policy: always
    tty: true
    restart: unless-stopped
    image: ollama/ollama:${OLLAMA_DOCKER_TAG-latest}
    environment:
      - OLLAMA_HOST=0.0.0.0:11434
    # 不要 ports，讓 ollama 本體不要直接對外

  # ✅ 新增：對外入口（帶 token 才能用）
  ollama-proxy:
    image: caddy:2
    container_name: ollama-proxy
    restart: unless-stopped
    depends_on:
      - ollama
    environment:
      - OLLAMA_PROXY_TOKEN=${OLLAMA_PROXY_TOKEN}
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile:ro
    ports:
      - "11435:8081"   # 對外用這個 port（之後也可掛網域）

  open-webui:
    build:
      context: .
      dockerfile: Dockerfile
    image: ghcr.io/open-webui/open-webui:${WEBUI_DOCKER_TAG-main}
    container_name: open-webui
    volumes:
      - open-webui:/app/backend/data
    depends_on:
      - ollama
    ports:
      - "8080:8080"
    environment:
      - 'WEBUI_URL=https://openwebui.0xfanslab.com'
      - 'OLLAMA_BASE_URL=http://ollama:11434'
      - 'WEBUI_SECRET_KEY='
    extra_hosts:
      - host.docker.internal:host-gateway
    restart: unless-stopped

volumes:
  ollama: {}
  open-webui: {}

```


產生密鑰：`openssl rand -base64 32

在.env加上`OLLAMA_PROXY_TOKEN=<前面產生的token>`

```
docker compose -f docker-compose.yaml -f docker-compose.gpu.yaml up -d
```
測試ollama有沒有用gpu
```
docker inspect ollama --format '{{json .HostConfig.DeviceRequests}}' | jq

```

測試直接打
```
curl -i http://127.0.0.1:11435/api/tags
HTTP/1.1 401 Unauthorized
Content-Type: text/plain; charset=utf-8
Server: Caddy
Date: Sat, 13 Dec 2025 07:37:21 GMT
Content-Length: 12

Unauthorized
```

帶入token
```
curl -i http://127.0.0.1:11435/api/tags \
  -H "Authorization: Bearer <token>"
HTTP/1.1 200 OK
Content-Length: 1030
Content-Type: application/json; charset=utf-8
Date: Sat, 13 Dec 2025 07:38:06 GMT
Via: 1.1 Caddy
```