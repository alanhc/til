---
title: Hugging Face LLM
date: 2024-07-10
tags: 
updated: 2024-07-10
up:
  - "[[llm]]"
---
確認有 Hugging face token，記得要有read權限
- `run.py`
- 
```python
access_token = "hf_..." # 這裡放 Hugging face token

# pip install accelerate

from transformers import AutoTokenizer, AutoModelForCausalLM

import torch

  

tokenizer = AutoTokenizer.from_pretrained("google/gemma-2b-it", token=access_token)

model = AutoModelForCausalLM.from_pretrained(

    "google/gemma-2b-it",

    device_map="auto",

    torch_dtype=torch.bfloat16

    , token=access_token

)

  

input_text = "Write me a poem about Machine Learning."

input_ids = tokenizer(input_text, return_tensors="pt").to("cuda")

  

outputs = model.generate(**input_ids)

print(tokenizer.decode(outputs[0]))
```

```
<bos>Write me a poem about Machine Learning.

Machines, they weave and they learn,
From
```
## Ref
https://huggingface.co/google/gemma-2b/discussions/28
https://huggingface.co/google/gemma-2b-it