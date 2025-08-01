import os
import sys
from dotenv import find_dotenv, load_dotenv
from langchain_mongodb import MongoDBChatMessageHistory
from langchain_openai.chat_models import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableWithMessageHistory

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

# 导入自定义的增强版MongoDB聊天历史类
from chat_memory.mongo_chat_memory import EnhancedMongoDBChatMessageHistory

# 加载环境变量
dotenv_path = find_dotenv(filename='.env.dev', usecwd=True)
load_dotenv(dotenv_path=dotenv_path)


def test_mongodb_chat_message_history():
    print("=== 测试langchain-ongoDB聊天历史类 ===")
    mongo_url = 'mongodb://{}:{}@{}:{}/{}?authSource=admin'.format(
        os.getenv('DB_MONGO_USER'),
        os.getenv('DB_MONGO_PASSWORD'),
        os.getenv('DB_MONGO_URL'),
        os.getenv('DB_MONGO_PORT'),
        os.getenv('DB_MONGO_DATABASE')
    )
    session_id = "custom_test_session"
    user_id = "custom_test_user"

    history = MongoDBChatMessageHistory(
        connection_string=mongo_url,
        session_id=session_id,
        # user_id=user_id,
        database_name=os.getenv('DB_MONGO_DATABASE'),
    )
    print("   创建成功")

    # 清除可能存在的历史记录
    history.clear()
    print("2. 清除可能存在的历史记录")

    # 测试添加消息
    print("3. 添加测试消息")
    history.add_user_message("用户消息1: 你好，这是一个测试")
    history.add_ai_message("AI消息1: 你好！我收到了你的消息")
    history.add_user_message("用户消息2: 请告诉我时间戳功能是否正常工作")
    history.add_ai_message("AI消息2: 是的，每条消息都会带有时间戳")
    print("   消息添加成功")

    # 测试获取消息
    print("4. 获取消息")
    messages = history.messages
    print(f"   获取到 {len(messages)} 条消息:")
    for i, message in enumerate(messages, 1):
        print(f"   {i}. {message.type}: {message.content}")

    # 验证消息类型和内容
    print("5. 验证消息类型和内容")
    expected_messages = [
        ("human", "用户消息1: 你好，这是一个测试"),
        ("ai", "AI消息1: 你好！我收到了你的消息"),
        ("human", "用户消息2: 请告诉我时间戳功能是否正常工作"),
        ("ai", "AI消息2: 是的，每条消息都会带有时间戳")
    ]


