<template>
  <div id="app">
    <ChatView />
  </div>
</template>

<script setup lang="ts">
import ChatView from './views/ChatView.vue'
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  background: #f5f5f5;
}

#app {
  height: 100vh;
  overflow: hidden;
}
</style>