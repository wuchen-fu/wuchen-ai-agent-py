import axios from 'axios';

// 创建axios实例
const apiClient = axios.create({
  baseURL: 'http://localhost:9091/api',
  timeout: 10000,
});

// Agent类型定义
export interface Agent {
  id: string;
  name: string;
  description: string;
  welcomeMessage: string;
  icon?: string;
}

// 消息类型定义
export interface Message {
  id: string;
  sessionId: string;
  agentId: string;
  content: string;
  sender: 'user' | 'ai';
  timestamp: Date;
}

// 后端接口返回的数据结构
interface AgentApiResponse {
  configured_agents: string[];
  available_agents: string[];
  unavailable_agents: string[];
  agent_details: Array<{
    id: string;
    name: string;
    icon: string;
  }>;
}

// 获取智能体列表
export const getAgents = async (): Promise<Agent[]> => {
  try {
    console.log('开始调用 /api/agents 接口'); // 添加调试日志
    const response = await apiClient.get<AgentApiResponse>('/agents');
    console.log('从后端获取的原始数据:', response.data); // 添加调试日志
    
    // 将后端返回的数据转换为前端需要的Agent数组格式
    const agents = response.data.agent_details.map(agent => ({
      id: agent.id,
      name: agent.name,
      icon: agent.icon,
      description: '', // 后端接口未提供description字段，暂时留空
      welcomeMessage: '' // 后端接口未提供welcomeMessage字段，暂时留空
    }));
    
    console.log('转换后的agents数据:', agents); // 添加调试日志
    return agents;
  } catch (error) {
    console.error('获取智能体列表失败:', error);
    // 模拟数据用于演示
    return [
      { id: '1', name: '客服助手', description: '处理客户问题', welcomeMessage: '您好，我是客服助手，有什么可以帮助您的吗？' },
      { id: '2', name: '技术助手', description: '解答技术问题', welcomeMessage: '您好，我是技术助手，有任何技术问题都可以问我！' },
      { id: '3', name: '生活助手', description: '日常生活助手', welcomeMessage: '您好，我是生活助手，让生活更简单是我的目标！' }
    ];
  }
};

// 创建会话
export const createSession = (agentId: string, userId: string): string => {
  // 前端生成会话ID
  return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
};

// 处理缓冲区中剩余的数据
function processBuffer(buffer: string, onMessage: (data: string) => void, onDone?: () => void) {
  if (buffer) {
    const trimmedBuffer = buffer.trim();
    console.log('处理缓冲区数据:', trimmedBuffer); // 调试日志
    processLine(trimmedBuffer, onMessage, onDone);
  }
}



