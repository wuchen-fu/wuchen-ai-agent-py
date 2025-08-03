import os
import uuid

from dotenv import find_dotenv, load_dotenv
from langchain_core.messages import SystemMessage, HumanMessage,AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, MessagesState, START
from langgraph.checkpoint.redis import RedisSaver
from langgraph.store.redis import RedisStore
from langgraph.store.base import BaseStore

dotenv_path = find_dotenv(filename='.env.dev', usecwd=True)
load_dotenv(dotenv_path=dotenv_path)

chatModel = ChatOpenAI(
    model=os.getenv('QWEN_MODEL'),
    api_key=os.getenv('QWEN_API_KEY'),
    base_url=os.getenv('QWEN_URL'))

# Redis连接配置，包含认证信息
REDIS_HOST = os.getenv('REDIS_HOST')
REDIS_PORT = os.getenv('REDIS_PORT')
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD')  # 如果Redis设置了密码

# 构建Redis连接URI
DB_URI = f"redis://{REDIS_HOST}:{REDIS_PORT}"
ai_session_id = '215190a1-5c73-4455-a445-9c48bbde60da'
with (
    RedisStore.from_conn_string(DB_URI) as store,
    RedisSaver.from_conn_string(DB_URI) as checkpointer,
):
    store.setup()
    checkpointer.setup()

    def call_model(
        state: MessagesState,
        config: RunnableConfig,
        *,
        store: BaseStore,
    ):
        user_id = config["configurable"]["user_id"]
        namespace = ("memories", user_id)

        # 获取相关记忆（用于上下文理解）
        memories = store.search(namespace, query=str(state["messages"][-1].content))
        info = "\n".join([d.value["data"] for d in memories])
        system_msg = f"You are a helpful assistant talking to the user. User info: {info}"

        # 生成AI回复
        response = chatModel.invoke(
            [{"role": "system", "content": system_msg}] + state["messages"]
        )

        # 只记录最新的用户消息
        latest_user_message = None
        for message in reversed(state["messages"]):
            if message.type == "human":
                latest_user_message = message
                break

        if latest_user_message:
            store.put(namespace, str(ai_session_id), {"data": f"User: {latest_user_message.content}"})

        # 记录AI回复
        store.put(namespace, str(ai_session_id), {"data": f"AI: {response.content}"})
        return {"messages": response}

    builder = StateGraph(MessagesState)
    builder.add_node("call_model", call_model)  # 修正节点名称
    builder.add_edge(START, "call_model")
    # prompt_template = ChatPromptTemplate.from_messages([
    #     SystemMessage(content="你是一个翻译官，能根据用户给的内容翻译成指定的语言"),  # 提示 content值的意思是“将英语翻译成意大利语”
    #     HumanMessage(content='{user_msg}'),
    #     # ('system', '请将下面内容翻译成{language}'),
    #     # ('human', '{text}')
    # ])
    graph = builder.compile(
        checkpointer=checkpointer,
        store=store,
    )

    config = {
        "configurable": {
            "thread_id": ai_session_id,
            "user_id": "1_ai",
        }
    }

    # for chunk in graph.stream(
    #     {"messages": [{"role": "user", "content": "我是张三，你是谁？"}]},
    #     config,
    #     stream_mode="values",
    # ):
    #     chunk["messages"][-1].pretty_print()
    #
    # for chunk in graph.stream(
    #     {"messages": [{"role": "user", "content": "我叫什么"}]},
    #     config,
    #     stream_mode="values",
    # ):
    #     chunk["messages"][-1].pretty_print()
    #
    # for chunk in graph.stream(
    #     {"messages": [{"role": "user", "content": "你能干什么"}]},
    #     config,
    #     stream_mode="values",
    # ):
    #     chunk["messages"][-1].pretty_print()
    print("\n=== 查询当前历史 ===")
    work_state = list(graph.get_state(config))


    print("\n=== 查询会话历史 ===")
    try:
        history = list(graph.get_state_history(config))
        print(f"获取到 {len(history)} 个历史状态")

        if history:
            current_state = history[-1]  # 最新状态
            messages = current_state.values.get("messages", [])
            print("当前会话消息:")
            for i, message in enumerate(messages):
                print(f"  {i + 1}.  {message.content}")
        else:
            print("该会话暂无历史记录")
    except Exception as e:
        print(f"获取历史记录时出错: {e}")


