"""
Agent模块初始化文件
"""

# 确保模块可以正确导入
import os
import sys

# 添加项目根目录到系统路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.append(project_root)