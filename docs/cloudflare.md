cloudflared tunnel create app-tunnel
sudo vim ~/.cloudflared/config.yml

```
tunnel: <你的 Tunnel ID>
credentials-file: /home/你的使用者/.cloudflared/<你的 Tunnel ID>.json

ingress:
  - hostname: app.0xfanslab.com
    service: http://localhost:3000
  - service: http_status:404
```
cloudflared tunnel route dns app-tunnel app.0xfanslab.com