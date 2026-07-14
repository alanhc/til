# 讓 Ollama 對區網/VPN 開放存取

預設 Ollama 只監聽本機（127.0.0.1）。將 `OLLAMA_HOST` 設為 `0.0.0.0` 可讓它監聽所有網路介面，方便同區網或 VPN 內其他裝置存取這台的 Ollama API。

```
export OLLAMA_HOST=0.0.0.0
ollama serve
```

> 注意：開放所有介面等於讓網路上可連到本機的裝置都能呼叫，請在受信任的網路或搭配防火牆使用。
