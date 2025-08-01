#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
DB Agent 测试示例
"""

import asyncio
import os
from dotenv import find_dotenv, load_dotenv

# 添加项目根目录到Python路径
import sys
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

from web.agent.db_agent import DBAgent

# 加载环境变量
dotenv_path = find_dotenv(filename='../.env.dev', usecwd=True)
load_dotenv(dotenv_path=dotenv_path)

chid = 'asdasdajsdsa222'

def test_db_agent_sync():
    """测试同步数据库代理"""
    print("=== 测试同步数据库代理 ===")
    
    try:
        # 创建数据库代理实例
        print("创建数据库代理实例...")
        db_agent = DBAgent()
        print("数据库代理实例创建成功")
        
        print("发送查询: 当前使用的是什么数据库")
        resp = db_agent.chat("当前使用的是什么数据库", chid, "test_user")
        print(f"回复: {resp}")
        
        # 测试第二条消息，验证历史记录功能
        # resp2 = db_agent.chat("我刚才问了什么", chid, "test_user")
        # print(f"回复: {resp2}")
                
    except Exception as e:
        print(f"测试出错: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        raise


async def test_db_agent_async():
    """测试异步数据库代理"""
    print("\n=== 测试异步数据库代理 ===")
    
    try:
        # 创建数据库代理实例
        db_agent = DBAgent()
        
        # 测试查询
        test_queries = [
            "描述ai_chat_message表的结构",
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n--- 异步测试查询 {i}: {query} ---")
            try:
                response = await db_agent.achat(query, f"async_test_session_{i}", "test_user")
                print(f"回复: {response}")
            except Exception as e:
                print(f"查询出错: {e}")
                import traceback
                traceback.print_exc()
                
    except Exception as e:
        print(f"创建数据库代理时出错: {e}")
        import traceback
        traceback.print_exc()


def main():
    """主测试函数"""
    print("开始测试 DB Agent...")
    
    # 测试同步功能
    test_db_agent_sync()
    
    # # 测试异步功能
    # asyncio.run(test_db_agent_async())
    
    print("\n测试完成。")


if __name__ == "__main__":
    main()