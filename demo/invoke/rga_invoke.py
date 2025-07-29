import os
import sys

# 添加项目根目录到系统路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from dotenv import load_dotenv, find_dotenv
from web.agent.rag_agent import RAGAgent

dotenv_path = find_dotenv(filename='.env.dev', usecwd=True)
# 加载 .env 文件
load_dotenv(dotenv_path=dotenv_path)
# LangSmish 调用AI检测平台
lang_chain_switch = os.getenv('LANGCHAIN_TRACING_V2')
lang_chain_api_key = os.getenv('LANGCHAIN_API_KEY')
lang_chain_server_name = os.getenv('LANGCHAIN_PROJECT')

# 创建RAG Agent实例
rag_agent = RAGAgent()

# 运行示例
if __name__ == "__main__":
    user_input = "我最近在看小说，有写小说的想法，请告诉我怎么写小说？"

    print("\n--- Streaming RAG 过程输出 ---\n")
    for chunk in rag_agent.stream(user_input):
        for node, update in chunk.items():
            print(f"Node: {node}")
            update["messages"][-1].pretty_print()
            print()