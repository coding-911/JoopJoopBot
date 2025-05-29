# JoopJoop Core

JoopJoop 프로젝트의 코어 패키지입니다.

## 기능

- DART API 클라이언트
- RAG (Retrieval Augmented Generation) 파이프라인

## 설치

```bash
poetry install
```

## 사용 예시

```python
from joopjoop.dart import DartClient
from joopjoop.rag import RAGPipeline

# DART API 사용
client = DartClient(api_key="your_api_key")
corps = await client.get_corp_codes()

# RAG 파이프라인 사용
pipeline = RAGPipeline(vector_store_path="./vector_store")
pipeline.process_document(document)
``` 