// 发送消息（流式方式）
export const sendMessageStream = async (
  sessionId: string, 
  agentId: string, 
  userId: string, 
  content: string,
  onMessage: (data: string) => void,
  onError: (error: any) => void,
  onDone?: () => void
): Promise<void> => {
  try {
    // 根据API文档，使用POST方式发送请求体数据
    const requestData = {
      message: content,
      chat_id: sessionId,
      agent_type: agentId,
      user_id: userId
    };

    // 使用fetch API发送POST请求
    const response = await fetch(`${apiClient.defaults.baseURL}/stream_chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(requestData)
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    if (!response.body) {
      throw new Error('ReadableStream not supported');
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = ''; // 用于累积未完成的数据

    // 读取流式数据
    while (true) {
      const { done, value } = await reader.read();
      
      if (done) {
        // 处理缓冲区中剩余的数据
        if (buffer) {
          processBuffer(buffer, onMessage, onDone);
        }
        if (onDone) onDone();
        break;
      }

      const chunk = decoder.decode(value, { stream: true });
      console.log('原始数据块:', chunk); // 调试日志
      
      // 累积到缓冲区
      buffer += chunk;
      
      // 尝试按换行符分割处理
      const lines = buffer.split('\n');
      
      // 保留最后一个可能不完整的行在缓冲区中
      buffer = lines.pop() || '';
      
      // 处理完整的行
      for (const line of lines) {
        const trimmedLine = line.trim();
        if (trimmedLine.length > 0) {
          console.log('处理行:', trimmedLine); // 调试日志
          processLine(trimmedLine, onMessage, onDone);
        }
      }
      
      // 如果缓冲区中没有换行符，尝试直接处理
      if (buffer && !buffer.includes('\n')) {
        console.log('处理缓冲区（无换行符）:', buffer); // 调试日志
        processLine(buffer, onMessage, onDone);
        buffer = ''; // 清空缓冲区
      }
    }
    
    reader.releaseLock();
  } catch (error) {
    console.error('流式请求错误:', error); // 调试日志
    onError(error);
  }
};

// 处理单行数据
function processLine(line: string, onMessage: (data: string) => void, onDone?: () => void) {
  if (line.length === 0) return;
  
  console.log('处理行:', line); // 调试日志
  
  // 检查是否是结束标记
  if (line === '[DONE]') {
    if (onDone) onDone();
    return;
  }
  
  // 处理SSE格式的数据（data: 前缀）
  if (line.startsWith('data: ')) {
    const jsonPart = line.slice(6).trim(); // 移除 "data: " 前缀
    
    if (jsonPart.length === 0) {
      console.log('空的数据行，跳过');
      return;
    }
    
    try {
      const jsonData = JSON.parse(jsonPart);
      console.log('解析的JSON数据:', jsonData); // 调试日志
      
      // 检查是否是结束事件
      if (jsonData.event === 'end') {
        if (onDone) onDone();
        return;
      }
      
      // 检查是否是错误事件
      if (jsonData.event === 'error') {
        const errorText = jsonData.text || jsonData.data || '未知错误';
        console.error('服务器返回错误:', errorText);
        onMessage(`错误: ${errorText}`);
        return;
      }
      
      // 提取数据内容，优先使用 text 字段
      if (jsonData.text) {
        console.log('发送内容到前端:', jsonData.text); // 调试日志
        onMessage(jsonData.text);
      } else if (jsonData.data) {
        // 兼容旧格式
        console.log('发送内容到前端:', jsonData.data); // 调试日志
        onMessage(jsonData.data);
      }
      
      // 可以处理元数据
      if (jsonData.metadata) {
        console.log('元数据:', jsonData.metadata);
      }
      
      return;
    } catch (error) {
      console.log('JSON解析失败，尝试其他格式:', error);
      // 如果JSON解析失败，且不是空内容，才尝试按纯文本处理
      if (jsonPart.length > 0) {
        console.log('处理纯文本数据:', jsonPart); // 调试日志
        onMessage(jsonPart);
      }
      return;
    }
  }
  
  // 尝试直接解析JSON格式的数据（没有data:前缀的情况）
  try {
    const jsonData = JSON.parse(line);
    console.log('解析的JSON数据:', jsonData); // 调试日志
    
    // 检查是否是结束事件
    if (jsonData.event === 'end') {
      if (onDone) onDone();
      return;
    }
    
    // 检查是否是错误事件
    if (jsonData.event === 'error') {
      const errorText = jsonData.text || jsonData.data || '未知错误';
      console.error('服务器返回错误:', errorText);
      onMessage(`错误: ${errorText}`);
      return;
    }
    
    // 提取数据内容
    if (jsonData.text) {
      console.log('发送内容到前端:', jsonData.text); // 调试日志
      onMessage(jsonData.text);
    } else if (jsonData.data) {
      // 兼容旧格式
      console.log('发送内容到前端:', jsonData.data); // 调试日志
      onMessage(jsonData.data);
    }
    
    // 可以处理元数据
    if (jsonData.metadata) {
      console.log('元数据:', jsonData.metadata);
    }
    
    return;
  } catch (error) {
    console.log('JSON解析失败，尝试其他格式:', error);
  }
  
  // 如果不是任何已知格式，且不是空的data:行，才按纯文本处理
  if (line !== 'data:') {
    console.log('处理纯文本数据:', line); // 调试日志
    onMessage(line);
  } else {
    console.log('跳过空的data:行');
  }
}
