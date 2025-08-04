<template>
  <div class="agent-list">
    <div class="agent-list-header">
      <h3>智能体应用列表</h3>
    </div>
    <div class="agent-list-items">
      <div 
        v-for="agent in computedAgents" 
        :key="agent.id" 
        :class="['agent-item', { active: selectedAgentId === agent.id }]"
        @click="selectAgent(agent)"
      >
        <div class="agent-icon">
          <i :class="agent.icon || 'fas fa-robot'"></i>
        </div>
        <div class="agent-info">
          <h4>{{ agent.name }}</h4>
          <p>{{ agent.description }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { Agent, getAgents } from '../services/agentService';

const props = defineProps<{
  agents?: Agent[];
}>();

const agentsFromService = ref<Agent[]>([]);
const selectedAgentId = defineModel<string>('selectedAgentId');

const emit = defineEmits<{
  (e: 'agent-selected', agent: Agent): void
}>();

// 计算属性，优先使用外部传入的agents列表
const computedAgents = computed(() => {
  console.log('computedAgents 计算结果:', props.agents || agentsFromService.value);
  return props.agents || agentsFromService.value;
});

onMounted(async () => {
  // 如果没有外部传入agents，则从服务获取
  if (!props.agents) {
    try {
      agentsFromService.value = await getAgents();
      // 默认选择第一个智能体
      if (agentsFromService.value.length > 0 && !selectedAgentId.value) {
        selectAgent(agentsFromService.value[0]);
      }
    } catch (error) {
      console.error('获取智能体列表失败:', error);
    }
  } else if (props.agents?.length > 0 && !selectedAgentId.value) {
    // 如果有外部传入agents且未选择agent，则默认选择第一个
    selectAgent(props.agents[0]);
  }
});

const selectAgent = (agent: Agent) => {
  selectedAgentId.value = agent.id;
  emit('agent-selected', agent);
};
</script>

<style scoped>
.agent-list {
  height: 100%;
  background: linear-gradient(135deg, #1a2a6c, #2c3e50);
  color: white;
  border-radius: 10px;
  box-shadow: 0 0 20px rgba(0, 0, 0, 0.3);
  display: flex;
  flex-direction: column;
}

.agent-list-header {
  padding: 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.agent-list-header h3 {
  margin: 0;
  font-size: 1.2em;
  font-weight: 600;
}

.agent-list-items {
  flex: 1;
  overflow-y: auto;
}

.agent-item {
  display: flex;
  align-items: center;
  padding: 15px 20px;
  cursor: pointer;
  transition: all 0.3s ease;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.agent-item:hover {
  background: rgba(255, 255, 255, 0.1);
}

.agent-item.active {
  background: rgba(66, 185, 131, 0.2);
  border-left: 4px solid #42b983;
}

.agent-icon {
  width: 40px;
  height: 40px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 15px;
  font-size: 1.2em;
}

.agent-info h4 {
  margin: 0 0 5px 0;
  font-size: 1em;
  font-weight: 600;
}

.agent-info p {
  margin: 0;
  font-size: 0.8em;
  color: rgba(255, 255, 255, 0.7);
}
</style>