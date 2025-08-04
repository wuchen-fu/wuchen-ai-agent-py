#!/usr/bin/env python3
"""
测试非SSE流式响应（使用StreamingResponse）
"""

import json

def test_streaming_response_format():
    """测试流式响应格式"""
    print("测试非SSE流式响应格式...")
    
    # 模拟正常的响应数据
    normal_response = {
        "text": " **节奏控制**：",
        "content_type": "markdown",
        "metadata": {
            "timestamp": 1754311939.6121275,
            "chat_id": "session_1754311912289_5659sjuot",
            "agent_type": "writing",
            "chunk_index": 140
        }
    }
    
    print("正常响应数据:")
    print(json.dumps(normal_response, ensure_ascii=False, indent=2))
    
    # 模拟流式响应格式（无SSE前缀，直接JSON）
    streaming_format = f"{json.dumps(normal_response, ensure_ascii=False)}\n\n"
    print("\n流式响应格式:")
    print(streaming_format)
    
    # 模拟结束信号
    end_signal = {
        "event": "end",
        "text": "[DONE]",
        "metadata": {
            "timestamp": 1754311939.6121275,
            "chat_id": "session_1754311912289_5659sjuot",
            "total_chunks": 141
        }
    }
    
    print("\n结束信号:")
    print(json.dumps(end_signal, ensure_ascii=False, indent=2))
    
    # 模拟错误信号
    error_signal = {
        "text": "发生错误",
        "event": "error",
        "metadata": {
            "timestamp": 1754311939.6121275,
            "error_code": "TEST_ERROR"
        }
    }
    
    print("\n错误信号:")
    print(json.dumps(error_signal, ensure_ascii=False, indent=2))
    
    print("\n✅ 非SSE流式响应格式测试完成！")
    print("注意：这不是SSE协议，而是普通的HTTP流式响应")

def test_frontend_parsing():
    """测试前端解析逻辑"""
    print("\n测试前端解析逻辑...")
    
    # 模拟前端接收到的JSON行
    json_line = '{"text": " **节奏控制**：", "content_type": "markdown", "metadata": {"timestamp": 1754311939.6121275, "chat_id": "session_1754311912289_5659sjuot", "agent_type": "writing", "chunk_index": 140}}'
    
    print(f"原始JSON行: {json_line}")
    
    # 模拟前端解析逻辑
    try:
        json_data = json.loads(json_line)
        print(f"解析的JSON数据: {json_data}")
        
        # 提取文本内容
        if 'text' in json_data:
            content = json_data['text']
            print(f"提取的文本内容: '{content}'")
            print(f"内容类型: {json_data.get('content_type', 'unknown')}")
            print(f"元数据: {json_data.get('metadata', {})}")
            
            # 验证内容是否正确提取
            expected_content = " **节奏控制**："
            if content == expected_content:
                print("✅ 文本内容提取正确！")
            else:
                print(f"❌ 文本内容提取错误！期望: '{expected_content}', 实际: '{content}'")
        else:
            print("❌ 没有找到text字段")
            
    except json.JSONDecodeError as e:
        print(f"❌ JSON解析失败: {e}")

def test_http_headers():
    """测试HTTP响应头"""
    print("\n测试HTTP响应头...")
    
    headers = {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Content-Type": "application/json; charset=utf-8"
    }
    
    print("StreamingResponse响应头:")
    for key, value in headers.items():
        print(f"  {key}: {value}")
    
    print("\n✅ 这些响应头确保流式传输正常工作")

if __name__ == "__main__":
    test_streaming_response_format()
    test_frontend_parsing()
    test_http_headers() 