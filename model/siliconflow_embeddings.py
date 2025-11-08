"""SiliconFlow嵌入模型支持"""
import requests
import numpy as np
from typing import List, Optional
from langchain_core.embeddings import Embeddings


class SiliconFlowEmbeddings(Embeddings):
    """SiliconFlow嵌入模型"""
    
    def __init__(
        self,
        model: str = "BAAI/bge-m3",
        api_key: Optional[str] = None,
        base_url: str = "https://api.siliconflow.cn/v1",
    ):
        self.model = model
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.url = f"{self.base_url}/embeddings"
        
    def _call_api(self, texts: List[str]) -> List[List[float]]:
        """调用SiliconFlow API"""
        payload = {
            "model": self.model,
            "input": texts
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(self.url, json=payload, headers=headers)
        
        if response.status_code != 200:
            raise Exception(f"API错误: {response.status_code}, {response.text}")
        
        result = response.json()
        if "data" not in result:
            raise Exception(f"API返回格式错误: {result}")
        
        return [item["embedding"] for item in result["data"]]
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """嵌入文档列表"""
        return self._call_api(texts)
    
    def embed_query(self, text: str) -> List[float]:
        """嵌入单个查询"""
        return self._call_api([text])[0]


def get_siliconflow_embeddings(model: str = "BAAI/bge-m3", api_key: str = None, base_url: str = None):
    """获取SiliconFlow嵌入模型实例"""
    import os
    from dotenv import load_dotenv

    load_dotenv()

    return SiliconFlowEmbeddings(
        model=model or os.getenv('OPENAI_EMBEDDINGS_MODEL', 'BAAI/bge-m3'),
        api_key=api_key or os.getenv('OPENAI_API_KEY'),
        base_url=base_url or os.getenv('OPENAI_BASE_URL', 'https://api.siliconflow.cn/v1'),
    )
