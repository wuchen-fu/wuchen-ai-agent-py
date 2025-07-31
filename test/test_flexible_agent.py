import sys
import os
from dotenv import load_dotenv, find_dotenv
from langchain_openai import ChatOpenAI

# 添加项目根目录到系统路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from web.agent.base_agent import BaseAgent, AgentFactory

# 加载环境变量
dotenv_path = find_dotenv(filename='.env.dev', usecwd=True)
load_dotenv(dotenv_path=dotenv_path)

def create_chat_model(model_name: str = None):
    """
    创建ChatOpenAI模型实例的辅助函数
    
    Args:
        model_name: 模型名称，默认使用环境变量中的DASH_SCOPE_MODEL
        
    Returns:
        ChatOpenAI实例
    """
    model = model_name or os.getenv('DASH_SCOPE_MODEL')
    return ChatOpenAI(
        model=model,
        api_key=os.getenv('DASH_SCOPE_API_KEY'),
        base_url=os.getenv('DASH_SCOPE_URL')
    )

def demo_writing_agent():
    """
    演示写作助手Agent（使用RAG）
    """
    print("=== 写作助手Agent（使用RAG） ===")
    
    # 创建模型实例
    chat_model = create_chat_model()
    
    # 使用工厂方法创建写作助手（必须传入chat_model）
    writing_agent = AgentFactory.create_writing_agent(chat_model)
    
    queries = [
        "怎么写小说大纲？",
        "写小说需要注意什么？"
    ]
    
    session_id = "writing_session_1"
    
    for query in queries:
        print(f"\n用户: {query}")
        print("助手: ", end="")
        response = writing_agent.invoke(query, session_id=session_id)
        print(response)
        print("-" * 50)

def demo_general_agent():
    """
    演示通用助手Agent（不使用RAG）
    """
    print("\n=== 通用助手Agent（不使用RAG） ===")
    
    # 创建模型实例
    chat_model = create_chat_model()
    
    # 使用工厂方法创建通用助手（必须传入chat_model）
    general_agent = AgentFactory.create_general_agent(chat_model)
    
    queries = [
        "今天天气怎么样？",
        "Python是什么？"
    ]
    
    session_id = "general_session_1"
    
    for query in queries:
        print(f"\n用户: {query}")
        print("助手: ", end="")
        response = general_agent.invoke(query, session_id=session_id)
        print(response)
        print("-" * 50)

def demo_custom_agent():
    """
    演示自定义Agent
    """
    print("\n=== 自定义Agent示例 ===")
    
    # 创建不同模型实例
    chat_model = create_chat_model("qwen-plus")
    
    # 创建一个数学老师Agent
    math_teacher_system_message = """
    你是一位数学老师，专门帮助学生解决数学问题。
    请用简单易懂的方式解释数学概念，并给出解题步骤。
    """
    
    # 使用自定义模型创建数学老师Agent（必须传入chat_model）
    math_agent = AgentFactory.create_custom_agent(
        chat_model=chat_model,
        system_message=math_teacher_system_message, 
        use_rag=False
    )
    
    queries = [
        "什么是勾股定理？",
        "如何计算圆的面积？"
    ]
    
    session_id = "math_session_1"
    
    for query in queries:
        print(f"\n学生: {query}")
        print("老师: ", end="")
        response = math_agent.invoke(query, session_id=session_id)
        print(response)
        print("-" * 50)

def demo_custom_agent_with_rag():
    """
    演示自定义Agent（使用RAG）
    """
    print("\n=== 自定义Agent（使用RAG） ===")
    
    # 创建模型实例
    chat_model = create_chat_model("qwen-plus")
    
    # 创建一个技术文档助手Agent
    tech_doc_system_message = """
    你是一个技术文档助手，专门帮助用户理解技术文档内容。
    你会根据提供的上下文信息来回答用户问题。
    """
    
    # 使用自定义模型创建技术文档助手Agent（必须传入chat_model）
    tech_agent = AgentFactory.create_custom_agent(
        chat_model=chat_model,
        system_message=tech_doc_system_message, 
        use_rag=True
    )
    
    queries = [
        "如何使用RAG技术？",
        "LangChain是什么？"
    ]
    
    session_id = "tech_session_1"
    
    for query in queries:
        print(f"\n用户: {query}")
        print("助手: ", end="")
        response = tech_agent.invoke(query, session_id=session_id)
        print(response)
        print("-" * 50)

def demo_direct_instantiation():
    """
    演示直接实例化BaseAgent
    """
    print("\n=== 直接实例化BaseAgent ===")
    
    # 创建模型实例
    coding_model = create_chat_model("qwen-coding-plus")
    
    # 直接实例化BaseAgent并指定模型（必须传入chat_model）
    coding_agent = BaseAgent(
        chat_model=coding_model,
        system_message="你是一位编程专家，专门帮助用户解决编程问题。",
        use_rag=False
    )
    
    queries = [
        "Python中如何定义一个类？",
        "什么是递归函数？"
    ]
    
    session_id = "coding_session_1"
    
    for query in queries:
        print(f"\n用户: {query}")
        print("助手: ", end="")
        response = coding_agent.invoke(query, session_id=session_id)
        print(response)
        print("-" * 50)

if __name__ == "__main__":
    # 演示不同类型的agents
    demo_writing_agent()
    demo_general_agent()
    demo_custom_agent()
    demo_custom_agent_with_rag()
    demo_direct_instantiation()
    
    print("\n=== 总结 ===")
    print("1. BaseAgent类现在要求在初始化时必须传入chat_model实例")
    print("2. 支持自定义system角色定义")
    print("3. 可以选择是否启用RAG功能")
    print("4. 提供了AgentFactory工厂类简化常用Agent创建")
    print("5. 支持会话历史管理")
    print("6. 提供invoke和stream两种调用方式")