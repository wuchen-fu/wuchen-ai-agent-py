<template>
  <div :class="['message-item', message.sender]">
    <div class="message-content">
      <div class="message-avatar">
        <i :class="message.sender === 'user' ? 'fas fa-user' : 'fas fa-robot'"></i>
      </div>
      <div class="message-text">
        <div class="message-sender">
          {{ message.sender === 'user' ? '我' : 'AI助手' }}
        </div>
        <div class="message-body" v-html="formatMessage(message.content)"></div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Message } from '../services/agentService';

const props = defineProps<{
  message: Message
}>();

const formatMessage = (content: string) => {
  // 将换行符转换为<br>标签
  return content.replace(/\n/g, '<br>');
};
</script>

<style scoped>
.message-item {
  margin-bottom: 20px;
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.message-content {
  display: flex;
  align-items: flex-start;
}

.message-item.ai .message-content {
  flex-direction: row;
}

.message-item.user .message-content {
  flex-direction: row-reverse;
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

.message-item.user .message-avatar {
  background: linear-gradient(135deg, #1a2a6c, #2c3e50);
}

.message-text {
  max-width: 80%;
}

.message-item.ai .message-text {
  margin-left: 0;
  margin-right: auto;
}

.message-item.user .message-text {
  margin-right: 0;
  margin-left: auto;
}

.message-sender {
  font-size: 0.8em;
  color: #888;
  margin-bottom: 5px;
}

.message-body {
  padding: 12px 16px;
  border-radius: 18px;
  line-height: 1.5;
  word-wrap: break-word;
}

.message-item.ai .message-body {
  background: #f1f1f1;
  border-top-left-radius: 5px;
}

.message-item.user .message-body {
  background: #42b983;
  color: white;
  border-top-right-radius: 5px;
}
</style>