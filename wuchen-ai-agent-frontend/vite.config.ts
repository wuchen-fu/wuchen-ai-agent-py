import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue'; // 导入vue插件
import vueJsx from '@vitejs/plugin-vue-jsx'; // 导入vue-jsx插件
import { fileURLToPath } from "node:url"; // 导入vue-devtools插件

export default defineConfig({
  plugins: [
    vue(), // 使用vue插件
    vueJsx(), // 使用vue-jsx插件
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
  },
  server: {
    port: 9101,
  },
})