def test_custom_enhanced_mongo_history():
    """测试自定义的EnhancedMongoDBChatMessageHistory类"""
    print("=== 测试自定义EnhancedMongoDBChatMessageHistory类 ===")
    
    try:
        # 构建MongoDB连接字符串
        # 本地或普通MongoDB实例
        mongo_url = 'mongodb://{}:{}@{}:{}/{}?authSource=admin'.format(
            os.getenv('DB_MONGO_USER'),
            os.getenv('DB_MONGO_PASSWORD'),
            os.getenv('DB_MONGO_URL'),
            os.getenv('DB_MONGO_PORT'),
            os.getenv('DB_MONGO_DATABASE')
        )

        
        session_id = "custom_test_session"
        user_id = "custom_test_user"
        
        # 创建EnhancedMongoDBChatMessageHistory实例
        print(f"1. 创建EnhancedMongoDBChatMessageHistory实例")
        print(f"   会话ID: {session_id}")
        print(f"   用户ID: {user_id}")
        
        history = EnhancedMongoDBChatMessageHistory(
            connection_string=mongo_url,
            session_id=session_id,
            user_id=user_id,
            database_name=os.getenv('DB_MONGO_DATABASE'),
        )
        print("   创建成功")
        
        # 清除可能存在的历史记录
        history.clear()
        print("2. 清除可能存在的历史记录")
        
        # 测试添加消息
        print("3. 添加测试消息")
        history.add_user_message("用户消息1: 你好，这是一个测试")
        history.add_ai_message("AI消息1: 你好！我收到了你的消息")
        history.add_user_message("用户消息2: 请告诉我时间戳功能是否正常工作")
        history.add_ai_message("AI消息2: 是的，每条消息都会带有时间戳")
        print("   消息添加成功")
        
        # 测试获取消息
        print("4. 获取消息")
        messages = history.messages
        print(f"   获取到 {len(messages)} 条消息:")
        for i, message in enumerate(messages, 1):
            print(f"   {i}. {message.type}: {message.content}")
        
        # 验证消息类型和内容
        print("5. 验证消息类型和内容")
        expected_messages = [
            ("human", "用户消息1: 你好，这是一个测试"),
            ("ai", "AI消息1: 你好！我收到了你的消息"),
            ("human", "用户消息2: 请告诉我时间戳功能是否正常工作"),
            ("ai", "AI消息2: 是的，每条消息都会带有时间戳")
        ]
        
        all_correct = True
        for i, (expected_type, expected_content) in enumerate(expected_messages, 1):
            if i <= len(messages):
                actual_message = messages[i-1]
                if actual_message.type == expected_type and actual_message.content == expected_content:
                    print(f"   消息{i}验证通过: {expected_type} - {expected_content}")
                else:
                    print(f"   消息{i}验证失败:")
                    print(f"     期望: {expected_type} - {expected_content}")
                    print(f"     实际: {actual_message.type} - {actual_message.content}")
                    all_correct = False
            else:
                print(f"   消息{i}缺失")
                all_correct = False
        
        if all_correct and len(messages) == len(expected_messages):
            print("   所有消息验证通过！")
        else:
            print("   部分消息验证失败！")
        
        # 验证数据库中的记录包含用户ID和时间戳
        print("6. 验证数据库记录包含用户ID和时间戳")
        try:
            # 直接从数据库查询文档
            docs = list(history.collection.find({
                "SessionId": session_id,
                "UserId": user_id
            }))
            
            print(f"   数据库中找到 {len(docs)} 条记录")
            for i, doc in enumerate(docs, 1):
                # 检查必需字段
                has_session_id = "SessionId" in doc
                has_user_id = "UserId" in doc
                has_timestamp = "timestamp" in doc
                has_history = history.history_key in doc
                
                print(f"   记录{i}:")
                print(f"     包含SessionId: {has_session_id}")
                print(f"     包含UserId: {has_user_id}")
                print(f"     包含timestamp: {has_timestamp}")
                print(f"     包含History: {has_history}")
                
                if has_session_id and has_user_id and has_timestamp and has_history:
                    print(f"     记录{i}结构验证通过")
                else:
                    print(f"     记录{i}结构验证失败")
                    all_correct = False
                    
        except Exception as e:
            print(f"   验证数据库记录时出错: {e}")
            all_correct = False
        
        # 测试清除历史记录
        # print("7. 测试清除历史记录")
        # history.clear()
        # messages = history.messages
        # print(f"   清除后剩余 {len(messages)} 条消息")
        
        # if len(messages) == 0:
        #     print("   历史记录清除成功！")
        # else:
        #     print("   历史记录清除失败！")
        #     all_correct = False
        
        # if all_correct:
        #     print("EnhancedMongoDBChatMessageHistory类测试通过！\n")
        # else:
        #     print("EnhancedMongoDBChatMessageHistory类测试失败！\n")
        
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

def test_mongo_store():
    """测试MongoStore类的基本功能"""
    print("=== 测试MongoStore类 ===")
    
    try:
        # 构建MongoDB连接字符串
        if os.getenv('DB_MONGO_URL') and 'cluster' in os.getenv('DB_MONGO_URL', ''):
            # MongoDB Atlas集群（使用SRV记录）
            mongo_url = 'mongodb+srv://{}:{}@{}/{}?authSource=admin'.format(
                os.getenv('DB_MONGO_USER'),
                os.getenv('DB_MONGO_PASSWORD'),
                os.getenv('DB_MONGO_URL'),
                os.getenv('DB_MONGO_DATABASE')
            )
        else:
            # 本地或普通MongoDB实例
            mongo_url = 'mongodb://{}:{}@{}:{}/{}?authSource=admin'.format(
                os.getenv('DB_MONGO_USER'),
                os.getenv('DB_MONGO_PASSWORD'),
                os.getenv('DB_MONGO_URL'),
                os.getenv('DB_MONGO_PORT'),
                os.getenv('DB_MONGO_DATABASE')
            )
        
        session_id = "test_session_1"
        user_id = "user_123"
        
        # 创建EnhancedMongoDBChatMessageHistory实例
        print(f"1. 创建EnhancedMongoDBChatMessageHistory实例，会话ID: {session_id}，用户ID: {user_id}")
        history = EnhancedMongoDBChatMessageHistory(
            connection_string=mongo_url,
            session_id=session_id,
            user_id=user_id,
            database_name=os.getenv('DB_MONGO_DATABASE'),
        )
        print("   创建成功")
        
        # 清除可能存在的历史记录
        history.clear()
        
        # 测试添加消息
        print("2. 添加消息")
        history.add_user_message("用户消息1: 你好")
        history.add_ai_message("AI消息1: 你好！有什么可以帮助你的吗？")
        history.add_user_message("用户消息2: 我想了解MongoDB的使用")
        print("   消息添加成功")
        
        # 测试获取消息
        print("3. 获取消息")
        messages = history.messages
        print(f"   获取到 {len(messages)} 条消息:")
        for i, message in enumerate(messages, 1):
            print(f"   {i}. {message.type}: {message.content}")
        
        # 测试清除历史记录
        print("4. 清除历史记录")
        history.clear()
        messages = history.messages
        print(f"   清除后剩余 {len(messages)} 条消息")
        
        print("EnhancedMongoDBChatMessageHistory测试完成！\n")
        
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

