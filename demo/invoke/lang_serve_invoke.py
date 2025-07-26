from langserve import RemoteRunnable
if __name__ == '__main__':
   client = RemoteRunnable('http://localhost:8101/chain/')
   resp = client.invoke({'text':'我喜欢你，翻译成英语和法语,返回方式为换行返回'})
   print(resp)