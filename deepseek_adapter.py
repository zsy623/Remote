# deepseek_adapter.py
"""DeepSeek API适配器模块 - 封装与大语言模型的通信逻辑"""

from langchain_openai import ChatOpenAI  # LangChain的OpenAI兼容客户端
from config import DEEPSEEK_API_KEY, DEEPSEEK_MODEL, DEEPSEEK_TEMPERATURE, DEEPSEEK_BASE_URL

class DeepSeekAdapter:
    """DeepSeek适配器类 - 负责与DeepSeek API的通信"""
    
    def __init__(self):
        """初始化DeepSeek客户端"""
        # 创建ChatOpenAI实例，配置为使用DeepSeek API
        self.client = ChatOpenAI(
            api_key=DEEPSEEK_API_KEY,  # 设置API密钥
            base_url=DEEPSEEK_BASE_URL,  # 设置API基础URL
            model=DEEPSEEK_MODEL,  # 设置模型名称
            temperature=DEEPSEEK_TEMPERATURE  # 设置生成温度
        )
    
    def call_llm(self, prompt: str) -> str:
        """
        调用大语言模型生成响应
        
        Args:
            prompt (str): 输入的提示词文本
            
        Returns:
            str: 模型生成的响应文本，出错时返回空字符串
        """
        try:
            # 调用模型生成响应
            response = self.client.invoke(prompt)
            print("response:\n")
            print(response)
            # 返回响应内容
            return response.content
        except Exception as e:
            # 打印错误信息，便于调试
            print(f"API调用错误: {e}")
            # 出错时返回空字符串
            return ""