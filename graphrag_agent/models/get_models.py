from langchain_openai import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
import os

from graphrag_agent.config.settings import (
    TIKTOKEN_CACHE_DIR,
    OPENAI_EMBEDDING_CONFIG,
    OPENAI_LLM_CONFIG,
)


# 设置 tiktoken 缓存目录，避免每次联网拉取
def setup_cache():
    TIKTOKEN_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    os.environ["TIKTOKEN_CACHE_DIR"] = str(TIKTOKEN_CACHE_DIR)


setup_cache()

def get_embeddings_model():
    config = {k: v for k, v in OPENAI_EMBEDDING_CONFIG.items() if v}
    return OpenAIEmbeddings(**config)


def get_llm_model():
    config = {k: v for k, v in OPENAI_LLM_CONFIG.items() if v is not None and v != ""}
    return ChatOpenAI(**config)


def get_llm_model_with_streaming():
    """获取支持流式输出的 LLM 模型"""
    config = {k: v for k, v in OPENAI_LLM_CONFIG.items() if v is not None and v != ""}
    
    # LangChain 1.0+ 中，流式处理使用 callbacks 参数
    config["streaming"] = True
    
    return ChatOpenAI(**config)


def count_tokens(text):
    """简单通用的token计数"""
    if not text:
        return 0
    
    model_name = (OPENAI_LLM_CONFIG.get("model") or "").lower()
    
    # 如果是deepseek，使用transformers
    if 'deepseek' in model_name:
        try:
            from transformers import AutoTokenizer
            tokenizer = AutoTokenizer.from_pretrained("deepseek-ai/DeepSeek-V2.5")
            return len(tokenizer.encode(text))
        except:
            pass
    
    # 默认使用 tiktoken
    try:
        import tiktoken
        enc = tiktoken.encoding_for_model("gpt-4o")
        return len(enc.encode(text))
    except:
        return len(text) // 4  # 粗略估算
