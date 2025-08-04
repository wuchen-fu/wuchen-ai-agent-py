#!/usr/bin/env python3
"""
测试内容格式化效果
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.agent.db_agent import DBAgent

def test_content_formatting():
    """测试内容格式化效果"""
    print("开始测试内容格式化效果...")
    
    # 创建DBAgent实例
    agent = DBAgent()
    
    # 测试原始内容
    test_content = """
    1. 数据库概览
    数据库中有以下表：
    - users: 用户信息表
    - orders: 订单表
    - products: 产品表
    
    2. 查询分析
    根据您的问题，我需要查询用户表来获取用户信息。
    
    3. 执行结果
    | id | name | email | created_at |
    |----|------|-------|------------|
    | 1  | 张三 | zhangsan@example.com | 2024-01-01 |
    | 2  | 李四 | lisi@example.com | 2024-01-02 |
    
    4. 总结
    查询成功返回了2条用户记录。
    """
    
    print("原始内容:")
    print("-" * 50)
    print(test_content)
    print("-" * 50)
    
    # 测试格式化后的内容
    formatted_content = agent._format_content_for_display(test_content)
    print("\n格式化后的内容:")
    print("-" * 50)
    print(formatted_content)
    print("-" * 50)
    
    # 测试分割效果
    print("\n分割后的片段:")
    print("-" * 50)
    for i, piece in enumerate(agent._split_content_for_streaming(formatted_content)):
        print(f"片段 {i+1}: {repr(piece)}")
    print("-" * 50)

def test_streaming_with_formatting():
    """测试带格式化的流式输出"""
    print("\n开始测试带格式化的流式输出...")
    
    try:
        # 创建DBAgent实例
        agent = DBAgent()
        
        # 测试消息
        test_message = "查询数据库中有哪些表"
        chat_id = "test_formatting_001"
        
        print(f"测试消息: {test_message}")
        print("开始流式输出:")
        print("-" * 50)
        
        # 测试流式输出
        for i, piece in enumerate(agent.stream_chat(test_message, chat_id)):
            print(f"片段 {i+1}: {piece}")
            
        print("-" * 50)
        print("流式输出完成")
        
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_content_formatting()
    test_streaming_with_formatting() 