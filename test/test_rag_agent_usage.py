import sys
import os
from dotenv import load_dotenv, find_dotenv

# 添加项目根目录到系统路径
# sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from web.agent.rag_agent import RAGAgent

# 加载环境变量
dotenv_path = find_dotenv(filename='.env.dev', usecwd=True)
load_dotenv(dotenv_path=dotenv_path)

def novel_writing_agent():
    """
    小说写作专用Agent（完整版）
    注意：此版本功能完整但需要多次调用LLM，成本较高
    """
    print("=== 小说写作助手 Agent（完整版） ===")
    print("此版本功能完整但需要多次调用LLM，成本较高\n")
    rag_agent = RAGAgent()
    
    query = "怎么写小说大纲？"
    print(f"用户问题: {query}\n")
    
    # 使用流式输出
    for chunk in rag_agent.stream(query):
        for node, update in chunk.items():
            print(f"Node: {node}")
            update["messages"][-1].pretty_print()
            print()

def general_qa_agent():
    """
    通用问答Agent（完整版）
    注意：此版本功能完整但需要多次调用LLM，成本较高
    """
    print("=== 通用问答助手 Agent（完整版） ===")
    print("此版本功能完整但需要多次调用LLM，成本较高\n")
    rag_agent = RAGAgent()
    
    query = "写小说需要注意什么？"
    print(f"用户问题: {query}\n")
    
    # 使用普通调用方式
    response = rag_agent.invoke(query)
    print("回答:")
    response["messages"][-1].pretty_print()

def cost_optimized_recommendation():
    """
    成本优化建议
    """
    print("=== 成本优化建议 ===")
    print("如果您关注成本，可以使用简化版RAG Agent:")
    print("1. 仅需一次LLM调用")
    print("2. 直接检索并生成答案")
    print("3. 请参考 simple_rag_agent_usage_invoke.py")
    print("4. 使用方法：from tools.simple_rag_agent import SimpleRAGAgent\n")

if __name__ == "__main__":
    # 运行不同类型的agents
    novel_writing_agent()
    print("\n" + "="*50 + "\n")
    general_qa_agent()
    print("\n" + "="*50 + "\n")
    cost_optimized_recommendation()