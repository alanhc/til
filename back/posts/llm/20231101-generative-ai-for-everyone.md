---
title: 20231101-generative-ai-for-everyone
date: 2023-11-02
tags:
  - ai
  - llm
---
## What is Generative AI
![](https://i.imgur.com/Q877q0W.png)

![](https://i.imgur.com/8DpeAAb.png)

![](https://i.imgur.com/FhLUDBG.png)
- Supervised learning (labeling things)
![](https://i.imgur.com/fFv1p2L.png)
- 2010 - 2020: Large scale supervised learning
- LLM
	- How? supervised learning (A->B) 重複預測下一個word
![](https://i.imgur.com/d3JGgOK.png)
- 例子
	- 寫作：rewrite for clarity
	- 閱讀：有沒有在抱怨、情緒分析
	- 聊天：聊天機器人
- web search or LLM？
![](https://i.imgur.com/PIehfwc.png)

- LLM可能會錯，但回答比較精簡
	- web search有時會得到比較好的答案，但要花時間找到你要的資訊
## Generative AI Applications
![](https://i.imgur.com/ubs4shO.png)

![](https://i.imgur.com/ZblmQDs.png)
![](https://i.imgur.com/F1oNomh.png)
- setup
```python
import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")

def llm_response(prompt):
    response = openai.ChatCompletion.create(
        model='gpt-3.5-turbo',
        messages=[{'role':'user','content':prompt}],
        temperature=0
    )
    return response.choices[0].message['content']
```
- classify
```python
prompt = '''
    Classify the following review 
    as having either a positive or
    negative sentiment:

    The banana pudding was really tasty!
'''

response = llm_response(prompt)
print(response)
```

```python
all_reviews = [
    'The mochi is excellent!',
    'Best soup dumplings I have ever eaten.',
    'Not worth the 3 month wait for a reservation.',
    'The colorful tablecloths made me smile!',
    'The pasta was cold.'
]

all_reviews
classifications = []
for review in all_reviews:
    prompt = f'''
        Classify the following review 
        as having either a positive or
        negative sentiment. State your answer
        as a single word, either "positive" or
        "negative":

        {review}
        '''
    response = llm_response(prompt)
    classifications.append(response)

classifications
```


![](https://i.imgur.com/MoG5DoG.png)

![](https://i.imgur.com/VOdC3dn.png)

![](https://i.imgur.com/zbDvhYJ.png)


![](https://i.imgur.com/ranyh2o.png)

![](https://i.imgur.com/BSS1Rsx.png)
### Advance technologies: Beyond prompting
![](https://i.imgur.com/EeOJZiM.png)

![](https://i.imgur.com/kkk2PLP.png)

![](https://i.imgur.com/Zx9Yun9.png)



![](https://i.imgur.com/EoqwkuW.png)

![](https://i.imgur.com/Ysjf6Bj.png)

![](https://i.imgur.com/cBEfLR0.png)

![](https://i.imgur.com/wdyy3ov.png)


![](https://i.imgur.com/4uomkXV.png)

![](https://i.imgur.com/VTx5KBM.png)

![](https://i.imgur.com/HM0jMCS.png)

![](https://i.imgur.com/DVqNRPm.png)

![](https://i.imgur.com/dnGp4io.png)

![](https://i.imgur.com/qOxdVE0.png)


![](https://i.imgur.com/JiWy6ky.png)

![](https://i.imgur.com/g9sp9gj.png)

![](https://i.imgur.com/DYyC9xa.png)

![](https://i.imgur.com/RmNpxgS.png)

![](https://i.imgur.com/YVs5iOT.png)

![](https://i.imgur.com/kvfmIsI.png)
![](https://i.imgur.com/s5j8JfV.png)

![](https://i.imgur.com/It3c1bn.png)

![](https://i.imgur.com/TrH6LIS.png)
## Generative AI and Business

![](https://i.imgur.com/5D0R3mM.png)
![](https://i.imgur.com/HFkgbK4.png)
![](https://i.imgur.com/kdIdQEQ.png)


![](https://i.imgur.com/DVpSVlE.png)

![](https://i.imgur.com/Lsj5aN7.png)


![](https://i.imgur.com/KflQWmQ.png)

![](https://i.imgur.com/pXYSuAp.png)

![](https://i.imgur.com/JmJIRpE.png)

![](https://i.imgur.com/1Cfi4jx.png)

![](https://i.imgur.com/GXoksq0.png)

![](https://i.imgur.com/wxGGuZ9.png)

![](https://i.imgur.com/mt1VnDQ.png)

![](https://i.imgur.com/UVO7diU.png)

![](https://i.imgur.com/Zn99itX.png)

![](https://i.imgur.com/U1YRRv7.png)

![](https://i.imgur.com/IoTCqWQ.png)

![](https://i.imgur.com/LJgsS6D.png)

![](https://i.imgur.com/bNLHur3.png)

![](https://i.imgur.com/qX5bDqc.png)

![](https://i.imgur.com/evZTSK7.png)

![](https://i.imgur.com/vcFTHu7.png)

![](https://i.imgur.com/B0OxfFz.png)

## Genetative AI and Society

![](https://i.imgur.com/GZBqhzT.png)

![](https://i.imgur.com/cp5Jqld.png)


![](https://i.imgur.com/uQVir2J.png)

![](https://i.imgur.com/LoEnxmX.png)
![](https://i.imgur.com/kH5ueLs.png)

![](https://i.imgur.com/QJ8LZst.png)

![](https://i.imgur.com/lL6DjKd.png)

![](https://i.imgur.com/EkOSUOB.png)


![](https://i.imgur.com/i37ibIL.png)

![](https://i.imgur.com/8UUjY8A.png)

![](https://i.imgur.com/EFJcxZl.png)

![](https://i.imgur.com/puW6AYX.png)

- w3 meterials
	- [he economic potential of generative AI: The next productivity frontier](https://www.mckinsey.com/capabilities/mckinsey-digital/our-insights/the-economic-potential-of-generative-ai-the-next-productivity-frontier#introduction)
	- [GPTs are GPTs: An Early Look at the Labor Market Impact Potential of Large Language Models](https://arxiv.org/pdf/2303.10130.pdf)
	- [The Potentially Large Effects of Artificial Intelligence on Economic Growth (Briggs/Kodnani)](https://www.gspublishing.com/content/research/en/reports/2023/03/27/d64e052b-0f6e-45d7-967b-d7be35fabd16.html)
	- https://www.onetonline.org/



## Ref
- https://www.coursera.org/learn/generative-ai-for-everyone
- slides: https://community.deeplearning.ai/t/generative-ai-for-everyone-lecture-notes/481740
- 