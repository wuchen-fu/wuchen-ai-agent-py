#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
启动AI Agent服务脚本
"""

import os
import sys

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def print_startup_info():
    """打印启动信息"""
    print("=" * 50)
    print("AI Agent服务启动中...")
    print("=" * 50)
    print("访问地址:")
    print("  - API基础路径: http://localhost:9091/api")
    print("  - Agent列表:   http://localhost:9091/api/agents")
    print("  - 模型列表:     http://localhost:9091/api/models")
    print("  - 健康检查:     http://localhost:9091/api/health")
    print("")
    print("API文档:")
    print("  - Swagger UI:  http://localhost:9091/docs")
    print("  - ReDoc:       http://localhost:9091/redoc")
    print("=" * 50)

if __name__ == "__main__":
    import uvicorn
    from web.app import app
    
    print_startup_info()
    
    uvicorn.run(
        "web.app:app",
        host="0.0.0.0",
        port=9091,
        reload=False
    )