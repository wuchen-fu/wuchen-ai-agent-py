import ollama
# 获得客户端对象
client = ollama.Client(host = 'http://localhost:11434')

# print(client.list())
# print(client.show("deepseek-r1:1.5b"))
# print(client.ps())
# 模型对话
while True:
    prompt =  input("")
    response = client.chat(
        model = 'deepseek-r1:1.5b',
        messages = [{"role":"user","content":prompt}]
    )
    print(response['message']['content'])