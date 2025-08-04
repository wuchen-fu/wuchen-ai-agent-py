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
        <div class="message-body markdown-content" v-html="formatMessage(message.content)"></div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Message } from '../services/agentService';
import { marked } from 'marked';

const props = defineProps<{
  message: Message
}>();

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

/* Markdown样式 */
.markdown-content {
  line-height: 1.6;
}

.markdown-content h1,
.markdown-content h2,
.markdown-content h3,
.markdown-content h4,
.markdown-content h5,
.markdown-content h6 {
  margin: 16px 0 8px 0;
  font-weight: 600;
  line-height: 1.25;
}

.markdown-content h1 {
  font-size: 1.5em;
  border-bottom: 2px solid #e1e4e8;
  padding-bottom: 8px;
}

.markdown-content h2 {
  font-size: 1.3em;
  border-bottom: 1px solid #e1e4e8;
  padding-bottom: 6px;
}

.markdown-content h3 {
  font-size: 1.1em;
}

.markdown-content p {
  margin: 8px 0;
}

.markdown-content ul,
.markdown-content ol {
  margin: 8px 0;
  padding-left: 24px;
}

.markdown-content li {
  margin: 4px 0;
}

.markdown-content blockquote {
  margin: 8px 0;
  padding: 8px 16px;
  border-left: 4px solid #dfe2e5;
  background-color: #f6f8fa;
  color: #6a737d;
}

.markdown-content code {
  background-color: #f6f8fa;
  padding: 2px 6px;
  border-radius: 3px;
  font-family: 'Courier New', monospace;
  font-size: 0.9em;
}

.markdown-content pre {
  background-color: #f6f8fa;
  padding: 12px;
  border-radius: 6px;
  overflow-x: auto;
  margin: 8px 0;
}

.markdown-content pre code {
  background: none;
  padding: 0;
}

.markdown-content table {
  border-collapse: collapse;
  width: 100%;
  margin: 8px 0;
}

.markdown-content th,
.markdown-content td {
  border: 1px solid #dfe2e5;
  padding: 8px 12px;
  text-align: left;
}

.markdown-content th {
  background-color: #f6f8fa;
  font-weight: 600;
}

.markdown-content tr:nth-child(even) {
  background-color: #f8f9fa;
}

.markdown-content strong {
  font-weight: 600;
}

.markdown-content em {
  font-style: italic;
}

.markdown-content hr {
  border: none;
  border-top: 1px solid #e1e4e8;
  margin: 16px 0;
}
</style>