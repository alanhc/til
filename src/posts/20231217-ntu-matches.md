---
title: 20231217-ntu-matches
date: 2023-12-17
tags:
  - vector_database
  - select
up:
  - "[[projects]]"
---
## 先請AI生成資料
### prompt
```text
請生成三組男女，各有各的自我介紹，僅說明自己，這個叫做content 請將這三組男女配對 用第一個使用者去敘述他配對的對象，這叫做mate 生成以上敘述的json資料，共會有六筆，有mate, content, gender, wish_gender欄位
```
### 回傳
```json
{
   "mate":"我心目中的理想伴侶是一個善良、聰明、有趣的人。她應該是一個有自己興趣愛好，能夠獨立思考和行動的人。她應該也是一個幽默風趣的人，能夠讓我的生活充滿樂趣。",
   "content":"我是一名 25 歲的男性軟體工程師。我喜歡閱讀、寫作和旅行。我是一個善良、聰明、有趣的人，希望找到一個和我一樣的人。",
   "gender":"male",
   "wish_gender":"female"
},
{
   "mate":"我心目中的理想伴侶是一個陽光、幽默、有責任心的人。他應該是一個熱愛生活，積極向上的人。他應該也是一個有責任心的人，能夠照顧好我和家庭。",
   "content":"我是一名 24 歲的女性護士。我喜歡烹飪、看電影和逛街。我是一個陽光、幽默、有責任心的人，希望找到一個和我一樣的人。",
   "gender":"female",
   "wish_gender":"male"
},
{
   "mate":"我心目中的理想伴侶是一個溫柔、體貼、有愛心的女性。她應該是一個善解人意，能夠包容我的人。她應該也是一個有愛心的女性，能夠與我一起去關愛他人。",
   "content":"我是一名 26 歲的男性律師。我喜歡運動、打球和聽音樂。我是一個溫柔、體貼、有愛心的人，希望找到一個和我一樣的人。",
   "gender":"male",
   "wish_gender":"female"
},
{
   "mate":"我心目中的理想伴侶是一個善良、聰明、有趣的人。她應該是一個有自己興趣愛好，能夠獨立思考和行動的人。她應該也是一個幽默風趣的人，能夠讓我的生活充滿樂趣。",
   "content":"我是一名 25 歲的女性護士。我喜歡烹飪、看電影和逛街。我是一個善良、聰明、有趣的人，希望找到一個和我一樣的人。",
   "gender":"female",
   "wish_gender":"male"
},
{
   "mate":"我心目中的理想伴侶是一個陽光、幽默、有責任心的人。他應該是一個熱愛生活，積極向上的人。他應該也是一個有責任心的人，能夠照顧好我和家庭。",
   "content":"我是一名 26 歲的男性軟體工程師。我喜歡運動、打球和聽音樂。我是一個陽光、幽默、有責任心的人，希望找到一個和我一樣的人。",
   "gender":"male",
   "wish_gender":"female"
}
```
## Vector Database
```python
%load_ext dotenv
%dotenv
import weaviate, os

# Connect with Weaviate Embedded
client = weaviate.connect_to_embedded(
    version="1.22.4",
    headers={
        "X-OpenAI-Api-Key": os.environ[
            "OPENAI_API_KEY"
        ],  # Replace with your inference API key
    },
)

client.is_ready()
```

```python
import weaviate.classes as wvc

if client.collections.exists("Dating"):
    client.collections.delete("Dating")
client.collections.create(
    name="Dating",
    vectorizer_config=wvc.Configure.Vectorizer.text2vec_openai(),  # wvc.Configure.Vectorizer.text2vec_cohere()
)

```
### Insert
```python
questions = client.collections.get("Dating")
questions.data.insert_many(data)
```
## search
```python
print(data[0]["mate"])
from weaviate.classes import Filter

response = questions.query.hybrid(
    data[0]["mate"],
    alpha=0.7,
    filters=(
        Filter("gender").equal(data[0]["wish_gender"])
        & (
            Filter("wish_gender").equal(data[0]["gender"])
            | Filter("wish_gender").equal("others")
        )
    ),
    limit=2,
)

for item in response.objects:
    print(item.properties)
```

```text
我心目中的理想伴侶是一個善良、聰明、有趣的人。她應該是一個有自己興趣愛好，能夠獨立思考和行動的人。她應該也是一個幽默風趣的人，能夠讓我的生活充滿樂趣。 {'mate': '我心目中的理想伴侶是一個善良、聰明、有趣的人。她應該是一個有自己興趣愛好，能夠獨立思考和行動的人。她應該也是一個幽默風趣的人，能夠讓我的生活充滿樂趣。', 'wish_gender': 'others', 'gender': 'female', 'content': '我是一名 25 歲的女性護士。我喜歡烹飪、看電影和逛街。我是一個善良、聰明、有趣的人，希望找到一個和我一樣的人。'} {'content': '我是一名 24 歲的女性護士。我喜歡烹飪、看電影和逛街。我是一個陽光、幽默、有責任心的人，希望找到一個和我一樣的人。', 'wish_gender': 'male', 'gender': 'female', 'mate': '我心目中的理想伴侶是一個陽光、幽默、有責任心的人。他應該是一個熱愛生活，積極向上的人。他應該也是一個有責任心的人，能夠照顧好我和家庭。'}
```
## Ref
- 
