import os

from dotenv import find_dotenv, load_dotenv
from langchain_core.runnables import Runnable,RunnableLambda,RunnablePassthrough
from document_loader_invoke import DocumentLoaderInvoke
from langchain_community.embeddings import DashScopeEmbeddings,HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_community.chat_models import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

'''
从本地加载文档
对文档进行切片
对切片的元数据处理metadata
使用Embedding模型处理存入chrom向量库
'''
dotenv_path = find_dotenv(filename='.env.dev',usecwd=True)
# 加载 .env 文件
load_dotenv(dotenv_path=dotenv_path)
loder = DocumentLoaderInvoke()
documents = loder.load_markdowns()

vector_store = Chroma.from_documents(
    documents,
    HuggingFaceEmbeddings()

    # DashScopeEmbeddings(
    #     dashscope_api_key=os.getenv("DASHSCOPE_API_KEY"),
    #     model="text-embedding-v1"
    # )
)
chatModel = ChatOpenAI(
    model=os.getenv('DASH_SCOPE_MODEL'),
    api_key=os.getenv('DASH_SCOPE_API_KEY'),
    base_url=os.getenv('DASH_SCOPE_URL'))

message = '''
结合上下文回答问题
{question}
上下文
{context}
'''
prompt = ChatPromptTemplate.from_messages([('human',message)])

search_vector_store = RunnableLambda(vector_store.similarity_search).bind(k=1)
chain = {'question':RunnablePassthrough(),'context':search_vector_store} | prompt | chatModel
# serach_text = ['大纲怎么设计','我该怎么写小说']
result = chain.invoke('我想写小说')
print(result.content)

# print(vector_store.similarity_search_with_vectors("大纲怎么设计"))
# print(documents)