def test_llm_with_mongo_history():
    """测试使用MongoDB存储历史记录的LLM对话"""
    print("=== 测试LLM与MongoDB历史记录集成 ===")
    
    try:
        # 初始化聊天模型
        chat_model = ChatOpenAI(
            model=os.getenv('DASH_SCOPE_MODEL', 'gpt-3.5-turbo'),
            api_key=os.getenv('DASH_SCOPE_API_KEY'),
            base_url=os.getenv('DASH_SCOPE_URL', 'https://api.openai.com/v1')
        )
        
        # 创建提示模板
        prompt = ChatPromptTemplate.from_messages([
            ("system", "你是一个有帮助的AI助手。请根据用户的提问提供准确的回答。"),
            ("placeholder", "{chat_history}"),
            ("human", "{input}")
        ])
        
        # 构建链
        chain = prompt | chat_model
        
        # 构建MongoDB连接字符串
        if os.getenv('DB_MONGO_URL') and 'cluster' in os.getenv('DB_MONGO_URL', ''):
            # MongoDB Atlas集群（使用SRV记录）
            mongo_url = 'mongodb+srv://{}:{}@{}/{}?authSource=admin'.format(
                os.getenv('DB_MONGO_USER'),
                os.getenv('DB_MONGO_PASSWORD'),
                os.getenv('DB_MONGO_URL'),
                os.getenv('DB_MONGO_DATABASE')
            )
        else:
            # 本地或普通MongoDB实例
            mongo_url = 'mongodb://{}:{}@{}:{}/{}?authSource=admin'.format(
                os.getenv('DB_MONGO_USER'),
                os.getenv('DB_MONGO_PASSWORD'),
                os.getenv('DB_MONGO_URL'),
                os.getenv('DB_MONGO_PORT'),
                os.getenv('DB_MONGO_DATABASE')
            )
        
        session_id = "llm_test_session"
        user_id = "llm_user_123"
        
        # 创建带历史记录的链
        chain_with_history = RunnableWithMessageHistory(
            chain,
            lambda session_id_param: EnhancedMongoDBChatMessageHistory(
                connection_string=mongo_url,
                session_id=session_id_param,  # 正确传递session_id参数
                user_id=user_id,
                database_name=os.getenv('DB_MONGO_DATABASE')
            ),
            input_messages_key="input",
            history_messages_key="chat_history"
        )
        
        print(f"使用会话ID: {session_id}，用户ID: {user_id}")
        
        # 第一轮对话
        print("\n--- 第一轮对话 ---")
        response = chain_with_history.invoke(
            {"input": "你好，我叫小明。你能记住我的名字吗？"},
            config={"configurable": {"session_id": session_id}}
        )
        print(f"用户: 你好，我叫小明。你能记住我的名字吗？")
        print(f"AI: {response.content}")
        
        # 第二轮对话
        print("\n--- 第二轮对话 ---")
        response = chain_with_history.invoke(
            {"input": "我刚才告诉你我的名字是什么了？"},
            config={"configurable": {"session_id": session_id}}
        )
        print(f"用户: 我刚才告诉你我的名字是什么了？")
        print(f"AI: {response.content}")
        
        # 第三轮对话
        print("\n--- 第三轮对话 ---")
        response = chain_with_history.invoke(
            {"input": "请告诉我一些关于MongoDB的信息"},
            config={"configurable": {"session_id": session_id}}
        )
        print(f"用户: 请告诉我一些关于MongoDB的信息")
        print(f"AI: {response.content}")
        
        # 查看存储的历史记录
        print("\n--- 存储的历史记录 ---")
        history = EnhancedMongoDBChatMessageHistory(
            connection_string=mongo_url,
            session_id=session_id,
            user_id=user_id,
            database_name=os.getenv('DB_MONGO_DATABASE')
        )
        messages = history.messages
        print(f"共存储 {len(messages)} 条消息:")
        for i, message in enumerate(messages, 1):
            print(f"  {i}. {message.type}: {message.content}")
        
        print("LLM与MongoDB历史记录集成测试完成！\n")
        
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

