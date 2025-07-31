import os
from dashscope import Generation as BaseApi
import sys
from dotenv import load_dotenv,find_dotenv
import dashscope


# 添加项目根目录到Python路径
# 获取当前脚本的绝对路径
# script_path = os.path.abspath(__file__)
#
# # 计算项目根目录（向上导航两级：从脚本所在目录 → test → 项目根目录）
# # 原代码只导航了两级，现在需要导航三级（如果脚本在demo的子目录中）
# # 请根据实际目录层级调整dirname的调用次数
# project_root = os.path.dirname(os.path.dirname(os.path.dirname(script_path)))  # 三次dirname
#
# # 添加项目根目录到Python路径
# sys.path.insert(0, project_root)
#






# env_path = os.path.join(project_root, '.env.dev')
# print(project_root)
# print(env_path)
dotenv_path = find_dotenv(filename='.env.dev',usecwd=True)
# 加载 .env 文件
load_dotenv(dotenv_path=dotenv_path)

# 对话记忆 对话流式输出

def chat_stream(messages):
    return BaseApi.call(
        api_key=os.getenv('DASH_SCOPE_API_KEY'),
        model='qwen-plus',
        messages=messages,
        result_from='message',
        stream=True,
        # 增量式流式输出
        incremental_output=True,
        # Qwen3模型通过enable_thinking参数控制思考过程（开源版默认True，商业版默认False）
        # 使用Qwen3开源版模型时，若未启用流式输出，请将下行取消注释，否则会报错
        enable_thinking=False
    )
    return response

messages = [
    {'role':'system','content':'You are a helpful assistant.'},
]
prompt = input("")
full_assistant = ''
while prompt:
    messages.append({'role':'user','content':prompt})
    rsps = chat_stream(messages)
    for rsp in rsps:
        full_assistant += rsp.output.text
        print(rsp.output.text)
        # assistant = rsp.output.text
    messages.append({'role':'assistant','content':full_assistant})
    print(f'{full_assistant}')
    full_assistant = ''
    prompt = input("")

# response = chat_stream(messages)
# if response.status_code == 200:
#     print(response)
#     print(response.output.text)
# else:
#     print(response.status_code)