---
title: 20231209-docker-machine-learning
date: 2023-12-09
tags:
  - docker
  - machine_learning
up:
  - "[[ml]]"
---
## Docker
`docker search tensorflow`
`docker pull jupyter/tensorflow-notebook`
`docker run jupyter/tensorflow-notebook -p 8000:8888`
- -p out:in

Transformers
`from transformers import pipeline`
`pip install transformers`
## docker compose
```yaml
services:
	transformers-notebook:
			build: ./Dockerfile | image: jupyter/tensorflow-notebook
				- 8000:8888
			environment
				- JUPYTER_TOKEN=token
			volumes
				- ./:/home/{user}
```

```Dockerfile
FROM jupyter/tensorflow-notebook
USER $NB_UID   //user | USER root
RUN pip install --upgrade pip &&\
	pip install transformers && \
	pip install pysrt && \
	fix-permissions "/home/${NB_USER}"
COPY file.srt Translate.ipynb ./

```

`docker-compose up`

`from transformers import pipeline`
`pip install transformers`
```python
translator = pipeline("translation_en_to_fr")
fr = translator("Hi there I'm Alan!")

 ```
 pysrt 讀取字幕檔

`docker images`

`docker image tag OOOOOOO-transformers-notebook:latest {user}/srt-translator:1.0`

`docker push {user}/srt-translator:1.0`

`docker container prune`
`docker rmi {user}/srt-translator:1.0`

`docker run -p 5000:8888 {user}/srt-translator:1.0`

## Ref
- https://youtu.be/-l7YocEQtA0?si=GOfJLcaa5CL8NBaX
