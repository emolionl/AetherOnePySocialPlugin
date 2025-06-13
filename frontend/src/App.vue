<template>
  <div id="app">
    <TopNav avatarUrl="https://randomuser.me/api/portraits/men/1.jpg" />
    <router-view />
  </div>
</template>

<script>
import TopNav from './components/TopNav.vue'

export default {
  name: 'App',
  components: { TopNav }
}
</script>

<style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #2c3e50;
  min-height: 100vh;
  background: #f8f9fa;
}
header {
  font-size: 1.5em;
  font-weight: bold;
  letter-spacing: 1px;
}
</style>
