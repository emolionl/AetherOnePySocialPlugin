<template>
  <nav class="topnav">
    <div class="nav-left">
      <div class="logo">
        <!-- Social SVG icon -->
        <svg width="36" height="36" viewBox="0 0 36 36" fill="none" xmlns="http://www.w3.org/2000/svg">
          <circle cx="18" cy="18" r="18" fill="#b39ddb"/>
          <circle cx="10" cy="18" r="4" fill="#fff"/>
          <circle cx="26" cy="18" r="4" fill="#fff"/>
          <circle cx="18" cy="10" r="4" fill="#fff"/>
          <circle cx="18" cy="26" r="4" fill="#fff"/>
          <line x1="14" y1="18" x2="18" y2="14" stroke="#b39ddb" stroke-width="2"/>
          <line x1="22" y1="18" x2="18" y2="14" stroke="#b39ddb" stroke-width="2"/>
          <line x1="14" y1="18" x2="18" y2="22" stroke="#b39ddb" stroke-width="2"/>
          <line x1="22" y1="18" x2="18" y2="22" stroke="#b39ddb" stroke-width="2"/>
        </svg>
      </div>
    </div>
    <div class="nav-center">
      <router-link to="/home" class="nav-item active" style="text-decoration:none; color:inherit;">
        <i class="fas fa-home"></i>
        <span>Home</span>
      </router-link>
      <router-link to="/sessions" class="nav-item" style="text-decoration:none; color:inherit;">
        <i class="fas fa-list"></i>
        <span>Sessions</span>
      </router-link>
      <router-link to="/analysis" class="nav-item" style="text-decoration:none; color:inherit;">
        <i class="fas fa-chart-pie"></i>
        <span>Shared Analysis</span>
      </router-link>
      <div class="nav-item" @click="$router.push('/servers')" style="position:relative;">
        <i class="fas fa-server"></i>
        <span>Servers</span>
        <span v-if="serverSelected" class="badge badge-green"><i class="fas fa-check"></i></span>
      </div>
      <div class="nav-item">
        <i class="fas fa-bell"></i>
        <span>Notifications</span>
        <span class="badge">3</span>
      </div>
    </div>
    <div class="nav-right">
      <template v-if="userEmail">
        <!-- Spiritual symbol SVG avatar -->
        <span class="avatar spiritual-avatar" @click="toggleDropdown">
          <svg width="36" height="36" viewBox="0 0 36 36" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="18" cy="18" r="18" fill="#f5f3e7"/>
            <g>
              <path d="M18 7C19.5 12 27 13.5 27 18C27 22.5 19.5 24 18 29C16.5 24 9 22.5 9 18C9 13.5 16.5 12 18 7Z" fill="#b39ddb"/>
              <circle cx="18" cy="18" r="4" fill="#9575cd"/>
              <path d="M18 12V24" stroke="#9575cd" stroke-width="1.5" stroke-linecap="round"/>
              <path d="M12 18H24" stroke="#9575cd" stroke-width="1.5" stroke-linecap="round"/>
            </g>
          </svg>
        </span>
        <span class="me-label" @click="toggleDropdown" style="cursor:pointer;">Me <i class="fas fa-caret-down"></i></span>
        <div v-if="dropdownOpen" class="dropdown-menu">
          <div class="dropdown-email">{{ userEmail }}</div>
          <router-link to="/settings" class="dropdown-item">Settings</router-link>
          <div class="dropdown-item" @click="logout">Logout</div>
        </div>
      </template>
      <template v-else>
        <button class="login-btn" @click="$router.push('/auth')">Login</button>
      </template>
    </div>
  </nav>
</template>

