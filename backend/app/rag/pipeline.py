from openai import OpenAI
from app.config import settings

client = OpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None



class RAGPipeline:
    def __init__(self, retriever):
        self.retriever = retriever

    def ask(self, query):
        docs = self.retriever.search(query)

        context = "\n\n".join(docs)

        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {
                    "role": "system",
                    "content": "너는 보험 약관을 분석하는 전문가야. 반드시 주어진 문맥 기반으로만 답해."
                },
                {
                    "role": "user",
                    "content": f"""
[약관]
{context}

[질문]
{query}
"""
                }
            ]
        )

        return response.choices[0].message.content