def test_chinese_encoding():
    """测试中文编码存储"""
    print("=== 测试中文编码存储 ===")
    
    try:
        # 构建MongoDB连接字符串
        if os.getenv('DB_MONGO_URL') and 'cluster' in os.getenv('DB_MONGO_URL', ''):
            # MongoDB Atlas集群（使用SRV记录）
            mongo_url = 'mongodb+srv://{}:{}@{}/{}?authSource=admin'.format(
                os.getenv('DB_MONGO_USER'),
                os.getenv('DB_MONGO_PASSWORD'),
                os.getenv('DB_MONGO_URL'),
                os.getenv('DB_MONGO_DATABASE')
            )
        else:
            # 本地或普通MongoDB实例
            mongo_url = 'mongodb://{}:{}@{}:{}/{}?authSource=admin'.format(
                os.getenv('DB_MONGO_USER'),
                os.getenv('DB_MONGO_PASSWORD'),
                os.getenv('DB_MONGO_URL'),
                os.getenv('DB_MONGO_PORT'),
                os.getenv('DB_MONGO_DATABASE')
            )
        
        session_id = "chinese_test_session_你好呀_test"
        user_id = "chinese_user_789"
        
        # 创建EnhancedMongoDBChatMessageHistory实例
        print(f"1. 创建EnhancedMongoDBChatMessageHistory实例，会话ID: {session_id}，用户ID: {user_id}")
        history = EnhancedMongoDBChatMessageHistory(
            connection_string=mongo_url,
            session_id=session_id,
            user_id=user_id,
            database_name=os.getenv('DB_MONGO_DATABASE'),
        )
        print("   创建成功")
        
        # 测试添加中文消息
        print("2. 添加中文消息")
        chinese_messages = [
            "你好，世界！",
            "今天天气很好。",
            "MongoDB是一个强大的NoSQL数据库。",
            "我正在测试中文字符的存储和检索。",
            "特殊字符测试：！@#￥%……&*（）——+-={}【】；：\"'《》，。？/\\|"
        ]
        
        for i, msg in enumerate(chinese_messages, 1):
            history.add_user_message(f"消息{i}: {msg}")
            print(f"   添加消息: {msg}")
        
        # 测试获取中文消息
        print("3. 获取中文消息")
        messages = history.messages
        print(f"   获取到 {len(messages)} 条消息:")
        for i, message in enumerate(messages, 1):
            print(f"   {i}. {message.type}: {message.content}")
            
        # 验证中文内容是否正确
        print("4. 验证中文内容")
        all_correct = True
        for i, (original, retrieved) in enumerate(zip(chinese_messages, [msg.content[4:] for msg in messages]), 1):  # 去掉"消息{i}: "前缀
            if original == retrieved:
                print(f"   消息{i} 验证通过")
            else:
                print(f"   消息{i} 验证失败: 原始='{original}', 检索='{retrieved}'")
                all_correct = False
                
        if all_correct:
            print("   所有中文消息验证通过！")
        else:
            print("   部分中文消息验证失败！")
            
        # 验证数据库中存储的内容
        print("5. 验证数据库中存储的原始内容")
        try:
            import json
            
            # 直接从数据库查询文档
            docs = list(history.collection.find({
                "SessionId": session_id,
                "UserId": user_id
            }))
            
            print(f"   数据库中找到 {len(docs)} 条记录")
            for i, doc in enumerate(docs, 1):
                history_content = doc[history.history_key]
                timestamp = doc.get("timestamp", "N/A")
                print(f"   记录{i}的原始内容: {history_content[:100]}...")
                print(f"   记录{i}的时间戳: {timestamp}")
                # 检查是否包含Unicode转义序列
                if "\\u" in history_content:
                    print(f"   警告: 记录{i}包含Unicode转义序列")
                else:
                    print(f"   记录{i}正常存储中文字符")
        except Exception as e:
            print(f"   验证数据库内容时出错: {e}")
        
        print("中文编码测试完成！\n")
        
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

def main():
    """主测试函数"""
    print("开始测试MongoDB聊天历史存储功能...\n")
    # test_mongodb_chat_message_history()

    # 测试自定义的EnhancedMongoDBChatMessageHistory类
    test_custom_enhanced_mongo_history()
    
    # # 测试直接使用EnhancedMongoDBChatMessageHistory
    # test_mongo_store()
    #
    # # 测试LLM与MongoDB历史记录集成
    test_llm_with_mongo_history()
    #
    # # 测试中文编码存储
    # test_chinese_encoding()
    
    print("所有测试完成！")

if __name__ == "__main__":
    main()