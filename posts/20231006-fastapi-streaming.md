---
title: 20231006-fastapi-streaming
date: 2023-10-06
tags:
  - python
---
- main.py
```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import time
app = FastAPI()
def fake_data_streamer():
	for i in range(10):
	yield b'some fake data\n\n'
	time.sleep(0.5)

@app.get('/')
async def main():
	return StreamingResponse(fake_data_streamer(), media_type='text/event-stream')
@app.get("/video")
def main():
def iterfile(): #
with open("rick_roll.mp4", mode="rb") as file_like: #
yield from file_like #
return StreamingResponse(iterfile(), media_type="video/mp4")
```
- test.py
```python
import httpx
url = 'http://127.0.0.1:8000/'
with httpx.stream('GET', url) as r:
for chunk in r.iter_raw(): # or, for line in r.iter_lines():
print(chunk)
```
## Ref
