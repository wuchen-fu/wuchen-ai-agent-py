import logging
import os
from pathlib import Path

from dotenv import find_dotenv, load_dotenv
from langchain_core.tools import tool
from langchain_core.documents import Document
from typing import List

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# 加载环境变量
dotenv_path = find_dotenv(filename='.env.dev', usecwd=True)
load_dotenv(dotenv_path=dotenv_path)

# 全局变量
vector_store = None
store_initialized = False
PERSIST_DIR = os.path.abspath("./chroma_db")
EMBEDDING_MODEL = "sentence-transformers/all-mpnet-base-v2"
def get_vector_store():
    """
    获取向量存储实例，不自动加载文档
    """
    """
       获取向量存储实例，优先加载已有的持久化数据
       """
    global vector_store, store_initialized

    if not store_initialized:
        # 延迟导入
        from langchain_community.embeddings import HuggingFaceEmbeddings
        from langchain_chroma import Chroma
        # 确保目录存在
        Path(PERSIST_DIR).mkdir(parents=True, exist_ok=True)
        # 检查持久化目录是否存在且包含数据
        if os.path.exists(PERSIST_DIR) and os.listdir(PERSIST_DIR):
            # 加载已有的向量存储
            print(f"加载已有的向量存储: {PERSIST_DIR}")
            vector_store = Chroma(
                embedding_function=HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL),
                persist_directory=PERSIST_DIR
            )
        else:
            # 创建新的空向量存储
            print(f"创建新的向量存储: {PERSIST_DIR}")
            vector_store = Chroma(
                embedding_function=HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL),
                persist_directory=PERSIST_DIR
            )

        store_initialized = True

    return vector_store


@tool
def rag_document_retrieval(query: str, k: int = 5) -> List[dict]:
    """
    RAG文档检索工具，用于从本地知识库中检索与查询相关的文档片段。

    该工具会在向量数据库中搜索与查询最相关的文档片段并返回相关内容。
    返回的结果可以用于后续的问答生成或其他处理。

    参数:
        query: 需要检索的查询内容
        k: 返回的文档片段数量，默认为5

    返回:
        检索到的相关文档信息列表，每个元素包含content和metadata
    """
    try:
        # 获取向量存储实例
        store = get_vector_store()
        docs: List[Document] = store.similarity_search(query, k=k)
        logger.info(f"检索到 {len(docs)} 个相关文档")
        results = []
        for doc in docs:
            results.append({
                "content": doc.page_content,
                "metadata": doc.metadata
            })

        return results
    except Exception as e:
        raise Exception(f"文档检索过程中发生错误: {str(e)}")


# # 保持兼容性
# rag_retrieval_tool = rag_document_retrieval
# tools = [rag_document_retrieval]
