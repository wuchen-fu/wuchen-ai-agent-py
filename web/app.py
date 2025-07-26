import os
import sys

from dotenv import load_dotenv,find_dotenv
from langchain_community.chat_models import ChatOpenAI
from langchain_core.messages import AIMessage,HumanMessage,SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate,MessagesPlaceholder
from fastapi import FastAPI
from langserve import add_routes
from langchain_core.chat_history import BaseChatMessageHistory,InMemoryChatMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables import RunnableWithMessageHistory

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
prompt_template = ChatPromptTemplate.from_messages([
    ('system', '你是一个智能助手。尽你所能解决我的问题'),
    # MessagesPlaceholder来插入之前的对话历史
    MessagesPlaceholder(variable_name='user_msg'),
    # ('human', '{user_msg}'),
])




parser = StrOutputParser()
chain = prompt_template | chatModel
# 上下问对话记忆
store = {}
def get_session_history(session_id: str):
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]
do_message = RunnableWithMessageHistory(
    chain,
    get_session_history,
    input_messages_key='user_msg',
    # history_messages_key = 'history_msg',
)

config = {"configurable": {"session_id": "abc2"}}
def run():
    print("请说出你的问题(输入exit结束对话)")
    while True:
        user = input('')
        if user.lower() == "exit":
            break
        context = '"'+user+'"'
        for resp in do_message.stream(
                {
                    'user_msg': [HumanMessage(content=context)],
                },
                config=config,
        ):
            print(resp.content)
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
