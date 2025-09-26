# deepseek_adapter.py
from langchain_openai import ChatOpenAI
from config import DEEPSEEK_API_KEY, DEEPSEEK_MODEL, DEEPSEEK_TEMPERATURE

class DeepSeekAdapter:
    def __init__(self):
        self.client = ChatOpenAI(
            api_key=DEEPSEEK_API_KEY,
            base_url="https://api.deepseek.com/v1",
            model=DEEPSEEK_MODEL,
            temperature=DEEPSEEK_TEMPERATURE
        )
    
    def call_llm(self, prompt: str) -> str:
        try:
            response = self.client.invoke(prompt)
            return response.content
        except Exception as e:
            print(f"API调用错误: {e}")
            return ""