<script>
export default {
  name: 'TopNav',
  props: {
    avatarUrl: {
      type: String,
      default: 'https://randomuser.me/api/portraits/men/1.jpg'
    }
  },
  data() {
    return {
      serverSelected: false,
      userEmail: '',
      dropdownOpen: false
    }
  },
  mounted() {
    this.checkServer()
    this.$watch(() => this.$route.fullPath, this.checkServer)
    document.addEventListener('click', this.handleClickOutside)
  },
  beforeUnmount() {
    document.removeEventListener('click', this.handleClickOutside)
  },
  methods: {
    checkServer() {
      this.serverSelected = !!localStorage.getItem('selectedServerId')
      const selectedServerId = localStorage.getItem('selectedServerId')
      const userTokens = JSON.parse(localStorage.getItem('userTokens') || '{}')
      const userEmails = JSON.parse(localStorage.getItem('userEmails') || '{}')
      this.userEmail = (selectedServerId && userTokens[selectedServerId] && userEmails[selectedServerId]) ? userEmails[selectedServerId] : ''
    },
    toggleDropdown() {
      this.dropdownOpen = !this.dropdownOpen
    },
    handleClickOutside(e) {
      if (!this.$el.contains(e.target)) {
        this.dropdownOpen = false
      }
    },
    logout() {
      // Remove user token and email for the selected server
      const selectedServerId = localStorage.getItem('selectedServerId')
      let userTokens = JSON.parse(localStorage.getItem('userTokens') || '{}')
      let userEmails = JSON.parse(localStorage.getItem('userEmails') || '{}')
      if (selectedServerId) {
        delete userTokens[selectedServerId]
        delete userEmails[selectedServerId]
        localStorage.setItem('userTokens', JSON.stringify(userTokens))
        localStorage.setItem('userEmails', JSON.stringify(userEmails))
      }
      this.dropdownOpen = false
      this.$router.push('/auth')
    }
  }
}
</script>

<style scoped>
.topnav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fff;
  border-bottom: 1px solid #e0e0e0;
  padding: 0 32px;
  height: 56px;
  position: sticky;
  top: 0;
  z-index: 1000;
}
.nav-left {
  display: flex;
  align-items: center;
  gap: 16px;
}
.logo {
  background: #0077b5;
  color: #fff;
  font-weight: bold;
  font-size: 2em;
  width: 36px;
  height: 36px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.search-box {
  display: flex;
  align-items: center;
  background: #eef3f8;
  border-radius: 4px;
  padding: 0 10px;
  height: 36px;
}
.search-box i {
  color: #888;
  margin-right: 6px;
}
.search-box input {
  border: none;
  background: transparent;
  outline: none;
  font-size: 1em;
  width: 160px;
}
.nav-center {
  display: flex;
  align-items: center;
  gap: 36px;
}
.nav-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  color: #666;
  font-size: 0.95em;
  position: relative;
  cursor: pointer;
  min-width: 60px;
}
.nav-item i {
  font-size: 1.3em;
  margin-bottom: 2px;
}
.nav-item.active {
  color: #111;
  font-weight: bold;
}
.nav-item.active::after {
  content: '';
  display: block;
  margin: 4px auto 0 auto;
  width: 32px;
  height: 3px;
  background: #111;
  border-radius: 2px;
}
.badge {
  position: absolute;
  top: 0px;
  right: 10px;
  background: #d93025;
  color: #fff;
  border-radius: 50%;
  font-size: 0.7em;
  width: 16px;
  height: 16px;
  font-weight: bold;
  border: 2px solid #fff;
  z-index: 2;
  display: flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
  padding: 0;
}
.badge-green {
  background: #2ecc40 !important;
  color: #fff;
  border: 2px solid #fff;
}
.badge-green i {
  font-size: 0.8em;
  line-height: 1;
}
.nav-right {
  display: flex;
  align-items: center;
  gap: 8px;
  position: relative;
}
.avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid #e0e0e0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f3e7;
  cursor: pointer;
}
.spiritual-avatar svg {
  display: block;
}
.me-label {
  color: #444;
  margin-left: 8px;
  font-weight: 500;
  cursor: pointer;
}
.dropdown-menu {
  position: absolute;
  top: 48px;
  right: 0;
  background: #fff;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.07);
  min-width: 140px;
  z-index: 2000;
  padding: 0.5em 0;
}
.dropdown-item {
  padding: 0.7em 1.2em;
  cursor: pointer;
  color: #444;
  font-size: 1em;
  transition: background 0.2s;
}
.dropdown-item:hover {
  background: #f5f3e7;
}
.login-btn {
  background: #0077b5;
  color: #fff;
  border: none;
  border-radius: 4px;
  padding: 0.5em 1.2em;
  font-size: 1em;
  cursor: pointer;
  margin-left: 8px;
}
.login-btn:hover {
  background: #005983;
}
.dropdown-email {
  padding: 0.7em 1.2em;
  color: #888;
  font-size: 0.95em;
  border-bottom: 1px solid #eee;
  cursor: default;
  user-select: text;
}
</style> 