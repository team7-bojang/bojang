import random

from openai import OpenAI

from app.config import settings

_client = None


def _get_client():
    global _client
    if _client is not None:
        return _client
    if settings.openai_api_key:
        _client = OpenAI(api_key=settings.openai_api_key)
        return _client
    return None


def embed(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []

    client = _get_client()
    if not client:
        # API Key가 비어 있으면 결정론적인 난수 기반 더미 1536차원 벡터 생성
        # (텍스트가 같으면 동일한 벡터가 나오도록 해시 시드 적용)
        dummy_vectors = []
        for text in texts:
            random.seed(hash(text))
            dummy_vectors.append([random.random() for _ in range(1536)])
        return dummy_vectors

    try:
        res = client.embeddings.create(model="text-embedding-3-small", input=texts)
        return [item.embedding for item in res.data]
    except Exception as e:
        print(f"[Embedder] OpenAI API call failed: {e}. Falling back to dummy embeddings.")
        dummy_vectors = []
        for text in texts:
            random.seed(hash(text))
            dummy_vectors.append([random.random() for _ in range(1536)])
        return dummy_vectors
