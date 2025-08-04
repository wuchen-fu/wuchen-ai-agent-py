import logging
from typing import Optional, List, Dict, AsyncIterator, Iterator

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains.history_aware_retriever import create_history_aware_retriever
from langchain.chains.retrieval import create_retrieval_chain
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.messages import BaseMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableWithMessageHistory as LangChainRunnableWithMessageHistory, Runnable, \
    RunnableWithMessageHistory

from chat_memory.mongo_chat_memory import MongoChatMemory
from tools.rag_tool import get_vector_store
from tools.web_search_toolkit import WebSearchToolkit
from .base_agent import BaseAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 提示词模板
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


class WritingAgent(BaseAgent):
    """
    写作智能体，继承自BaseAgent
    实现具体的对话逻辑、历史记录管理等
    """

    AGENT_TYPE = "writing"
    AGENT_NAME = "写作助手"
    DEFAULT_SYSTEM_PROMPT = system_prompt

    def __init__(self, config: Optional[Dict] = None):
        """
        初始化写作智能体
        
        Args:
            config: 配置字典，可包含chat_model、system_prompt等
        """
        # 处理向后兼容性 - 如果config是chat_model实例而不是字典
        if config and not isinstance(config, dict):
            config = {"chat_model": config}

        super().__init__(config)

        # 从配置中获取system_prompt，如果没有则使用默认值
        self.system_prompt = self.config.get("system_prompt", self.DEFAULT_SYSTEM_PROMPT)

        # 初始化RAG相关组件
        self._initialize_rag_components()

        # 初始化Agent执行器
        self._initialize_agent_executor()
    def get_chat_model(self, provider_name: str = None, model_name: str = None):
        """
        获取指定的聊天模型

        Args:
            provider_name: 模型提供商名称
            model_name: 模型名称

        Returns:
            聊天模型实例
        """
        # 实现从BaseAgent继承来的模型获取方法
        return super().get_chat_model(provider_name, model_name)

    def _initialize_rag_components(self):
        """初始化RAG相关组件"""
        try:
            # 获取默认聊天模型
            chat_model = self.get_chat_model()
            if not chat_model:
                raise ValueError("无法获取聊天模型")

            # 初始化RAG组件
            self._initialize_rag_components_with_model(chat_model)

        except Exception as e:
            logger.error(f"初始化RAG组件失败: {e}")
            raise

    def _initialize_rag_components_with_model(self, chat_model):
        """使用指定模型初始化RAG相关组件"""
        try:
            # 初始化提示词模板
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
                ('system', self.system_prompt),
                MessagesPlaceholder(variable_name='chat_history'),
                ('human', '{input}'),
            ])

            # 绑定工具到模型
            bind_chat = chat_model.bind_tools(WebSearchToolkit().get_tools())

            # 初始化向量存储
            vector_store = get_vector_store()

            # 问题重写链
            qa_chain = create_history_aware_retriever(bind_chat, vector_store.as_retriever(), qa_prompt)

            # 提问链
            question_chain = create_stuff_documents_chain(bind_chat, prompt_template)

            # RAG链
            self.rag_chain = create_retrieval_chain(qa_chain, question_chain)

        except Exception as e:
            logger.error(f"使用指定模型初始化RAG组件失败: {e}")
            raise

    def _initialize_agent_executor(self):
        """初始化Agent执行器"""
        try:
            # 覆盖BaseAgent的history_chain以使用LangChain的实现
            self.history_chain = RunnableWithMessageHistory(
                self.rag_chain,
                MongoChatMemory.get_session_history,
                input_messages_key="input",
                history_messages_key="chat_history",
                output_messages_key="answer"
            )
        except Exception as e:
            logger.error(f"初始化Agent执行器失败: {e}")
            raise

    def _reinitialize_with_model(self, chat_model):
        """使用指定模型重新初始化组件"""
        try:
            # 重新初始化RAG组件
            self._initialize_rag_components_with_model(chat_model)

            # 重新初始化Agent执行器
            self._initialize_agent_executor()
        except Exception as e:
            logger.error(f"重新初始化组件失败: {e}")
            raise

    def chat(self, message: str, chat_id: str, user_id: Optional[str] = None,
            provider_name: Optional[str] = None, model_name: Optional[str] = None) -> str:
        """
        与智能体进行对话
        
        Args:
            message: 用户消息
            chat_id: 聊天ID
            user_id: 用户ID（可选）
            provider_name: 模型提供商名称（可选）
            model_name: 模型名称（可选）
            
        Returns:
            智能体的回复
        """
        try:
            # 如果指定了提供商或模型，则重新初始化组件
            if provider_name or model_name:
                chat_model = self.get_chat_model(provider_name, model_name)
                if chat_model:
                    self._reinitialize_with_model(chat_model)
            
            # 准备输入数据
            input_data = {"input": message}

            # 使用带历史记录的链进行调用
            config = {"configurable": {"session_id": chat_id}}
            if user_id:
                config["configurable"]["user_id"] = user_id
                
            response = self.history_chain.invoke(input_data, config=config)

            # 返回响应内容
            if isinstance(response, dict):
                return response.get("answer", str(response))
            else:
                return str(response)

        except Exception as e:
            logger.error(f"智能体对话出错: {e}")
            return "抱歉，我在处理您的问题时遇到了错误。"

    def stream_chat(self, message: str, chat_id: str, user_id: Optional[str] = None,
                   provider_name: Optional[str] = None, model_name: Optional[str] = None) -> Iterator[str]:
        """
        与智能体进行流式对话
        
        Args:
            message: 用户消息
            chat_id: 聊天ID
            user_id: 用户ID（可选）
            provider_name: 模型提供商名称（可选）
            model_name: 模型名称（可选）
            
        Yields:
            智能体的回复片段
        """
        try:
            # 如果指定了提供商或模型，则重新初始化组件
            if provider_name or model_name:
                chat_model = self.get_chat_model(provider_name, model_name)
                if chat_model:
                    self._reinitialize_with_model(chat_model)
            
            # 准备输入数据
            input_data = {"input": message}
            
            # 使用带历史记录的链进行流式调用
            config = {"configurable": {"session_id": chat_id}}
            if user_id:
                config["configurable"]["user_id"] = user_id
                
            for chunk in self.history_chain.stream(input_data, config=config):
                # 处理不同类型的响应
                if isinstance(chunk, dict):
                    # 如果是字典，尝试提取answer或content字段
                    content = chunk.get("answer") or chunk.get("content", "")
                    if content:
                        yield content
                else:
                    # 如果是字符串或其他类型，直接转换为字符串
                    content = str(chunk)
                    if content:
                        yield content
                        
        except Exception as e:
            logger.error(f"智能体流式对话出错: {e}")
            yield "抱歉，我在处理您的问题时遇到了错误。"

    async def achat(self, message: str, chat_id: str, user_id: Optional[str] = None,
                   provider_name: Optional[str] = None, model_name: Optional[str] = None) -> str:
        """
        异步与智能体进行对话
        
        Args:
            message: 用户消息
            chat_id: 聊天ID
            user_id: 用户ID（可选）
            provider_name: 模型提供商名称（可选）
            model_name: 模型名称（可选）
            
        Returns:
            智能体的回复
        """
        try:
            # 如果指定了提供商或模型，则重新初始化组件
            if provider_name or model_name:
                chat_model = self.get_chat_model(provider_name, model_name)
                if chat_model:
                    self._reinitialize_with_model(chat_model)
            
            # 准备输入数据
            input_data = {"input": message}

            # 使用带历史记录的链进行调用
            config = {"configurable": {"session_id": chat_id}}
            if user_id:
                config["configurable"]["user_id"] = user_id
                
            response = await self.history_chain.ainvoke(input_data, config=config)

            # 返回响应内容
            if isinstance(response, dict):
                return response.get("answer", str(response))
            else:
                return str(response)

        except Exception as e:
            logger.error(f"智能体对话出错: {e}")
            return "抱歉，我在处理您的问题时遇到了错误。"

    async def astream_chat(self, message: str, chat_id: str, user_id: Optional[str] = None, 
                          provider_name: Optional[str] = None, model_name: Optional[str] = None) -> AsyncIterator[str]:
        """
        异步与智能体进行流式对话
        
        Args:
            message: 用户消息
            chat_id: 聊天ID
            user_id: 用户ID（可选）
            provider_name: 模型提供商名称（可选）
            model_name: 模型名称（可选）
            
        Yields:
            智能体的回复片段
        """
        try:
            # 如果指定了提供商或模型，则重新初始化组件
            if provider_name or model_name:
                chat_model = self.get_chat_model(provider_name, model_name)
                if chat_model:
                    self._reinitialize_with_model(chat_model)
            
            # 准备输入数据
            input_data = {"input": message}
            
            # 使用带历史记录的链进行流式调用
            config = {"configurable": {"session_id": chat_id}}
            if user_id:
                config["configurable"]["user_id"] = user_id
                
            async for chunk in self.history_chain.astream(input_data, config=config):
                # 处理不同类型的响应
                if isinstance(chunk, dict):
                    # 如果是字典，尝试提取answer或content字段
                    content = chunk.get("answer") or chunk.get("content", "")
                    if content:
                        yield content
                else:
                    # 如果是字符串或其他类型，直接转换为字符串
                    content = str(chunk)
                    if content:
                        yield content
                        
        except Exception as e:
            logger.error(f"智能体流式对话出错: {e}")
            yield "抱歉，我在处理您的问题时遇到了错误."

    def get_history(self, chat_id: str) -> List[BaseMessage]:
        """
        获取指定会话的历史记录
        
        Args:
            chat_id: 聊天ID
            
        Returns:
            历史消息列表
        """
        try:
            history = MongoChatMemory.get_session_history(chat_id)
            return history.messages
        except Exception as e:
            logger.error(f"获取历史记录出错: {e}")
            return []

    def clear_history(self, chat_id: str):
        """
        清除指定会话的历史记录
        
        Args:
            chat_id: 聊天ID
        """
        try:
            history = MongoChatMemory.get_session_history(chat_id)
            history.clear()
        except Exception as e:
            logger.error(f"清除历史记录出错: {e}")