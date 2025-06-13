<template>
  <div class="user-bar">
    <div class="icon-group">
      <div class="icon-wrapper">
        <span class="icon-badge" v-if="notifications > 0">{{ notifications }}</span>
        <i class="fas fa-bell"></i>
      </div>
      <div class="icon-wrapper">
        <span class="icon-badge" v-if="messages > 0">{{ messages }}</span>
        <i class="fas fa-envelope"></i>
      </div>
    </div>
    <img class="avatar" :src="avatarUrl" alt="User Avatar" />
  </div>
</template>

<script>
export default {
  name: 'UserBar',
  props: {
    notifications: { type: Number, default: 0 },
    messages: { type: Number, default: 0 },
    avatarUrl: { type: String, default: 'https://randomuser.me/api/portraits/men/1.jpg' }
  }
}
</script>

<style scoped>
.user-bar {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding: 10px 30px 0 0;
  background: #fff;
}
.icon-group {
  display: flex;
  gap: 24px;
  margin-right: 20px;
}
.icon-wrapper {
  position: relative;
  font-size: 22px;
  color: #888;
}
.icon-badge {
  position: absolute;
  top: -8px;
  right: -10px;
  background: #2ee6c5;
  color: #fff;
  border-radius: 50%;
  padding: 2px 6px;
  font-size: 12px;
  font-weight: bold;
  border: 2px solid #fff;
}
.avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid #e0e0e0;
}
</style> 