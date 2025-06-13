<template>
  <div class="auth-page">
    <h2 v-if="mode==='login'">Login</h2>
    <h2 v-else>Register</h2>
    <form @submit.prevent="mode==='login' ? login() : register()">
      <div v-if="mode==='register'">
        <label>Username:<br>
          <input v-model="username" required />
        </label><br>
      </div>
      <label>Email:<br>
        <input v-model="email" type="email" required />
      </label><br>
      <label>Password:<br>
        <input v-model="password" type="password" required />
      </label><br>
      <button type="submit">{{ mode==='login' ? 'Login' : 'Register' }}</button>
    </form>
    <div v-if="error" class="error">{{ error }}</div>
    <div class="switch-mode">
      <span v-if="mode==='login'">Need an account? <a href="#" @click.prevent="mode='register'">Register</a></span>
      <span v-else>Already have an account? <a href="#" @click.prevent="mode='login'">Login</a></span>
    </div>
  </div>
</template>

<script>
const API_BASE = '/aetheronepysocial/local';

export default {
  name: 'AuthForm',
  data() {
    return {
      mode: 'login',
      username: '',
      email: '',
      password: '',
      error: ''
    }
  },
  methods: {
    login() {
      this.error = ''
      fetch(`${API_BASE}/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: this.email, password: this.password })
      })
        .then(res => res.json())
        .then(data => {
          if (data.access_token || data.token) {
            this.saveToken(data.access_token || data.token, this.email)
            this.$router.push('/home')
          } else {
            this.error = data.message || 'Login failed.'
          }
        })
        .catch(() => { this.error = 'Login failed.' })
    },
    register() {
      this.error = ''
      fetch(`${API_BASE}/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: this.username, email: this.email, password: this.password })
      })
        .then(res => res.json())
        .then(data => {
          if (data.access_token || data.token) {
            this.saveToken(data.access_token || data.token, this.email)
            this.$router.push('/home')
          } else {
            this.error = data.message || 'Registration failed.'
          }
        })
        .catch(() => { this.error = 'Registration failed.' })
    },
    saveToken(token, email) {
      const selectedServerId = localStorage.getItem('selectedServerId')
      let userTokens = JSON.parse(localStorage.getItem('userTokens') || '{}')
      userTokens[selectedServerId] = token
      localStorage.setItem('userTokens', JSON.stringify(userTokens))
      let userEmails = JSON.parse(localStorage.getItem('userEmails') || '{}')
      userEmails[selectedServerId] = email
      localStorage.setItem('userEmails', JSON.stringify(userEmails))
    }
  }
}
</script>

<style scoped>
.auth-page {
  max-width: 400px;
  margin: 60px auto;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.07);
  padding: 2em 2em 1em 2em;
  text-align: center;
}
input {
  width: 100%;
  padding: 0.5em;
  margin: 0.5em 0 1em 0;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-size: 1em;
}
button {
  background: #0077b5;
  color: #fff;
  border: none;
  border-radius: 4px;
  padding: 0.7em 2em;
  font-size: 1em;
  cursor: pointer;
  margin-top: 1em;
}
button:hover {
  background: #005983;
}
.error {
  color: #d93025;
  margin-top: 1em;
}
.switch-mode {
  margin-top: 1.5em;
  color: #444;
}
.switch-mode a {
  color: #0077b5;
  cursor: pointer;
  text-decoration: underline;
}
</style> 