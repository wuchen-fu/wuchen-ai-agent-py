import os
from typing import List, Optional, Dict, Any
from dotenv import load_dotenv, find_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from tools.rag_tool import get_vector_store

# 加载环境变量
dotenv_path = find_dotenv(filename='.env.dev', usecwd=True)
load_dotenv(dotenv_path=dotenv_path)


class BaseAgent:
    """
    通用Agent基类，支持自定义system角色定义和可选的RAG功能
    """
    
    def __init__(self, 
                 chat_model: ChatOpenAI,
                 system_prompt: str = "You are a helpful AI assistant.",
                 use_rag: bool = False,
                 rag_k: int = 5):
        """
        初始化Agent
        
        Args:
            chat_model: 已配置的ChatOpenAI实例（必填）
            system_prompt: 系统角色定义和提示词
            use_rag: 是否使用RAG功能
            rag_k: RAG检索文档数量
        """
        if not isinstance(chat_model, ChatOpenAI):
            raise ValueError("chat_model必须是ChatOpenAI实例")
            
        self.chat_model = chat_model
        self.system_prompt = system_prompt
        self.use_rag = use_rag
        self.rag_k = rag_k
        
        # 如果使用RAG，初始化向量存储
        if self.use_rag:
            vector_store = get_vector_store()
            self.retriever = vector_store.as_retriever(search_kwargs={"k": rag_k})
        
        # 初始化聊天历史存储
        self.chat_history = {}
    
    def _get_session_history(self, session_id: str) -> List:
        """
        获取会话历史
        
        Args:
            session_id: 会话ID
            
        Returns:
            会话历史消息列表
        """
        if session_id not in self.chat_history:
            self.chat_history[session_id] = []
        return self.chat_history[session_id]
    
    def _format_docs(self, docs) -> str:
        """
        格式化检索到的文档
        
        Args:
            docs: 检索到的文档列表
            
        Returns:
            格式化后的文档字符串
        """
        return "\n\n".join(doc.page_content for doc in docs)
    
    def invoke(self, 
               query: str, 
               session_id: str = "default",
               **kwargs) -> str:
        """
        处理用户查询
        
        Args:
            query: 用户查询
            session_id: 会话ID
            **kwargs: 其他参数
            
        Returns:
            模型回答
        """
        # 获取会话历史
        history = self._get_session_history(session_id)
        
        # 如果使用RAG，先检索相关文档
        context = ""
        if self.use_rag:
            docs = self.retriever.invoke(query)
            context = self._format_docs(docs)
        
        # 构建提示词
        messages = [SystemMessage(content=self.system_prompt)]
        
        # 添加历史消息
        messages.extend(history[-10:])  # 保留最近10条消息
        
        # 添加上下文（如果使用RAG）
        if context:
            messages.append(SystemMessage(content=f"参考以下上下文信息:\n{context}"))
        
        # 添加当前查询
        messages.append(HumanMessage(content=query))
        
        # 调用模型
        response = self.chat_model.invoke(messages)
        
        # 更新会话历史
        history.append(HumanMessage(content=query))
        history.append(AIMessage(content=response.content))
        
        return response.content
    
    def stream(self, 
               query: str, 
               session_id: str = "default",
               **kwargs):
        """
        流式处理用户查询
        
        Args:
            query: 用户查询
            session_id: 会话ID
            **kwargs: 其他参数
            
        Yields:
            模型回答的内容块
        """
        # 获取会话历史
        history = self._get_session_history(session_id)
        
        # 如果使用RAG，先检索相关文档
        context = ""
        if self.use_rag:
            docs = self.retriever.invoke(query)
            context = self._format_docs(docs)
        
        # 构建提示词
        messages = [SystemMessage(content=self.system_prompt)]
        
        # 添加历史消息
        messages.extend(history[-10:])  # 保留最近10条消息
        
        # 添加上下文（如果使用RAG）
        if context:
            messages.append(SystemMessage(content=f"参考以下上下文信息:\n{context}"))
        
        # 添加当前查询
        messages.append(HumanMessage(content=query))
        
        # 流式调用模型
        response = self.chat_model.stream(messages)
        
        # 收集完整响应
        full_response = ""
        for chunk in response:
            full_response += chunk.content
            yield chunk.content
        
        # 更新会话历史
        history.append(HumanMessage(content=query))
        history.append(AIMessage(content=full_response))


class AgentFactory:
    """
    Agent工厂类，用于创建不同类型的agents
    """
    
    @staticmethod
    def create_writing_agent(chat_model: ChatOpenAI) -> BaseAgent:
        """
        创建写作助手Agent
        
        Args:
            chat_model: 已配置的ChatOpenAI实例
        """
        system_prompt = """
        你是一位专业的小说作者，有丰富的小说经验和指导新人写小说经验。
        引导用户描述内容、设定以及想法，给出相对应的指导。
        核心能力：
        1. 教学指导：将复杂技巧拆解为三步实操法
        2. 文本分析：诊断+带注释修改示范
        3. 创作示范：生成符合网文平台特性的内容
        """
        return BaseAgent(chat_model=chat_model,
                        system_prompt=system_prompt, 
                        use_rag=True)
    
    @staticmethod
    def create_general_agent(chat_model: ChatOpenAI) -> BaseAgent:
        """
        创建通用助手Agent
        
        Args:
            chat_model: 已配置的ChatOpenAI实例
        """
        system_prompt = """
        你是一个通用的AI助手，能够回答各种问题。
        请以友好、专业的态度帮助用户解决问题。
        """
        return BaseAgent(chat_model=chat_model,
                        system_prompt=system_prompt, 
                        use_rag=False)
    
    @staticmethod
    def create_custom_agent(chat_model: ChatOpenAI,
                          system_prompt: str, 
                          use_rag: bool = False) -> BaseAgent:
        """
        创建自定义Agent
        
        Args:
            system_prompt: 系统角色定义
            use_rag: 是否使用RAG功能
            
        Returns:
            自定义Agent实例
        """
        return BaseAgent(system_prompt=system_prompt, use_rag=use_rag)