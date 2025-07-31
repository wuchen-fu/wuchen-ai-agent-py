import os
from dotenv import load_dotenv,find_dotenv
from langchain_community.chat_models import ChatOpenAI
from langchain_core.messages import AIMessage,HumanMessage,SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

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
# 正常提示词
# messages = [
#     SystemMessage(content="你是一个翻译官，能根据用户给的内容翻译成指定的语言"), # 提示 content值的意思是“将英语翻译成意大利语”
#     HumanMessage(content="我今天想吃苹果"),
# ]
# resp = chatModel.invoke(messages)
parser = StrOutputParser()
# 链路写法
# chain = chatModel | parser
# print(chain)

# prompt动态模板

prompt_template = ChatPromptTemplate.from_messages([
    ('system', '请将下面内容翻译成{language}'),
    ('human', '{text}')
])
chain = prompt_template | chatModel | parser

language = input('请输入要翻译的语言')
text = input('请输入要翻译的内容')
language = '"'+ language +'"'
text = '"'+ text +'"'
print(chain.invoke({ 'language': language, 'text': text }))
