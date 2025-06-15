<template>
  <div class="server-setup">
    <div v-if="userEmail" class="user-email">Logged in as: {{ userEmail }}</div>
    <h2>Server Setup</h2>
    <div v-if="loading">Loading...</div>
    <div v-else>
      <div v-if="servers.length === 0">
        <form @submit.prevent="addServer">
          <label>Server URL:<br>
            <input v-model="url" required placeholder="https://example.com" />
          </label><br>
          <label>Description:<br>
            <input v-model="description" placeholder="Description (optional)" />
          </label><br>
          <button type="submit">Add Server</button>
        </form>
        <div v-if="error" class="error">{{ error }}</div>
      </div>
      <div v-else>
        <form v-if="editId" @submit.prevent="saveEdit">
          <label>Edit URL:<br>
            <input v-model="editUrl" required />
          </label><br>
          <label>Edit Description:<br>
            <input v-model="editDescription" />
          </label><br>
          <button type="submit">Save</button>
          <button type="button" @click="cancelEdit">Cancel</button>
        </form>
        <div v-else>
          <label>Select a server:</label>
          <select v-model="selectedServerId">
            <option v-for="s in servers" :key="s.id" :value="s.id">{{ s.url }} ({{ s.description }})</option>
          </select>
          <button @click="selectServer">Continue</button>
        </div>
        <h3 style="margin-top:2em;">All Servers</h3>
        <table class="servers-table">
          <thead>
            <tr><th>URL</th><th>Description</th><th>Actions</th></tr>
          </thead>
          <tbody>
            <tr v-for="s in servers" :key="s.id">
              <td>{{ s.url }}</td>
              <td>{{ s.description }}</td>
              <td>
                <button @click="startEdit(s)">Edit</button>
                <button @click="deleteServer(s.id)">Delete</button>
              </td>
            </tr>
          </tbody>
        </table>
        <form @submit.prevent="addServer" style="margin-top:2em;">
          <label>New Server URL:<br>
            <input v-model="url" required placeholder="https://example.com" />
          </label><br>
          <label>New Description:<br>
            <input v-model="description" placeholder="Description (optional)" />
          </label><br>
          <button type="submit">Add Server</button>
        </form>
        <div v-if="error" class="error">{{ error }}</div>
      </div>
    </div>
  </div>
</template>

<script>
const API_BASE = '/aetheronepysocialplugin';

export default {
  name: 'ServerSetup',
  data() {
    return {
      servers: [],
      loading: true,
      url: '',
      description: '',
      error: '',
      selectedServerId: null,
      editId: null,
      editUrl: '',
      editDescription: '',
      userEmail: ''
    }
  },
  mounted() {
    this.fetchServers()
    this.updateUserEmail()
  },
  watch: {
    selectedServerId() {
      this.updateUserEmail()
    }
  },
  methods: {
    fetchServers() {
      this.loading = true
      fetch(`${API_BASE}/server`)
        .then(res => res.json())
        .then(data => {
          this.servers = (data.servers || [])
          this.loading = false
          if (this.servers.length > 0) {
            // Try to restore selected server from localStorage
            const sel = localStorage.getItem('selectedServerId')
            if (sel && this.servers.find(s => s.id == sel)) {
              this.selectedServerId = Number(sel)
            } else {
              this.selectedServerId = this.servers[0].id
            }
            this.updateUserEmail()
          }
        })
    },
    addServer() {
      this.error = ''
      fetch(`${API_BASE}/server`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: this.url, description: this.description })
      })
        .then(res => res.json())
        .then(data => {
          if (data.status === 'success') {
            this.url = ''
            this.description = ''
            this.fetchServers()
          } else {
            this.error = data.message || 'Failed to add server.'
          }
        })
        .catch(() => { this.error = 'Failed to add server.' })
    },
    selectServer() {
      if (this.selectedServerId) {
        localStorage.setItem('selectedServerId', this.selectedServerId)
        this.updateUserEmail()
        this.$router.push('/home')
      }
    },
    startEdit(server) {
      this.editId = server.id
      this.editUrl = server.url
      this.editDescription = server.description
    },
    cancelEdit() {
      this.editId = null
      this.editUrl = ''
      this.editDescription = ''
    },
    saveEdit() {
      this.error = 'Edit not implemented (backend needed)'
      // To implement: PATCH/PUT endpoint in Flask, then call fetchServers()
      // fetch(`${API_BASE}/server/${this.editId}`, { method: 'PUT', ... })
      //   .then(...)
      //   .finally(() => this.cancelEdit())
    },
    deleteServer(id) {
      if (!confirm('Are you sure you want to delete this server?')) return
      fetch(`${API_BASE}/server/${id}`, { method: 'DELETE' })
        .then(res => res.json())
        .then(data => {
          if (data.status === 'success') {
            if (String(id) === String(localStorage.getItem('selectedServerId'))) {
              localStorage.removeItem('selectedServerId')
            }
            this.fetchServers()
          } else {
            this.error = data.message || 'Failed to delete server.'
          }
        })
        .catch(() => { this.error = 'Failed to delete server.' })
    },
    updateUserEmail() {
      const userEmails = JSON.parse(localStorage.getItem('userEmails') || '{}')
      this.userEmail = this.selectedServerId && userEmails[this.selectedServerId] ? userEmails[this.selectedServerId] : ''
    }
  }
}
</script>

<style scoped>
.server-setup {
  max-width: 600px;
  margin: 60px auto;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.07);
  padding: 2em 2em 1em 2em;
  text-align: center;
}
.user-email {
  color: #0077b5;
  font-weight: bold;
  margin-bottom: 1em;
  font-size: 1.1em;
}
input, select {
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
.servers-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 1em;
}
.servers-table th, .servers-table td {
  border: 1px solid #eee;
  padding: 0.5em 1em;
}
.servers-table th {
  background: #f8f9fa;
}
.error {
  color: #d93025;
  margin-top: 1em;
}
</style> 