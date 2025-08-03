#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简单工具调用测试
"""
import os
from dotenv import find_dotenv, load_dotenv
from langchain_openai.chat_models import ChatOpenAI
from langchain_core.tools import BaseTool, StructuredTool, tool
from langchain_core.messages import HumanMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableWithMessageHistory
from langchain_core.chat_history import InMemoryChatMessageHistory

# 加载环境变量
dotenv_path = find_dotenv(filename='../.env.dev', usecwd=True)
if not dotenv_path:
    print("警告: 未找到.env.dev文件，使用系统环境变量")
else:
    load_dotenv(dotenv_path=dotenv_path)
    print(f"已加载环境变量文件: {dotenv_path}")

# 定义一个简单工具
@tool
def get_current_time():
    """获取当前时间"""
    import datetime
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# 定义另一个工具
@tool
def add_numbers(a: int, b: int) -> int:
    """将两个数字相加"""
    return a + b

# 获取环境变量
model = os.getenv('DASH_SCOPE_MODEL')
api_key = os.getenv('DASH_SCOPE_API_KEY')
base_url = os.getenv('DASH_SCOPE_URL')

# 检查环境变量
if not model:
    raise ValueError("未设置DASH_SCOPE_MODEL环境变量")
if not api_key:
    raise ValueError("未设置DASH_SCOPE_API_KEY环境变量")
if not base_url:
    raise ValueError("未设置DASH_SCOPE_URL环境变量")

print(f"使用模型: {model}")
print(f"API基础URL: {base_url}")

# 初始化聊天模型
chat_model = ChatOpenAI(
    model=model,
    api_key=api_key,
    base_url=base_url
)

# 创建提示词模板
prompt_template = ChatPromptTemplate.from_messages([
    ("system", "你是一个有用的助手，会使用工具来回答问题。"),
    ("placeholder", "{chat_history}"),
    ("human", "{input}")
])

# 创建工具列表
tools = [get_current_time, add_numbers]

# 绑定工具到聊天模型
chat_model_with_tools = chat_model.bind_tools(tools)

# 设置消息历史
chat_history = InMemoryChatMessageHistory()

def test_tool_calls():
    """测试工具调用和响应"""
    print("=== 测试工具调用和响应 ===")

    # 第一次调用：请求当前时间
    print("发送请求: 现在几点了?")
    response = chat_model_with_tools.invoke([
        HumanMessage(content="现在几点了?")
    ])
    print(f"响应: {response}")

    # 检查是否有工具调用
    if hasattr(response, 'tool_calls') and response.tool_calls:
        print(f"工具调用: {response.tool_calls}")

        # 处理工具调用
        tool_messages = []
        for tool_call in response.tool_calls:
            tool_name = tool_call['name']
            tool_args = tool_call['args']
            tool_call_id = tool_call['id']
            print(f"处理工具调用: {tool_name}, 参数: {tool_args}, id: {tool_call_id}")

            # 查找工具
            tool = next((t for t in tools if t.name == tool_name), None)
            if tool:
                try:
                    result = tool.invoke(tool_args)
                    print(f"工具 {tool_name} 执行结果: {result}")
                    tool_message = ToolMessage(
                        tool_call_id=tool_call_id,
                        content=str(result)
                    )
                    tool_messages.append(tool_message)
                    print(f"添加工具响应消息: {tool_message}")
                except Exception as e:
                    print(f"执行工具 {tool_name} 时出错: {e}")
                    tool_message = ToolMessage(
                        tool_call_id=tool_call_id,
                        content=f"执行工具时出错: {str(e)}"
                    )
                    tool_messages.append(tool_message)
            else:
                print(f"未找到工具: {tool_name}")
                tool_message = ToolMessage(
                    tool_call_id=tool_call_id,
                    content=f"未找到工具: {tool_name}"
                )
                tool_messages.append(tool_message)

        # 第二次调用：传入工具响应
        print("\n发送带有工具响应的请求...")
        response_with_tool = chat_model_with_tools.invoke([
            HumanMessage(content="现在几点了?"),
            response,
            *tool_messages
        ])
        print(f"最终响应: {response_with_tool}")

    # 测试数字相加
    print("\n发送请求: 3加5等于多少?")
    response = chat_model_with_tools.invoke([
        HumanMessage(content="3加5等于多少?")
    ])
    print(f"响应: {response}")

    if hasattr(response, 'tool_calls') and response.tool_calls:
        print(f"工具调用: {response.tool_calls}")
        tool_messages = []
        for tool_call in response.tool_calls:
            tool_name = tool_call['name']
            tool_args = tool_call['args']
            tool_call_id = tool_call['id']
            print(f"处理工具调用: {tool_name}, 参数: {tool_args}, id: {tool_call_id}")

            tool = next((t for t in tools if t.name == tool_name), None)
            if tool:
                result = tool.invoke(tool_args)
                print(f"工具 {tool_name} 执行结果: {result}")
                tool_message = ToolMessage(
                    tool_call_id=tool_call_id,
                    content=str(result)
                )
                tool_messages.append(tool_message)
            else:
                print(f"未找到工具: {tool_name}")

        response_with_tool = chat_model_with_tools.invoke([
            HumanMessage(content="3加5等于多少?"),
            response,
            *tool_messages
        ])
        print(f"最终响应: {response_with_tool}")

if __name__ == "__main__":
    test_tool_calls()