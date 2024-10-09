---
title: 20240227-huggingface-nlp
date: 2024-02-27
tags:
  - course
  - nlp
updated: 2024-02-27
up:
  - "[[nlp]]"
---
# transformers models
![](https://i.imgur.com/QkCYS7N.png)

![](https://i.imgur.com/72ZHVoq.png)

## NLP
### challenge
- 人可以很快知道詞相似
## Transformers, what can they do?
### Working with pipelines
- https://huggingface.co/models
```python
from transformers import pipeline

classifier = pipeline("sentiment-analysis")
classifier("I've been waiting for a HuggingFace course my whole life.")
# [{'label': 'POSITIVE', 'score': 0.9598047137260437}]
```
 [available pipelines](https://huggingface.co/transformers/main_classes/pipelines)
### Zero-shot classification
不需要pretrain來進行分類
```python
from transformers import pipeline

classifier = pipeline("zero-shot-classification")
classifier(
    "This is a course about the Transformers library",
    candidate_labels=["education", "politics", "business"],
)
#{'sequence': 'This is a course about the Transformers library',
# 'labels': ['education', 'business', 'politics'],
# 'scores': [0.8445963859558105, 0.111976258456707, 0.043427448719739914]}
```
### Text generation
```python
from transformers import pipeline

generator = pipeline("text-generation")
generator("In this course, we will teach you how to")
# [{'generated_text': 'In this course, we will teach you how to understand and use ' 'data flow and data interchange when handling user data. We ' 'will be working with one or more of the most commonly used ' 'data flows — data flows of various types, as seen by the ' 'HTTP'}]
```
### Using any model from the Hub in a pipeline
```python
from transformers import pipeline

generator = pipeline("text-generation", model="distilgpt2")
generator(
    "In this course, we will teach you how to",
    max_length=30,
    num_return_sequences=2,
)
# [{'generated_text': 'In this course, we will teach you how to manipulate the world and ' 'move your mental and physical capabilities to your advantage.'}, {'generated_text': 'In this course, we will teach you how to become an expert and ' 'practice realtime, and with a hands on experience on both real ' 'time and real'}]
```
### Mask filling
```python
from transformers import pipeline

unmasker = pipeline("fill-mask")
unmasker("This course will teach you all about <mask> models.", top_k=2)
# [{'sequence': 'This course will teach you all about mathematical models.', 'score': 0.19619831442832947, 'token': 30412, 'token_str': ' mathematical'}, {'sequence': 'This course will teach you all about computational models.', 'score': 0.04052725434303284, 'token': 38163, 'token_str': ' computational'}]
```
### Named entity recognition
```python
from transformers import pipeline

ner = pipeline("ner", grouped_entities=True)
ner("My name is Sylvain and I work at Hugging Face in Brooklyn.")
# [{'entity_group': 'PER', 'score': 0.99816, 'word': 'Sylvain', 'start': 11, 'end': 18}, {'entity_group': 'ORG', 'score': 0.97960, 'word': 'Hugging Face', 'start': 33, 'end': 45}, {'entity_group': 'LOC', 'score': 0.99321, 'word': 'Brooklyn', 'start': 49, 'end': 57} ]
```
### Question answering
```python
from transformers import pipeline

question_answerer = pipeline("question-answering")
question_answerer(
    question="Where do I work?",
    context="My name is Sylvain and I work at Hugging Face in Brooklyn",
)
# {'score': 0.6385916471481323, 'start': 33, 'end': 45, 'answer': 'Hugging Face'}
```

###  Summarization
```python
from transformers import pipeline

summarizer = pipeline("summarization")
summarizer(
    """
    America has changed dramatically during recent years. Not only has the number of 
    graduates in traditional engineering disciplines such as mechanical, civil, 
    electrical, chemical, and aeronautical engineering declined, but in most of 
    the premier American universities engineering curricula now concentrate on 
    and encourage largely the study of engineering science. As a result, there 
    are declining offerings in engineering subjects dealing with infrastructure, 
    the environment, and related issues, and greater concentration on high 
    technology subjects, largely supporting increasingly complex scientific 
    developments. While the latter is important, it should not be at the expense 
    of more traditional engineering.

    Rapidly developing economies such as China and India, as well as other 
    industrial countries in Europe and Asia, continue to encourage and advance 
    the teaching of engineering. Both China and India, respectively, graduate 
    six and eight times as many traditional engineers as does the United States. 
    Other industrial countries at minimum maintain their output, while America 
    suffers an increasingly serious decline in the number of engineering graduates 
    and a lack of well-educated engineers.
"""
)
# [{'summary_text': ' America has changed dramatically during recent years . The ' 'number of engineering graduates in the U.S. has declined in ' 'traditional engineering disciplines such as mechanical, civil ' ', electrical, chemical, and aeronautical engineering . Rapidly ' 'developing economies such as China and India, as well as other ' 'industrial countries in Europe and Asia, continue to encourage ' 'and advance engineering .'}]
```
###  Translation
```python
from transformers import pipeline

translator = pipeline("translation", model="Helsinki-NLP/opus-mt-fr-en")
translator("Ce cours est produit par Hugging Face.")
# [{'translation_text': 'This course is produced by Hugging Face.'}]
```
##  How do Transformers work?
### A bit of Transformer history
 [Transformer architecture](https://arxiv.org/abs/1706.03762) 2017, June
![A brief chronology of Transformers models.](https://huggingface.co/datasets/huggingface-course/documentation-images/resolve/main/en/chapter1/transformers_chrono.svg)
###  Transformers are language models
- _causal language modelin_: 預測n個word
![Example of causal language modeling in which the next word from a sentence is predicted.](https://huggingface.co/datasets/huggingface-course/documentation-images/resolve/main/en/chapter1/causal_modeling.svg)
- _masked language modeling_: 預測空格![Example of masked language modeling in which a masked word from a sentence is predicted.](https://huggingface.co/datasets/huggingface-course/documentation-images/resolve/main/en/chapter1/masked_modeling.svg)
###  Transformers are big models
![Number of parameters of recent Transformers models](https://huggingface.co/datasets/huggingface-course/documentation-images/resolve/main/en/chapter1/model_parameters.png)
![The carbon footprint of a large language model.](https://huggingface.co/datasets/huggingface-course/documentation-images/resolve/main/en/chapter1/carbon_footprint.svg)
### Transfer Learning
- pre training vs Fine-tuning
![The pretraining of a language model is costly in both time and money.](https://huggingface.co/datasets/huggingface-course/documentation-images/resolve/main/en/chapter1/pretraining.svg)

![The fine-tuning of a language model is cheaper than pretraining in both time and money.](https://huggingface.co/datasets/huggingface-course/documentation-images/resolve/main/en/chapter1/finetuning.svg)
### General architecture
### Introduction
![Architecture of a Transformers models](https://huggingface.co/datasets/huggingface-course/documentation-images/resolve/main/en/chapter1/transformers_blocks.svg)
### Attention layers
### The original architecture
![Architecture of a Transformers models](https://huggingface.co/datasets/huggingface-course/documentation-images/resolve/main/en/chapter1/transformers.svg)
### Architectures vs. checkpoints
- **Architecture**: skeleton
- **Checkpoints**: weights 
- **Model**: This is an umbrella term that isn’t as precise as “architecture” or “checkpoint”: it can mean both. This course will specify _architecture_ or _checkpoint_ when it matters to reduce ambiguity.
## Encoder models
- 具有雙向attension
- 模型訓練通常使用mask訓練
- encoder model適合理解完整句子
- example 
	-  [ALBERT](https://huggingface.co/docs/transformers/model_doc/albert)
	- [BERT](https://huggingface.co/docs/transformers/model_doc/bert)
	- [DistilBERT](https://huggingface.co/docs/transformers/model_doc/distilbert)
	- [ELECTRA](https://huggingface.co/docs/transformers/model_doc/electra)
	- [RoBERTa](https://huggingface.co/docs/transformers/model_doc/roberta)
![](https://i.imgur.com/pSKKssf.png)
## Decoder models
![](https://i.imgur.com/0AaFRkb.png)
- example
	- - [CTRL](https://huggingface.co/transformers/model_doc/ctrl)
	- [GPT](https://huggingface.co/docs/transformers/model_doc/openai-gpt)
	- [GPT-2](https://huggingface.co/transformers/model_doc/gpt2)
	- [Transformer XL](https://huggingface.co/transformers/model_doc/transfo-xl)
## Sequence-to-sequence models sequence-to-sequence-models
![](https://i.imgur.com/hY4WxfB.png)
- example
	- [BART](https://huggingface.co/transformers/model_doc/bart)
	- [mBART](https://huggingface.co/transformers/model_doc/mbart)
	- [Marian](https://huggingface.co/transformers/model_doc/marian)
	- [T5](https://huggingface.co/transformers/model_doc/t5)
## Bias and limitations
- 可能有偏見，因為他從網路資料訓練
### Summary
| Model           | Examples                                   | Tasks                                                                            |
| --------------- | ------------------------------------------ | -------------------------------------------------------------------------------- |
| Encoder         | ALBERT, BERT, DistilBERT, ELECTRA, RoBERTa | Sentence classification, named entity recognition, extractive question answering |
| Decoder         | CTRL, GPT, GPT-2, Transformer XL           | Text generation                                                                  |
| Encoder-decoder | BART, T5, Marian, mBART                    | Summarization, translation, generative question answering                        |
|                 |                                            |                                                                                  |
# using transformers
## inside pipline
![The full NLP pipeline: tokenization of text, conversion to IDs, and inference through the Transformer model and the model head.](https://huggingface.co/datasets/huggingface-course/documentation-images/resolve/main/en/chapter2/full_nlp_pipeline.svg)

## models
可以使用 save pretrain 
```python
model = BertModel(config)
model.save_pretrained("directory_on_my_computer")
import torch

model_inputs = torch.tensor(encoded_sequences)
output = model(model_inputs)
```
## Tokenizer

### word based
- 有可能遇到沒在資料庫的會unknown
### Character-based
### Subword tokenization
- BERT 用這
![](https://i.imgur.com/HCERX6Z.png)
![](https://i.imgur.com/ChfFqii.png)
### encoding
![](https://i.imgur.com/0spIuRj.png)
##  Handling multiple sequences
## Putting it all together
# Fine tuning a pre-trained model
(skip)
# Sharing
(skip)
# Datasets Lib
(skip)
# Tokenizer lib
(skip)
## Main NLP tasks
### Token Classification
- **Named entity recognition (NER)**: 找相近
- **Part-of-speech tagging (POS)**: 分詞性
- **Chunking**: 分段(?)
![](https://i.imgur.com/HAe8XCf.png)

### Fine Tuning masked L M 

### Translation
### Summarization
### Causal Language Modeling
- 從前一個字預測下一個
### Question answering

# Building and sharing using Gradio
## Ref
- https://huggingface.co/learn/nlp-course/chapter0/1
