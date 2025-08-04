<template>
  <div class="chat-container">
    <div class="chat-header">
      <h3>{{ agent?.name || 'AI助手' }}</h3>
      <p v-if="agent">{{ agent.description }}</p>
    </div>
    
    <div class="chat-messages" ref="messagesContainer">
      <div v-if="messages.length === 0 && agent" class="welcome-message">
        <MessageItem :message="welcomeMessage" />
      </div>
      <div v-else>
        <div v-for="(message, index) in messages" :key="index"
             :class="['message-row', message.sender === 'user' ? 'right' : 'left']">
          <div class="message">
            <div class="message-avatar">
              <i :class="message.sender === 'user' ? 'fas fa-user' : 'fas fa-robot'"></i>
            </div>
            <div class="message-content container">
              <div v-html="formatMessage(message.content)"></div><span v-if="message.isStreaming" class="cursor">_</span>
            </div>
          </div>
        </div>
        <div v-if="isLoading" class="loading-message">
          <div class="message-content">
            <div class="message-avatar">
              <i class="fas fa-robot"></i>
            </div>
            <div class="typing-indicator">
              <div class="typing-dot"></div>
              <div class="typing-dot"></div>
              <div class="typing-dot"></div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <div class="chat-input-container">
      <textarea
        v-model="inputMessage"
        placeholder="请输入消息..."
        @keydown.enter="handleEnter"
        :disabled="isLoading || !agent"
      ></textarea>
      <button 
        @click="sendMessage" 
        :disabled="isLoading || !inputMessage.trim() || !agent"
        class="send-button"
      >
        <i class="fas fa-paper-plane"></i>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick, onUnmounted } from 'vue';
import { Agent, Message } from '../services/agentService';
import { createSession, sendMessageStream } from '../services/agentService';
import MessageItem from './MessageItem.vue';
import { marked } from 'marked';

const props = defineProps<{
  agent: Agent | null
}>();

const messages = ref<Message[]>([]);
const inputMessage = ref('');
const sessionId = ref<string | null>(null);
const userId = ref<string>('');
const isLoading = ref(false);
const messagesContainer = ref<HTMLDivElement | null>(null);
const eventSource = ref<EventSource | null>(null);

// 欢迎消息
const welcomeMessage = computed<Message>(() => {
  return {
    id: 'welcome',
    sessionId: sessionId.value || '',
    agentId: props.agent?.id || '',
    content: props.agent?.welcomeMessage || '欢迎使用AI助手！',
    sender: 'ai',
    timestamp: new Date()
  };
});

// 格式化消息内容（支持Markdown）
const formatMessage = (content: string) => {
  if (!content) return '';
  
  try {
    // 使用marked解析Markdown
    return marked(content, {
      breaks: true, // 支持换行符
      gfm: true,    // 支持GitHub风格的Markdown
      sanitize: false // 允许HTML标签
    });
  } catch (error) {
    console.error('Markdown解析错误:', error);
    // 如果解析失败，回退到简单的换行符转换
    return content.replace(/\n/g, '<br>');
  }
};

// 生成用户ID
const generateUserId = () => {
  let id = localStorage.getItem('user_id');
  if (!id) {
    id = 'user_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    localStorage.setItem('user_id', id);
  }
  return id;
};

// 创建会话
const createNewSession = async () => {
  if (!props.agent) return;
  
  try {
    userId.value = generateUserId();
    const newSessionId = await createSession(props.agent.id, userId.value);
    sessionId.value = newSessionId;
    messages.value = [];
  } catch (error) {
    console.error('创建会话失败:', error);
  }
};

// 监听agent变化
watch(() => props.agent, async (newAgent) => {
  if (newAgent) {
    await createNewSession();
  }
}, { immediate: true });

// 滚动到底部
const scrollToBottom = async () => {
  await nextTick();
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
  }
};

// 监听消息变化，自动滚动到底部
watch(messages, scrollToBottom, { deep: true });

// 处理回车发送消息
const handleEnter = (e: KeyboardEvent) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
};

let currentEventSource: EventSource | null = null;

function closeEventSource() {
  if (currentEventSource) {
    currentEventSource.close();
    currentEventSource = null;
  }
}

onUnmounted(() => {
  closeEventSource();
});

