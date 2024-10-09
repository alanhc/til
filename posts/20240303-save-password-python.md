---
title: 20240303-save-password-python
date: 2024-03-03
tags:
  - python
  - security
updated: 2024-03-03
up:
---
使用 AES（對稱加密） + base64 
## 加密
```python
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Random import get_random_bytes

salt = get_random_bytes(16)
key_enc = PBKDF2(password, salt, dkLen=32)
cipher = AES.new(key_enc, AES.MODE_ECB)
ciphertext = cipher.encrypt(pad(plaintext.encode(), BLOCK_SIZE))
data[k] = base64.b64encode(ciphertext).decode()
with open("password.txt", "w") as f:
	json.dump(data, f)
```

## Ref
