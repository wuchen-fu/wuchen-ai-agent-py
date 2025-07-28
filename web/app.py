import logging
import os
import sys

from dotenv import load_dotenv,find_dotenv
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains.history_aware_retriever import create_history_aware_retriever
from langchain.chains.retrieval import create_retrieval_chain
from langchain_community.chat_models import ChatOpenAI
from langchain_core.messages import AIMessage,HumanMessage,SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate,MessagesPlaceholder
from fastapi import FastAPI
from langserve import add_routes
from langchain_core.chat_history import BaseChatMessageHistory,InMemoryChatMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables import RunnableWithMessageHistory
from tools.rag_tool import get_vector_store

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
dotenv_path = find_dotenv(filename='.env.dev',usecwd=True)
# 加载 .env 文件
load_dotenv(dotenv_path=dotenv_path)
#LangSmish#调用AI检测平台
lang_chain_switch = os.getenv('LANGCHAIN_TRACING_V2')
lang_chain_api_key = os.getenv('LANGCHAIN_API_KEY')
lang_chain_server_name = os.getenv('LANGCHAIN_PROJECT')


chatModel = ChatOpenAI(
    model=os.getenv('DASH_SCOPE_MODEL'),
    api_key=os.getenv('DASH_SCOPE_API_KEY'),
    base_url=os.getenv('DASH_SCOPE_URL'))

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
    {context}
'''
prompt_template = ChatPromptTemplate.from_messages([
    ('system', system_prompt),
    # MessagesPlaceholder 占位插入消息类型
    MessagesPlaceholder(variable_name='chat_history'),
    ('human', '{input}'),
])

vector_store = get_vector_store ()


# print(vector_store.similarity_search_with_score("我想写小说", k=5))



# 提问链路
chain1 = create_stuff_documents_chain(chatModel,prompt_template)

son_system_prompt = '''
给我一个历史的聊天记录以即用户最新提出的问题。
在我们的聊天记录中引用我们的上下文内容，得到一个独立的问题。
当没有聊天记录的时候，不需要回答这个问题。
直接返回问题就可以了。
'''
history_prompt_temp = ChatPromptTemplate.from_messages([
    ('system', son_system_prompt),
    # MessagesPlaceholder 占位插入消息类型
    MessagesPlaceholder(variable_name='chat_history'),
    ('human', '{input}'),
])
# 子链路检索器检索最新的消息和对话历史
chain2 = create_history_aware_retriever(chatModel,vector_store.as_retriever(),history_prompt_temp)



parser = StrOutputParser()
# chain = prompt_template | chatModel
# 上下问对话记忆
store = {}
def get_session_history(session_id: str):
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]

chain = create_retrieval_chain(chain2,chain1)
'''
为指定类型链路添加历史消息，包装其它对象，并可以管理历史消息
input_messages_key-指定哪个部分应该在聊天历史中被跟踪和存储
history_messages_key-用于指定以前的消息如何注入提示中，当前使用MessagesPlaceholder
output_messages_key 指定哪个链路的输出存为历史记录
'''
do_message = RunnableWithMessageHistory(
    chain,
    get_session_history,
    input_messages_key='input',
    history_messages_key = 'chat_history',
    output_messages_key='answer'
)


config = {"configurable": {"session_id": "abc2"}}
def run():
    print("请说出你的问题(输入exit结束对话)")
    while True:
        user = input('')
        if user.lower() == "exit":
            break
        context = '"'+user+'"'
        resp = do_message.invoke(
            {
                'input': context,
            },
            config=config,
        )
        # for resp in do_message.stream(
        #         {
        #             'input': context,
        #         },
        #         config=config,
        # ):
            # print(resp.content)
        print(resp['answer'])
        print()


# app = FastAPI(
#     title='LangChain Chat  Server',
#     version='1.0',
#     description='使用LangChain Chat Server 智能助手',
# )
#
# add_routes(
#     app,
#     chain,
#     path="/chain",
# )

if __name__ == '__main__':
    # import uvicorn
    # uvicorn.run(app, host='localhost', port=8101)
    run()
