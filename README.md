# Wuchen AI Agent Platform

<div align="center">

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Vue.js](https://img.shields.io/badge/Vue.js-3.5+-green.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-red.svg)
![LangChain](https://img.shields.io/badge/LangChain-0.1+-yellow.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

**一个基于LangChain的多Agent AI对话平台，支持多种AI模型和智能工具**

[🚀 快速开始](#快速开始) • [📖 文档](#文档) • [🔧 功能特性](#功能特性) • [🏗️ 架构设计](#架构设计)

</div>

---

## 📋 目录

- [项目简介](#项目简介)
- [功能特性](#功能特性)
- [架构设计](#架构设计)
- [核心内容](#核心内容)
- [快速开始](#快速开始)
- [使用说明](#使用说明)
- [API文档](#api文档)
- [开发指南](#开发指南)
- [贡献指南](#贡献指南)
- [许可证](#许可证)

## 🎯 项目简介

Wuchen AI Agent Platform 是一个基于 LangChain 框架构建的智能对话平台，集成了多种AI模型和专业的Agent，为用户提供智能化的对话体验。平台支持写作助手、数据库查询、RAG检索等多种专业场景，并提供了现代化的Web界面。

### 🌟 主要特色

- 🤖 **多Agent架构**：支持写作、数据库查询、RAG检索等多种专业Agent
- 🔄 **流式对话**：实时流式响应，提供流畅的对话体验
- 🎨 **现代化UI**：基于Vue.js的响应式Web界面
- 🔌 **多模型支持**：支持阿里百炼、OpenAI等多种AI模型
- 🛠️ **工具集成**：内置数据库查询、网络搜索等实用工具
- 📊 **会话管理**：完整的对话历史和会话管理功能

## 🔧 功能特性

### 🤖 智能Agent
- **写作助手**：专业的写作辅助，支持小说创作、内容生成
- **数据库Agent**：智能SQL查询和数据库操作
- **RAG Agent**：基于文档的智能问答和检索
- **简单RAG Agent**：轻量级文档检索功能

### 💬 对话功能
- 实时流式对话响应
- 多轮对话上下文保持
- 会话历史管理
- 支持Markdown格式显示

### 🔌 模型支持
- 阿里百炼（DashScope）
- OpenAI GPT系列
- 可扩展的模型提供商架构

### 🛠️ 工具集成
- 数据库查询工具
- 网络搜索工具
- 文档检索工具
- 自定义工具扩展

## 🏗️ 架构设计

### 整体架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   External      │
│   (Vue.js)      │◄──►│   (FastAPI)     │◄──►│   Services      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
        │                       │                       │
        │                       │                       │
        ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   UI Components │    │   Agent Layer   │    │   AI Models     │
│   - Chat        │    │   - Writing     │    │   - Qwen        │
│   - Agent List  │    │   - Database    │    │   - OpenAI      │
│   - Settings    │    │   - RAG         │    │   - Custom      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 技术栈

#### 后端技术栈
- **框架**: FastAPI + Uvicorn
- **AI框架**: LangChain
- **数据库**: Redis (会话存储) + MongoDB/MySQL (可选)
- **向量数据库**: ChromaDB
- **模型提供商**: 阿里百炼、OpenAI等

#### 前端技术栈
- **框架**: Vue.js 3 + TypeScript
- **构建工具**: Vite
- **状态管理**: Pinia
- **路由**: Vue Router
- **UI组件**: 自定义组件
- **Markdown渲染**: Marked.js

### 核心模块

#### 1. Agent管理系统
```
web/agent/
├── agent_factory.py      # Agent工厂模式
├── base_agent.py         # 基础Agent类
├── writing_agent.py      # 写作助手
├── db_agent.py          # 数据库Agent
├── rag_agent.py         # RAG检索Agent
└── model_provider.py    # 模型提供商管理
```

#### 2. 前端组件
```
wuchen-ai-agent-frontend/src/
├── components/
│   ├── ChatContainer.vue    # 聊天容器
│   ├── MessageItem.vue      # 消息组件
│   └── AgentList.vue        # Agent列表
├── services/
│   └── agentService.ts      # API服务
└── views/
    ├── ChatView.vue         # 聊天页面
    └── HomeView.vue         # 首页
```

## 🚀 快速开始

### 环境要求

- Python 3.8+
- Node.js 20.19.0+
- Redis 6.0+
- 阿里百炼API密钥

### 1. 克隆项目

```bash
git clone https://github.com/your-username/wuchen-ai-agent-py.git
cd wuchen-ai-agent-py
```

### 2. 后端设置

```bash
# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 或
.venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp env.example .env
# 编辑 .env 文件，填入你的API密钥
```

### 3. 前端设置

```bash
cd wuchen-ai-agent-frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

### 4. 启动服务

```bash
# 启动后端服务
python start_server.py

# 启动前端服务（新终端）
cd wuchen-ai-agent-frontend
npm run dev
```

### 5. 访问应用

- 前端界面: http://localhost:5173
- 后端API: http://localhost:9091
- API文档: http://localhost:9091/docs

## 📖 使用说明

### 基本使用

1. **选择Agent**: 在首页选择要使用的AI助手类型
2. **开始对话**: 在聊天界面输入消息，AI会实时回复
3. **查看历史**: 所有对话都会自动保存，可以查看历史记录

### 写作助手

- 支持小说创作、文章写作
- 提供写作建议和内容生成
- 支持多种写作风格和主题

### 数据库Agent

- 支持自然语言转SQL查询
- 智能数据库操作
- 查询结果可视化展示

### RAG检索

- 上传文档进行智能问答
- 基于文档内容的精准回答
- 支持多种文档格式

### 环境变量配置

```bash
# 阿里百炼配置
QWEN_API_KEY=your_api_key_here
QWEN_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
QWEN_MODEL=qwen-plus

# Redis配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your_redis_password

# 数据库配置（可选）
DB_MYSQL_URL=127.0.0.1
DB_MYSQL_PORT=3306
DB_MYSQL_USER=root
DB_MYSQL_PASSWORD=your_password
DB_MYSQL_DATABASE=your_database
```

## 📚 API文档

### 主要接口

#### 1. 获取Agent列表
```http
GET /api/agents
```

#### 2. 流式对话
```http
POST /api/stream_chat
Content-Type: application/json

{
  "message": "你好",
  "agent_type": "writing",
  "chat_id": "session_123",
  "user_id": "user_456"
}
```

#### 3. 获取模型列表
```http
GET /api/models
```

### 响应格式

```json
{
  "text": "AI回复内容",
  "content_type": "markdown",
  "metadata": {
    "chat_id": "session_123",
    "agent_type": "writing",
    "chunk_index": 1
  }
}
```

## 🛠️ 开发指南

### 项目结构

```
wuchen-ai-agent-py/
├── web/                    # 后端代码
│   ├── agent/             # Agent实现
│   ├── app.py             # FastAPI应用
│   └── controller.py      # API控制器
├── wuchen-ai-agent-frontend/  # 前端代码
│   ├── src/
│   │   ├── components/    # Vue组件
│   │   ├── services/      # API服务
│   │   └── views/         # 页面视图
│   └── package.json
├── tools/                 # 工具模块
├── rag/                   # RAG相关
├── chat_memory/           # 会话管理
├── config.py              # 配置管理
└── start_server.py        # 启动脚本
```

### 添加新的Agent

1. 在 `web/agent/` 目录下创建新的Agent类
2. 继承 `BaseAgent` 类
3. 实现必要的方法
4. 在 `agent_factory.py` 中注册新Agent

```python
from web.agent.base_agent import BaseAgent

class CustomAgent(BaseAgent):
    def __init__(self, config):
        super().__init__(config)
    
    def chat(self, message, **kwargs):
        # 实现聊天逻辑
        pass
    
    def stream_chat(self, message, **kwargs):
        # 实现流式聊天逻辑
        pass
```

### 添加新的模型提供商

1. 在 `web/agent/model_provider.py` 中添加新提供商
2. 实现相应的API调用逻辑
3. 在配置文件中添加相关配置

## 🤝 贡献指南

我们欢迎所有形式的贡献！

### 贡献方式

1. **报告Bug**: 在GitHub Issues中报告问题
2. **功能建议**: 提出新功能建议
3. **代码贡献**: 提交Pull Request
4. **文档改进**: 改进文档和示例

### 开发流程

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建Pull Request

### 代码规范

- 遵循PEP 8 Python代码规范
- 使用TypeScript进行前端开发
- 添加适当的注释和文档
- 编写单元测试

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

<div align="center">

**如果这个项目对你有帮助，请给它一个 ⭐️**

Made with ❤️ by [Your Name]

</div> 