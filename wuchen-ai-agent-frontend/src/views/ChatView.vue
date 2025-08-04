<template>
  <div class="chat-view">
    <div class="chat-layout">
      <div class="chat-sidebar">
        <AgentList 
          :agents="agents" 
          v-model:selectedAgentId="selectedAgentId" 
          @agent-selected="handleAgentSelected" 
        />
      </div>
      <div class="chat-main">
        <ChatContainer :agent="currentAgent" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'; // 确保 ref 已正确导入
import { getAgents } from '../services/agentService';
import ChatContainer from '../components/ChatContainer.vue';
import AgentList from '../components/AgentList.vue';

interface Agent {
  id: string;
  name: string;
  description: string;
  icon: string;
}

const agents = ref<Agent[]>([]);

onMounted(async () => {
  console.log('开始获取智能体列表'); 
  try {
    agents.value = await getAgents();
    console.log('获取到的智能体列表:', agents.value); 
  } catch (error) {
    console.error('获取智能体列表失败:', error);
  }

  // 调整调试日志位置，确保在数据加载后打印
  console.log('传递给 AgentList 的 agents 数据:', agents.value); 
});

const selectedAgentId = ref<string>('');

const currentAgent = computed(() => {
  const agent = agents.value.find(a => a.id === selectedAgentId.value);
  return agent ? { ...agent } : null;
});

const handleAgentSelected = (agent: Agent) => {
  console.log('选择了智能体:', agent);
};

// 生成用户ID并存储在localStorage中
const userId = ref<string>('user_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9));
(() => {
  let id = localStorage.getItem('userId');
  if (!id) {
    id = userId.value;
    localStorage.setItem('userId', id);
  } else {
    userId.value = id;
  }
})();

// 生成会话ID
const sessionId = ref<string>('session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9));
</script>

<style scoped>
.chat-view {
  height: 100vh;
  padding: 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.chat-layout {
  display: flex;
  height: 100%;
  gap: 20px;
  max-width: 1600px;
  margin: 0 auto;
  border-radius: 10px;
  overflow: hidden;
}

.chat-sidebar {
  width: 300px;
  flex-shrink: 0;
}

.chat-main {
  flex: 1;
  min-width: 0;
}

@media (max-width: 768px) {
  .chat-view {
    padding: 10px;
  }
  
  .chat-layout {
    flex-direction: column;
    gap: 10px;
  }
  
  .chat-sidebar {
    width: 100%;
    height: 30%;
  }
  
  .chat-main {
    height: 70%;
  }
}

@media (max-width: 480px) {
  .chat-view {
    padding: 5px;
  }
}
</style>