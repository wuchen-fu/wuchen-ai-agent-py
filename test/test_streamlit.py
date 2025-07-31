import time
import streamlit
import ollama
import re

if 'message' not in streamlit.session_state:
    streamlit.session_state['message'] = []

client = ollama.Client(host = 'http://localhost:11434')
streamlit.text("对话机器人")

streamlit.write("你好，我是无尘")

streamlit.divider()
# 正则去除ai返回的格式
pattern = r'(?i)<think\b[^>]*>.*?</think>'

prompt = streamlit.chat_input("请输入")

if prompt:
    streamlit.session_state['message'].append({'role':'user','content':prompt})
    for message in streamlit.session_state['message']:
        streamlit.chat_message(message['role']).markdown(message['content'])
    with streamlit.spinner('思考中'):
        response = client.chat(
            model='deepseek-r1:1.5b',
            messages=[{"role": "user", "content": prompt}]
        )
        # 记录ai回答并响应
        content = response['message']['content']
        content = re.sub(pattern, '', content, flags=re.DOTALL).strip()
        streamlit.chat_message('assistant').markdown(content)
        streamlit.session_state['message'].append({'role': 'assistant', 'content': content})
        streamlit.write("思考完成")


# 角色支持user、assistant、ai、human
# streamlit.chat_message("user").markdown("你是谁")
# streamlit.chat_message("assistant").markdown("我是机器人")
