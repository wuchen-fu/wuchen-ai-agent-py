import sys
import os
from dotenv import load_dotenv, find_dotenv

# 添加项目根目录到系统路径
# sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from web.agent.simple_rag_agent import SimpleRAGAgent

# 加载环境变量
dotenv_path = find_dotenv(filename='.env.dev', usecwd=True)
load_dotenv(dotenv_path=dotenv_path)

def main():
    """
    演示简化版RAG Agent的使用，降低LLM调用成本
    """
    print("=== 简化版RAG Agent示例 ===")
    print("此版本只需调用一次LLM，显著降低成本\n")
    
    # 创建简化版RAG Agent实例
    simple_rag_agent = SimpleRAGAgent()
    
    # 测试查询
    queries = [
        "怎么写小说大纲？",
        "写小说需要注意什么？",
        "小说的三幕式结构是什么？"
    ]
    
    for query in queries:
        print(f"问题: {query}")
        print("回答:", end=" ")
        
        # 使用流式输出
        for chunk in simple_rag_agent.stream(query):
            print(chunk, end="", flush=True)
        print("\n")
        
        # 分隔线
        print("-" * 50 + "\n")

if __name__ == "__main__":
    main()