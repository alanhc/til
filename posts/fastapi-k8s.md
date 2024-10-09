---
title: fastapi-k8s
date: 2024-07-17
tags:
  - kubernetes
updated: 2024-07-17
up:
---
![[Pasted image 20240717010914.png]]
```
FROM tiangolo/uvicorn-gunicorn-fastapi:python3.9
COPY ./main.py /app/main.py
```
- fastapi-deployment.yaml
```

apiVersion: apps/v1

kind: Deployment

metadata:

  name: fastapi-deployment

spec:

  replicas: 1

  selector:

    matchLabels:

      app: fastapi

  template:

    metadata:

      labels:

        app: fastapi

    spec:

      containers:

        - name: fastapi-container

          image: alanhc/test:latest

          ports:

            - containerPort: 80
```
- fastapi-service.yaml
```
apiVersion: v1

kind: Service

metadata:

  name: fastapi-service

spec:

  selector:

    app: fastapi

  ports:

    - protocol: TCP

      port: 80

      targetPort: 80

  type: NodePort
```

```
from fastapi import FastAPI

app = FastAPI()

@app.get("/")

def read_root():

    return {"Hello": "World"}
```

`kubectl apply -f`

`kubectl get services`

 `kubectl port-forward svc/fastapi`
 
## Ref
