from langchain_openai import OpenAIEmbeddings
from langchain_openai import ChatOpenAI

# 导入SiliconFlow嵌入模型
try:
    from model.siliconflow_embeddings import SiliconFlowEmbeddings, get_siliconflow_embeddings
except ImportError:
    SiliconFlowEmbeddings = None
    get_siliconflow_embeddings = None
try:
    from langchain.callbacks.streaming_aiter import AsyncIteratorCallbackHandler
    from langchain.callbacks.manager import AsyncCallbackManager
except ImportError:
    # 新版本langchain中的替代导入
    from langchain_core.callbacks.manager import AsyncCallbackManager
    # AsyncIteratorCallbackHandler在新版本中已移除，使用其他方式
    AsyncIteratorCallbackHandler = None


import os
from pathlib import Path
from dotenv import load_dotenv

# 设置tiktoken缓存避免网络问题
def setup_cache():
    cache_dir = Path.home() / "cache" / "tiktoken"
    cache_dir.mkdir(parents=True, exist_ok=True)
    os.environ["TIKTOKEN_CACHE_DIR"] = str(cache_dir)

setup_cache()

load_dotenv()

def get_embeddings_model():
    """智能选择嵌入模型"""
    model_name = os.getenv('OPENAI_EMBEDDINGS_MODEL', 'text-embedding-3-small')
    api_key = os.getenv('OPENAI_API_KEY')
    base_url = os.getenv('OPENAI_BASE_URL')

    # 如果是BAAI模型，使用SiliconFlow自定义嵌入
    if model_name.startswith('BAAI/') and get_siliconflow_embeddings:
        print(f"使用SiliconFlow嵌入模型: {model_name}")
        return get_siliconflow_embeddings(
            model=model_name,
            api_key=api_key,
            base_url=base_url
        )

    # 否则使用OpenAI嵌入
    print(f"使用OpenAI嵌入模型: {model_name}")
    return OpenAIEmbeddings(
        model=model_name,
        api_key=api_key,
        base_url=base_url,
    )


def get_llm_model():
    model = ChatOpenAI(
        model=os.getenv('DEFAULT_MODEL', 'gpt-3.5-turbo'),
        temperature=float(os.getenv('TEMPERATURE', '0.7')),
        max_tokens=int(os.getenv('MAX_TOKENS', '4000')),
        api_key=os.getenv('OPENAI_API_KEY'),
        base_url=os.getenv('OPENAI_BASE_URL'),
    )
    return model

def get_stream_llm_model():
    # 检查是否支持流式回调
    if AsyncIteratorCallbackHandler is not None:
        callback_handler = AsyncIteratorCallbackHandler()
        manager = AsyncCallbackManager(handlers=[callback_handler])
        callbacks = manager
    else:
        # 新版本langchain中直接使用streaming=True
        callbacks = None

    model = ChatOpenAI(
        model=os.getenv('DEFAULT_MODEL', 'gpt-3.5-turbo'),
        temperature=float(os.getenv('TEMPERATURE', '0.7')),
        max_tokens=int(os.getenv('MAX_TOKENS', '4000')),
        api_key=os.getenv('OPENAI_API_KEY'),
        base_url=os.getenv('OPENAI_BASE_URL'),
        streaming=True,
        callbacks=callbacks,
    )
    return model

def count_tokens(text):
    """简单通用的token计数"""
    if not text:
        return 0

    model_name = os.getenv('DEFAULT_MODEL', '').lower()
    
    # 如果是deepseek，使用transformers
    if 'deepseek' in model_name:
        try:
            from transformers import AutoTokenizer
            tokenizer = AutoTokenizer.from_pretrained("deepseek-ai/DeepSeek-V3")
            return len(tokenizer.encode(text))
        except:
            pass
    
    # 如果是gpt，使用tiktoken
    if 'gpt' in model_name:
        try:
            import tiktoken
            encoding = tiktoken.get_encoding("cl100k_base")
            return len(encoding.encode(text))
        except:
            pass
    
    # 备用方案：简单计算
    chinese = len([c for c in text if '\u4e00' <= c <= '\u9fff'])
    english = len(text) - chinese
    return chinese + english // 4

if __name__ == '__main__':
    # 测试llm
    llm = get_llm_model()
    print(llm.invoke("你好"))

    # 由于langchain版本问题，这个目前测试会报错
    # llm_stream = get_stream_llm_model()
    # print(llm_stream.invoke("你好"))

    # 测试embedding
    test_text = "你好，这是一个测试。"
    embeddings = get_embeddings_model()
    print(embeddings.embed_query(test_text))

    # 测试计数
    test_text = "Hello 你好世界"
    tokens = count_tokens(test_text)
    print(f"Token计数: '{test_text}' = {tokens} tokens")