// 发送消息
const sendMessage = async () => {
  if (!inputMessage.value.trim() || !props.agent || !sessionId.value || isLoading.value) {
    return;
  }

  const userMessage: Message = {
    id: 'msg_' + Date.now(),
    sessionId: sessionId.value,
    agentId: props.agent.id,
    content: inputMessage.value.trim(),
    sender: 'user',
    timestamp: new Date()
  };

  messages.value.push(userMessage);
  const userContent = inputMessage.value.trim();
  inputMessage.value = '';
  isLoading.value = true;

  let aiMessage: Message & { isStreaming?: boolean } = {
    id: 'ai_' + Date.now(),
    sessionId: sessionId.value,
    agentId: props.agent.id,
    content: '',
    sender: 'ai',
    timestamp: new Date(),
    isStreaming: true
  };
  messages.value.push(aiMessage);

  // 使用修复后的sendMessageStream函数
  try {
    await sendMessageStream(
      sessionId.value,
      props.agent.id,
      userId.value,
      userContent,
      (chunk: string) => {
        // 接收到数据块时的回调
        console.log('接收到数据块:', chunk);
        
        // agentService已经解析过JSON，这里直接使用chunk作为内容
        aiMessage.content += chunk;
        messages.value = [...messages.value];
        nextTick(() => {
          scrollToBottom();
        });
      },
      (error: any) => {
        // 错误处理
        console.error('流式请求错误:', error);
        aiMessage.content = `错误: ${error.message || '请求失败'}`;
        aiMessage.isStreaming = false;
        isLoading.value = false;
      },
      () => {
        // 完成时的回调
        console.log('流式请求完成');
        aiMessage.isStreaming = false;
        isLoading.value = false;
      }
    );
  } catch (error) {
    console.error('发送消息失败:', error);
    aiMessage.content = `错误: ${error instanceof Error ? error.message : '请求失败'}`;
    aiMessage.isStreaming = false;
    isLoading.value = false;
  }
};
</script>

<style scoped>
.chat-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: white;
  border-radius: 10px;
  box-shadow: 0 0 20px rgba(0, 0, 0, 0.1);
}

.chat-header {
  padding: 20px;
  border-bottom: 1px solid #eee;
}

.chat-header h3 {
  margin: 0 0 5px 0;
  color: #333;
}

.chat-header p {
  margin: 0;
  color: #888;
  font-size: 0.9em;
}

.chat-messages {
  display: flex;
  flex-direction: column;
  align-items: stretch;
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  background: #f9f9f9;
}

.welcome-message {
  display: flex;
  justify-content: flex-start;
}

.loading-message {
  margin-bottom: 20px;
}

.typing-indicator {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  background: #f1f1f1;
  border-radius: 18px;
  border-top-left-radius: 5px;
}

.typing-dot {
  width: 8px;
  height: 8px;
  background-color: #888;
  border-radius: 50%;
  margin: 0 3px;
  animation: typing 1.4s infinite ease-in-out;
}

.typing-dot:nth-child(1) { 
  animation-delay: -0.32s; 
}
.typing-dot:nth-child(2) { 
  animation-delay: -0.16s; 
}

@keyframes typing {
  0%, 80%, 100% { 
    transform: scale(0); 
  }
  40% { 
    transform: scale(1.0); 
  }
}

.chat-input-container {
  display: flex;
  padding: 15px;
  border-top: 1px solid #eee;
  background: white;
}

.chat-input-container textarea {
  flex: 1;
  padding: 12px 15px;
  border: 1px solid #ddd;
  border-radius: 20px;
  resize: none;
  outline: none;
  font-family: inherit;
  max-height: 150px;
  min-height: 20px;
}

.chat-input-container textarea:focus {
  border-color: #42b983;
}

.send-button {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  border: none;
  background: #42b983;
  color: white;
  margin-left: 10px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.3s;
}

.send-button:hover:not(:disabled) {
  background: #359c6d;
}

.send-button:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.cursor {
  display: inline-block;
  width: 10px;
  animation: blink 1s steps(1) infinite;
}
@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

