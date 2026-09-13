---
title: 20240321-interview-warmup
date: 2024-03-21
tags:
  - llm
  - chatgpt
  - rag
updated: 2024-03-21
up:
  - "[[projects]]"
---
## Backgrounds
I just got rejected by a big tech company. In order to improve my ability to explain interview questions effectively in English, I'm designing an interview warmup tool using LLM and RAG technologies.
## Design
So, I start design a system that could help me practice:
- User Story
	- As a recruiter, I want to disguise the user’s answer is correct or not based on the QA dataset so that I could filter potential candidates.
- Scope the Problem
	- Recruiter can build his/her QA datasets.
	- LLM will provide some technical advice to the recruiter
- Main component
	- Storage: JSON file
	- Advice: ChatGPT+RAG
![](https://i.imgur.com/n7v6IgB.png)

This project consists of two main components: Retriever and Advisor. Retriever focuses on managing the dataset. Initially, I use Gemini to generate the correct answers, which are then saved in a JSON file. Subsequently, questions and answers are stored in a JSON file due to its advantages:
- **Machine-readable:** Computers can easily process the data.
- **Human-readable:** Users can understand the content readily.
- **Consolidated storage:** All questions and answers are conveniently located in a single file.
To find relevant questions quickly, Retriever employs embedding techniques.
The Advisor component, powered by the ChatGPT API, assesses candidate responses **to** the recruiter's questions. Advisor will then provide its results to the recruiter.  

## Sample Code
- `qa.json`
```python
{
   "tq":[
      {
         "q":"What is the order of elements return by the keys() method of a python dict?",
         "a":"The order of elements returned by the keys() method of a Python dictionary is not guaranteed to be in any specific order. It may reflect the order the items were added in some cases, but this behavior is not reliable and can change between Python versions. If you depend on a specific order for your keys, you can use the sorted() function along with the keys() method."
      }
   ]
}
```
- `main.py`
```python
import json
from pathlib import Path
file_path='qa.json'
data = json.loads(Path(file_path).read_text())

from langchain.embeddings.sentence_transformer import SentenceTransformerEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.prompts import ChatPromptTemplate
embedding_function = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
db = Chroma.from_documents(documents, embedding_function)
retriever = db.as_retriever()
template = """Please distinguish the answer is correct or not based only on the following context and question, if the answer is incorrect, please explain why answer is incorrect.:
{context}
Question: {question}
Answer: {answer}
"""
prompt = ChatPromptTemplate.from_template(template)
from langchain_core.runnables import RunnableLambda, RunnablePassthrough

from langchain_core.output_parsers import StrOutputParser

from langchain_openai import ChatOpenAI

import os

os.environ['OPENAI_API_KEY'] = "sk-OOOO"

model = ChatOpenAI()

question = "what is the return order of the dict by using keys() method"

chain = (

{"context": retriever, "answer": RunnablePassthrough(), "question": RunnablePassthrough()}
| prompt
| model
| StrOutputParser()
)

query = "I'm not sure the order. But If I thought I will first sorted by its key to granted the return order of the elements"
print(chain.invoke(query))
```
## Notes
- https://python.langchain.com/docs/get_started/installation