# AI Agent API 接口文档

## 基础信息
- 基础路径: `/api`
- 文档地址: `http://0.0.0.0:9091/docs` 或 `http://0.0.0.0:9091/redoc`

## 数据模型

### ChatRequest (聊天请求)
用于向AI助手发送聊天消息的请求数据模型。

| 字段名 | 类型 | 必填 | 描述 |
|--------|------|----|------|
| message | string | 是  | 用户发送的聊天消息内容 |
| chat_id | string | 是  | 聊天会话ID（可选）<br>用于标识一个聊天会话的唯一ID。如果未提供，服务器将自动生成一个。<br>相同ID的请求会被认为是同一个会话的一部分。 |
| agent_type | string | 是  | AI助手类型<br>指定要使用的AI助手类型。可用的助手类型可以通过 /agents 接口获取。<br>默认值为"default"。 |
| provider_name | string | 否  | 模型提供商名称（可选）<br>指定要使用的模型提供商，如"qwen"。如果未指定，将使用系统默认的提供商。<br>可用的提供商列表可以通过 /models 接口获取。 |
| model_name | string | 否  | 模型名称（可选）<br>指定要使用的具体模型名称。如果未指定，将使用该提供商的默认模型。<br>不同提供商支持的模型列表可以通过 /models 接口获取。 |
| user_id | string | 是  | 用户ID（可选）<br>用于标识用户的唯一ID。如果未提供，系统会使用默认值。<br>建议前端生成并持久化存储用户ID以保持会话一致性。 |

### ChatResponse (聊天响应)
用于描述AI助手回复的响应数据模型。

| 字段名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| chat_id | string | 是 | 聊天会话ID<br>用于标识一个聊天会话的唯一ID。如果请求中未提供chat_id，服务器将自动生成一个。<br>客户端应使用相同的chat_id进行后续对话，以保持会话上下文。 |
| message | string | 是 | AI助手的回复内容<br>AI助手对用户消息的回复内容。可能是完整回复（在非流式接口中），<br>或者是错误信息（当error字段为True时）。 |
| error | boolean | 否 | 错误标识（可选）<br>标识该响应是否为错误响应。<br>- True: 表示发生了错误，message字段包含错误信息<br>- None/False: 表示正常响应，message字段包含AI助手的回复内容<br>- 该字段仅在发生错误时出现 |

### AgentInfo (Agent信息)
描述单个Agent的详细信息。

| 字段名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| id | string | 是 | Agent ID<br>Agent的唯一标识符，用于在请求中指定要使用的Agent类型。<br>例如: "writing", "db" 等。 |
| name | string | 是 | Agent名称<br>Agent的显示名称，用于在用户界面中展示。<br>例如: "写作助手", "数据查询助手" 等。 |

### AgentListResponse (Agent列表响应)
用于描述系统中所有Agent的配置和可用性状态。

| 字段名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| configured_agents | array of string | 是 | 已配置的Agent列表<br>系统中配置的所有Agent类型ID列表，无论其当前是否可用。 |
| available_agents | array of string | 是 | 可用的Agent列表<br>成功初始化并可使用的Agent类型ID列表。<br>这些Agent可以正常处理用户请求。 |
| unavailable_agents | array of string | 是 | 不可用的Agent列表<br>配置了但初始化失败的Agent类型ID列表。<br>这些Agent当前无法处理用户请求。 |
| agent_details | array of AgentInfo | 是 | Agent详细信息列表<br>包含所有已配置Agent的详细信息，包括ID和显示名称。<br>前端可根据这些信息构建Agent选择界面。 |

### ModelsResponse (模型列表响应)
用于描述系统中所有可用模型的信息，按提供商分组。

| 字段名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| models | object | 是 | 模型信息字典<br>按提供商分组的模型列表。<br>- 键(key): 模型提供商名称，如 "qwen"<br>- 值(value): 该提供商下可用的模型名称列表，如 ["qwen-turbo", "qwen-plus"] |

### ErrorResponse (错误响应)
用于描述发生错误时的统一响应格式。

| 字段名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| error | string | 是 | 错误信息描述 |

## API 接口

### 1. 获取可用Agent列表
**GET** `/api/agents`

获取系统中所有配置的AI助手信息，包括可用的和不可用的。可用于前端展示可选择的AI助手列表。

#### 响应示例
成功响应:
```json
{
  "configured_agents": ["writing", "db"],
  "available_agents": ["writing"],
  "unavailable_agents": ["db"],
  "agent_details": [
    {
      "id": "writing",
      "name": "写作助手"
    },
    {
      "id": "db",
      "name": "数据库助手"
    }
  ]
}
```

错误响应:
```json
{
  "error": "获取Agent列表失败"
}
```

### 2. 获取可用模型列表
**GET** `/api/models`

获取系统中所有配置并可用的AI模型信息，按提供商分组。可用于前端展示模型选择列表。

#### 响应示例
成功响应:
```json
{
  "models": {
    "qwen": ["qwen-turbo", "qwen-plus", "qwen-max"]
  }
}
```

错误响应:
```json
{
  "error": "获取模型列表失败"
}
```

### 3. 非流式对话接口
**POST** `/api/chat`

与指定的AI助手进行非流式对话。一次性返回完整的AI助手回复，适用于不需要实时显示回复内容的场景。

#### 请求示例
```json
{
  "message": "你好，能帮我写一篇科幻小说吗？",
  "agent_type": "writing",
  "chat_id": "chat_123456"
}
```

#### 响应示例
成功响应:
```json
{
  "chat_id": "chat_123456",
  "message": "你好！我很乐意帮你写一篇科幻小说..."
}
```

Agent不可用响应:
```json
{
  "chat_id": "chat_123456",
  "message": "Agent 'writing' 不可用或初始化失败",
  "error": true
}
```

### 4. 流式对话接口
**POST** `/api/stream_chat`

与指定的AI助手进行流式对话。流式响应会逐步返回AI助手的回复，提供更好的用户体验。

#### 请求示例
```json
{
  "message": "你好，能帮我写一篇科幻小说吗？",
  "agent_type": "writing",
  "chat_id": "chat_123456"
}
```

#### 响应
返回文本流形式的逐步响应内容，或JSON格式的错误信息。

### 5. 健康检查接口
**GET** `/api/health`

用于检查服务是否正常运行。通常用于负载均衡器的健康检查或者前端应用启动时检查服务状态。

#### 响应示例
```json
{
  "status": "healthy",
  "message": "服务运行正常"
}
```

## 使用说明

1. 所有API接口都以 `/api` 为前缀
2. 使用前建议先调用 `/api/agents` 获取可用的Agent列表
3. 可以通过 `/api/models` 获取可用的模型列表
4. 发起聊天请求时，建议前端生成并持久化存储用户ID，以保持会话一致性
5. 如果需要保持对话上下文，应使用相同的 chat_id 进行后续请求
6. 流式接口适用于需要实时显示回复内容的场景，非流式接口适用于不需要实时显示的场景

## 错误处理

当发生错误时，API会返回相应的错误信息：
- Agent不可用时会返回具体的Agent类型和错误原因
- 其他系统错误会返回通用的错误描述信息