.message {
  display: flex;
  align-items: flex-start;
  max-width: 90%;
}
.message.left {
  flex-direction: row;
  justify-content: flex-start;
}
.message.right {
  flex-direction: row-reverse;
  justify-content: flex-end;
}
.message-row.left .message {
  max-width: 95%;
}
.message-row.right .message {
  max-width: 80%;
}
.message-content.container {
  max-width: 100%;
  word-break: break-all;
  padding: 12px 16px;
  border-radius: 18px;
  line-height: 1.5;
}
.message.left .message-content.container {
  background: #f1f1f1;
  color: #333;
  border-top-left-radius: 5px;
}
.message.right .message-content.container {
  background: #42b983;
  color: #fff;
  border-top-right-radius: 5px;
}
.message-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: linear-gradient(135deg, #42b983, #1a2a6c);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  margin: 0 10px;
  flex-shrink: 0;
}
.message.right .message-avatar {
  background: linear-gradient(135deg, #1a2a6c, #2c3e50);
}

.chat-messages .message.right {
  flex-direction: row-reverse !important;
  justify-content: flex-end !important;
}
.chat-messages .message.left {
  flex-direction: row !important;
  justify-content: flex-start !important;
}

.chat-container .chat-messages .message.right {
  flex-direction: row-reverse !important;
  justify-content: flex-end !important;
  align-items: flex-start !important;
}
.chat-container .chat-messages .message.left {
  flex-direction: row !important;
  justify-content: flex-start !important;
  align-items: flex-start !important;
}

.chat-messages .message.right {
  flex-direction: row-reverse !important;
  justify-content: flex-end !important;
  align-items: flex-start !important;
  margin-left: auto !important;
}
.chat-messages .message.left {
  flex-direction: row !important;
  justify-content: flex-start !important;
  align-items: flex-start !important;
  margin-right: auto !important;
}

.message-row {
  display: flex;
  width: 100%;
  margin-bottom: 20px;
}
.message-row.right {
  justify-content: flex-end;
}
.message-row.left {
  justify-content: flex-start;
}

@media (max-width: 768px) {
  .chat-header {
    padding: 15px;
  }
  
  .chat-messages {
    padding: 15px;
  }
  
  .chat-input-container {
    padding: 10px;
  }
}

/* Markdown样式 */
.message-content.container {
  line-height: 1.6;
}

.message-content.container h1,
.message-content.container h2,
.message-content.container h3,
.message-content.container h4,
.message-content.container h5,
.message-content.container h6 {
  margin: 16px 0 8px 0;
  font-weight: 600;
  line-height: 1.25;
}

.message-content.container h1 {
  font-size: 1.5em;
  border-bottom: 2px solid #e1e4e8;
  padding-bottom: 8px;
}

.message-content.container h2 {
  font-size: 1.3em;
  border-bottom: 1px solid #e1e4e8;
  padding-bottom: 6px;
}

.message-content.container h3 {
  font-size: 1.1em;
}

.message-content.container p {
  margin: 8px 0;
}

.message-content.container ul,
.message-content.container ol {
  margin: 8px 0;
  padding-left: 24px;
}

.message-content.container li {
  margin: 4px 0;
}

.message-content.container blockquote {
  margin: 8px 0;
  padding: 8px 16px;
  border-left: 4px solid #dfe2e5;
  background-color: #f6f8fa;
  color: #6a737d;
}

.message-content.container code {
  background-color: #f6f8fa;
  padding: 2px 6px;
  border-radius: 3px;
  font-family: 'Courier New', monospace;
  font-size: 0.9em;
}

.message-content.container pre {
  background-color: #f6f8fa;
  padding: 12px;
  border-radius: 6px;
  overflow-x: auto;
  margin: 8px 0;
}

.message-content.container pre code {
  background: none;
  padding: 0;
}

.message-content.container table {
  border-collapse: collapse;
  width: 100%;
  margin: 8px 0;
}

.message-content.container th,
.message-content.container td {
  border: 1px solid #dfe2e5;
  padding: 8px 12px;
  text-align: left;
}

.message-content.container th {
  background-color: #f6f8fa;
  font-weight: 600;
}

.message-content.container tr:nth-child(even) {
  background-color: #f8f9fa;
}

.message-content.container strong {
  font-weight: 600;
}

.message-content.container em {
  font-style: italic;
}

.message-content.container hr {
  border: none;
  border-top: 1px solid #e1e4e8;
  margin: 16px 0;
}
</style>