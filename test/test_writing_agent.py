#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Writing Agent 测试示例
"""

import asyncio
import os
from dotenv import find_dotenv, load_dotenv

# 添加项目根目录到Python路径
import sys

from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains.history_aware_retriever import create_history_aware_retriever
from langchain.chains.retrieval import create_retrieval_chain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableWithMessageHistory

from chat_memory.mongo_chat_memory import MongoChatMemory
from tools.rag_tool import get_vector_store
from tools.web_search_toolkit import WebSearchToolkit

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

from web.agent.writing_agent import WritingAgent
from langchain_openai.chat_models import ChatOpenAI

# 加载环境变量
dotenv_path = find_dotenv(filename='../.env.dev', usecwd=True)
load_dotenv(dotenv_path=dotenv_path)

chid = 'writing_test_session'

def test_writing_agent_sync():
    """测试同步写作代理"""
    print("=== 测试同步写作代理 ===")
    
    try:
        # 初始化聊天模型
        chat_model = ChatOpenAI(
            model=os.getenv('QWEN_MODEL'),
            api_key=os.getenv('QWEN_API_KEY'),
            base_url=os.getenv('QWEN_URL')
        )
        
        # 创建写作代理实例
        print("创建写作代理实例...")
        # 使用新的配置字典方式创建WritingAgent
        writing_agent = WritingAgent({"chat_model": chat_model})
        print("写作代理实例创建成功")
        

        response = writing_agent.stream_chat('我想都市小说', chid, "test_user")
        for chunk in response:
            print(chunk, end="")
        # print(f"回复: {response}")

    except Exception as e:
        print(f"测试出错: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        raise


async def test_writing_agent_async():
    """测试异步写作代理"""
    print("\n=== 测试异步写作代理 ===")
    
    try:
        # 初始化聊天模型
        chat_model = ChatOpenAI(
            model=os.getenv('QWEN_MODEL'),
            api_key=os.getenv('QWEN_API_KEY'),
            base_url=os.getenv('QWEN_URL')
        )
        
        # 创建写作代理实例
        # 使用新的配置字典方式创建WritingAgent
        writing_agent = WritingAgent({"chat_model": chat_model})
        
        # 测试查询
        test_queries = [
            "如何构建小说的世界观？",
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n--- 异步测试查询 {i}: {query} ---")
            try:
                response = await writing_agent.achat(query, f"async_writing_test_session_{i}", "test_user")
                print(f"回复: {response}")
            except Exception as e:
                print(f"查询出错: {e}")
                import traceback
                traceback.print_exc()
                
    except Exception as e:
        print(f"创建写作代理时出错: {e}")
        import traceback
        traceback.print_exc()


def test_writing_agent_with_history():
    """测试写作代理的历史记录功能"""
    print("\n=== 测试写作代理的历史记录功能 ===")
    
    try:
        # 初始化聊天模型
        chat_model = ChatOpenAI(
            model=os.getenv('QWEN_MODEL'),
            api_key=os.getenv('QWEN_API_KEY'),
            base_url=os.getenv('QWEN_URL')
        )
        
        # 创建写作代理实例
        # 使用新的配置字典方式创建WritingAgent
        writing_agent = WritingAgent({"chat_model": chat_model})
        
        # 第一条消息
        print("--- 第一条消息 ---")
        resp1 = writing_agent.chat("我想写一部科幻小说，有什么建议吗？", "history_test_session", "test_user")
        print(f"回复: {resp1}")
        
        # 第二条消息，基于历史记录
        print("\n--- 第二条消息（基于历史） ---")
        resp2 = writing_agent.chat("刚才提到的科幻小说，我应该设定怎样的世界观？", "history_test_session", "test_user")
        print(f"回复: {resp2}")
                
    except Exception as e:
        print(f"测试出错: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        raise

def test_writing_agent_tool_rag_with_memory():
    # global chain1, chain2, chain
    chat_model = ChatOpenAI(
        model=os.getenv('QWEN_MODEL'),
        api_key=os.getenv('QWEN_API_KEY'),
        base_url=os.getenv('QWEN_URL')
    )
    bind_chat = chat_model.bind_tools(WebSearchToolkit().get_tools())
    system_prompt = '''
    你是一位专业的的小说作者，有丰富的小说经验和指导新人写小说经验。
    引导用户描述内容、设定,以及想法,给出相对应的指导
    核心能力：
    教学指导：将复杂技巧拆解为三步实操法
    文本分析：诊断+带注释修改示范
    创作示范：生成符合网文平台特性的内容
    你要用下面检索器检索出来的内容回答问题。
    如果不知道的话,就自行判断是否要通过工具进行网络查询
    工作规则：  
    1. 基于「上下文-问题转化器」输出的独立问题，先查看检索内容（{context}）：  
       - 若{context}有相关信息，结合信息回答；  
       - 若{context}无相关信息，进入工具调用判断。  
    
    2. 工具调用判断（不限制问题领域）：  
       - 无论问题属于小说创作、生活服务、信息查询等任何领域，只要存在对应的绑定工具，就调用工具获取信息后回答；  
       - 若没有对应工具，基于自身知识回答（若自身不知道，明确说明“无法回答该问题”）。 
    '''

    qa_prompt = ChatPromptTemplate.from_messages([
        ('system', '''
                    你是「上下文-问题转化器」，负责从历史聊天记录和用户最新提问中，提炼出独立、完整的核心问题。  
                    工作规则：  
                    1. 若有历史记录，分析与最新问题的关联，提炼出不依赖上下文也能理解的问题。  
                    2. 若历史记录与新问题无关（或无历史记录），直接返回新问题作为独立问题。  
                    3. 仅返回问题，不添加任何额外内容。
                    '''),
        MessagesPlaceholder(variable_name='chat_history'),
        ('human', '{input}'),
    ])

    prompt_template = ChatPromptTemplate.from_messages([
        ('system', system_prompt),
        MessagesPlaceholder(variable_name='chat_history'),
        ('human', '{input}'),
    ])
    # 问题重写lian
    qa_chain = create_history_aware_retriever(bind_chat,get_vector_store().as_retriever(),qa_prompt)

    # 提问链
    question_chain = create_stuff_documents_chain(bind_chat, prompt_template)


    rag_chain = create_retrieval_chain(qa_chain, question_chain)

    # 覆盖BaseAgent的history_chain以使用LangChain的实现
    history_chain = RunnableWithMessageHistory(
        rag_chain,
        MongoChatMemory.get_session_history,
        input_messages_key="input",
        history_messages_key="chat_history",
        output_messages_key="answer"
    )
    resp = history_chain.invoke(
        {"input": "今天上海天气怎么样？"},
         config={"configurable": {"session_id": "abc2"}}
    )['answer']
    print(f"回复: {resp}")

def main():
    """主测试函数"""
    print("开始测试 Writing Agent...")
    # test_writing_agent_tool_rag_with_memory()
    # 测试同步功能
    test_writing_agent_sync()
    
    # # 测试历史记录功能
    # test_writing_agent_with_history()
    #
    # # 测试异步功能
    # asyncio.run(test_writing_agent_async())
    #
    print("\n测试完成。")


if __name__ == "__main__":
    main()