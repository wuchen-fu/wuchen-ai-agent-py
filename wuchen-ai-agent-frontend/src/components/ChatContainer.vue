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
              {{ message.content }}<span v-if="message.isStreaming" class="cursor">_</span>
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

  // 用 fetch 发送 POST 请求并流式处理响应
  const url = `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:9091/api'}/stream_chat`;
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      chat_id: sessionId.value,
      agent_type: props.agent.id,
      user_id: userId.value,
      message: userContent
    })
  });

  if (!response.body) {
    aiMessage.content = '流式响应不支持';
    aiMessage.isStreaming = false;
    isLoading.value = false;
    return;
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let done = false;
  let buffer = '';

  while (!done) {
    const { value, done: streamDone } = await reader.read();
    done = streamDone;
    if (value) {
      const chunk = decoder.decode(value, { stream: true });
      buffer += chunk;
      let lines = buffer.split('\n');
      buffer = lines.pop() || '';
      for (const line of lines) {
        if (line.startsWith('data:')) {
          const data = line.slice(5).trim();
          if (data === '[DONE]') {
            aiMessage.isStreaming = false;
            isLoading.value = false;
          } else {
            aiMessage.content += data;
            messages.value = [...messages.value];
            await nextTick();
            scrollToBottom();
          }
        }
      }
    }
  }
  aiMessage.isStreaming = false;
  isLoading.value = false;
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
  max-width: 80%;
}
.message.left {
  flex-direction: row;
  justify-content: flex-start;
}
.message.right {
  flex-direction: row-reverse;
  justify-content: flex-end;
}
.message-content.container {
  max-width: 70%;
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
</style>