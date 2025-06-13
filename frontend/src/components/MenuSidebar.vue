<template>
  <nav class="top-menu">
    <ul>
      <li><button @click="$emit('login')">Login</button></li>
      <li><button @click="$emit('logout')">Logout</button></li>
      <li><button @click="$emit('create-session')">Create Session</button></li>
      <li><button @click="$emit('see-sessions')">See Sessions</button></li>
      <li><button @click="$emit('about')">About</button></li>
    </ul>
  </nav>
</template>

<script>
export default {
  name: 'MenuSidebar',
}
</script>

<style scoped>
.top-menu {
  position: sticky;
  top: 0;
  left: 0;
  width: 100%;
  background: #2c3e50;
  z-index: 1200;
  box-shadow: 0 2px 8px rgba(0,0,0,0.03);
  padding: 0 0 0 10px;
}
.top-menu ul {
  display: flex;
  align-items: center;
  margin: 0;
  padding: 0;
  list-style: none;
  height: 56px;
}
.top-menu li {
  margin-right: 16px;
}
.top-menu button {
  background: none;
  color: #fff;
  border: none;
  font-size: 1em;
  padding: 10px 16px;
  border-radius: 4px;
  cursor: pointer;
  transition: background 0.2s, color 0.2s;
}
.top-menu button:hover {
  background: #42b983;
  color: #fff;
}
</style> 