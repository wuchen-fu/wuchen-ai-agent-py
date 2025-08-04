# AI Agent 聊天前端项目

这是一个基于Vue3和TypeScript构建的AI智能体聊天应用前端项目。

## 功能特性

- 左侧智能体应用列表
- 右侧聊天界面，支持实时对话
- 通过SSE（Server-Sent Events）实现实时消息传输
- 响应式设计，支持PC端、手机端和平板端
- 科技风格UI界面
- 自动生成用户ID并持久化存储
- 为每个会话生成唯一会话ID

## 技术栈

- Vue 3 (Composition API)
- TypeScript
- Vite
- Axios
- Pinia (状态管理)

## 项目结构

```
src/
├── assets/           # 静态资源
├── components/       # 组件
│   ├── AgentList.vue     # 智能体列表组件
│   ├── ChatContainer.vue # 聊天容器组件
│   └── MessageItem.vue   # 消息项组件
├── services/         # API服务
│   └── agentService.ts
├── views/            # 页面视图
│   └── ChatView.vue
├── router/           # 路由配置
├── stores/           # 状态管理
├── App.vue           # 根组件
└── main.ts           # 入口文件
```

## 安装与运行

1. 安装依赖：
```bash
npm install
```

2. 启动开发服务器：
```bash
npm run dev
```

3. 构建生产版本：
```bash
npm run build
```

## 使用说明

1. 应用启动后会自动加载智能体列表
2. 点击左侧任一智能体即可开始对话
3. 系统会自动生成用户ID并存储在localStorage中
4. 每次切换智能体或开始新对话时会生成新的会话ID
5. 支持通过回车键或点击发送按钮发送消息
6. 消息通过SSE方式实时接收并显示

## 注意事项

- 后端API地址配置在 `src/services/agentService.ts` 文件中
- 当前默认后端地址为 `http://localhost:9091`
- 项目使用了Font Awesome图标库，通过CDN引入

## 自定义配置

如需修改后端API地址，请修改 `src/services/agentService.ts` 文件中的 `baseURL` 配置。