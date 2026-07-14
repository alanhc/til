# aisuite

aisuite 是 Andrew Ng 團隊開源的 Python 套件，提供統一介面來呼叫多家 LLM 供應商的 API，讓你用一致的寫法切換不同模型。

- 以類似 OpenAI SDK 的介面封裝多家供應商（如 OpenAI、Anthropic、Google 等）。
- 用 `provider:model` 字串指定模型，方便比較與切換。
- 定位在讓開發者、研究者容易跨供應商實驗。

## 範例
```python
import aisuite as ai

client = ai.Client()
response = client.chat.completions.create(
    model="openai:gpt-4o",   # 換成 "anthropic:..." 即可切換供應商
    messages=[{"role": "user", "content": "Hello"}],
)
print(response.choices[0].message.content)
```

- 原始碼：https://github.com/andrewyng/aisuite
