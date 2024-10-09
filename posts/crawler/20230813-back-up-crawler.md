---
title: '三種使用Python爬取網頁的方法'
date: '2023-08-13'
tag: ['notes', 'crawler']
---
## 第一版: 使用session慢慢爬
```python
s = requests.Session()
```
## 第二版: 使用python的並行處理功能
```python
import requests
import concurrent.futures
results = []
# 定義爬蟲任務
def fetch_url(url, session):
    try:
        response = session.get(url)
        try:
            return url, response.status_code, response.json()
        except:
            return url, response.status_code, {}

       
    except requests.RequestException as e:
        return url, None

def fetch(urls):
    with requests.Session() as session:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # 使用 map 函式來同時執行多個爬蟲任務
            results = executor.map(fetch_url, urls, [session] * len(urls))
    return results
```
## 第三版: 直接使用異步處理方式
```python
import asyncio
import aiohttp

async def fetch_url(session, url):
    try:
        async with session.get(url) as response:
            # 在這裡你可以對回應進行任何處理，例如解析HTML，提取資料等。
            # 這裡我們只回傳回應的狀態碼作為範例。
            try:
                data = await response.json()
                return url, response.status, data
            except:
                print("=======================================", url, response.status)
                return url, response.status, {}

    except aiohttp.ClientError as e:
        return url, None, {}
async def fetch_all(urls):
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_url(session, url) for url in urls]
        return await asyncio.gather(*tasks)

urls_courses = [
    "https://up.mcuosc.dev/courses/json?page="+str(i) for i in range(200)
]

loop = asyncio.get_event_loop()
results = loop.run_until_complete(fetch_all(urls_courses))
```
## link
- https://github.com/alanhc/back-up