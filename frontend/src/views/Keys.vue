<template>
  <div class="keys-view">
    <nav class="breadcrumb-nav">
      <ul class="breadcrumb">
        <li><router-link to="/home">Home</router-link></li>
        <li>Keys</li>
      </ul>
    </nav>
    <h1>Key Management</h1>
    <div v-if="loadingKeys">Loading keys...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <button class="create-key-btn" @click="showCreateModal = true">Create New Key</button>
      <div class="merged-block">
        <h2>All Keys (Merged)</h2>
        <ul class="key-list">
          <li v-for="item in mergedKeys" :key="item.key" class="key-item">
            <div class="key-row-flex">
              <div class="key-details">
                <div><strong>Key:</strong> {{ item.key }}</div>
                <template v-if="item.local">
                  <div><strong>Local Key ID:</strong> {{ item.local.id }}</div>
                  <div><strong>Created:</strong> {{ item.local.created_at }}</div>
                  <div><strong>Session ID:</strong> {{ item.local.session_id }}</div>
                  <div class="key-actions">
                    <button @click="editKey(item.local)">Edit</button>
                    <button @click="deleteKey(item.local)">Delete</button>
                  </div>
                </template>
                <template v-if="item.server">
                  <div><strong>Server Key ID:</strong> {{ item.server.id }}</div>
                  <div><strong>User ID:</strong> {{ item.server.user_id }}</div>
                  <div><strong>Server Session ID:</strong> {{ item.server.session_id || item.server.local_session_id }}</div>
                  <div v-if="item.server.local_session_id"><strong>Local Session ID:</strong> {{ item.server.local_session_id }}</div>
                </template>
                <button @click="showMore[item.key] = !showMore[item.key]">
                  {{ showMore[item.key] ? 'Hide' : 'View More' }}
                </button>
                <pre v-if="showMore[item.key]">{{ item }}</pre>
              </div>
            </div>
          </li>
        </ul>
      </div>
    </div>

    <!-- Create Key Modal -->
    <div v-if="showCreateModal" class="modal-overlay" @click.self="showCreateModal = false">
      <div class="modal">
        <h2>Create New Key</h2>
        <form @submit.prevent="createKey">
          <label>Session:
            <select v-model="newKeySessionId" required>
              <option value="" disabled>Select a session</option>
              <option v-for="session in sessions" :key="session.id" :value="session.id">
                {{ session.description || ('Session ' + session.id) }}
              </option>
            </select>
          </label>
          <div class="modal-actions">
            <button type="submit">Create</button>
            <button type="button" @click="showCreateModal = false">Cancel</button>
          </div>
        </form>
        <div v-if="createError" class="error">{{ createError }}</div>
      </div>
    </div>

    <!-- Edit Key Modal -->
    <div v-if="showEditModal" class="modal-overlay" @click.self="closeEditModal">
      <div class="modal">
        <h2>Edit Key</h2>
        <form @submit.prevent="updateKey">
          <label>Key:
            <input v-model="editKeyData.key" required />
          </label>
          <div class="modal-actions">
            <button type="submit">Save</button>
            <button type="button" @click="closeEditModal">Cancel</button>
          </div>
        </form>
        <div v-if="editError" class="error">{{ editError }}</div>
      </div>
    </div>

    <!-- Delete Confirmation Modal -->
    <div v-if="showDeleteModal" class="modal-overlay" @click.self="closeDeleteModal">
      <div class="modal">
        <h2>Delete Key</h2>
        <p>Are you sure you want to delete this key?</p>
        <div class="modal-actions">
          <button @click="confirmDeleteKey">Yes, Delete</button>
          <button @click="closeDeleteModal">Cancel</button>
        </div>
        <div v-if="deleteError" class="error">{{ deleteError }}</div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'KeysView',
  data() {
    return {
      localKeys: [],
      serverKeys: [],
      mergedKeys: [],
      loadingKeys: true,
      error: '',
      showCreateModal: false,
      newKeySessionId: '',
      createError: '',
      showEditModal: false,
      editKeyData: {},
      editError: '',
      showDeleteModal: false,
      deleteKeyData: null,
      deleteError: '',
      sessions: [],
      showMore: {}
    }
  },
  mounted() {
    this.fetchKeys()
    this.fetchSessions()
  },
  methods: {
    fetchKeys() {
      this.loadingKeys = true
      this.error = ''
      fetch('/aetheronepysocialplugin/user')
        .then(res => res.json())
        .then(user => {
          return fetch(`/aetheronepysocialplugin/key/${user.server_user_id}`)
        })
        .then(res => res.json())
        .then(data => {
          this.localKeys = (data.data && data.data.local) ? data.data.local : []
          this.serverKeys = (data.data && data.data.server) ? data.data.server : []
          // Merge by key string
          const merged = {};
          for (const l of this.localKeys) {
            if (!l.key) continue;
            merged[l.key] = { key: l.key, local: l };
          }
          for (const s of this.serverKeys) {
            if (!s.key) continue;
            if (merged[s.key]) {
              merged[s.key].server = s;
            } else {
              merged[s.key] = { key: s.key, server: s };
            }
          }
          this.mergedKeys = Object.values(merged);
          this.loadingKeys = false
        })
        .catch(() => {
          this.error = 'Failed to load keys.'
          this.loadingKeys = false
        })
    },
    fetchSessions() {
      fetch('/aetheronepysocialplugin/sessions')
        .then(res => res.json())
        .then(data => {
          this.sessions = data.sessions || []
        })
        .catch(() => {
          this.sessions = []
        })
    },
    createKey() {
      this.createError = ''
      fetch('/aetheronepysocialplugin/key', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ local_session_id: this.newKeySessionId })
      })
        .then(res => res.json())
        .then(data => {
          if (data.status === 'success' || data.status === 'exists') {
            this.showCreateModal = false
            this.newKeySessionId = ''
            this.fetchKeys()
          } else {
            this.createError = data.message || 'Failed to create key.'
          }
        })
        .catch(() => {
          this.createError = 'Failed to create key.'
        })
    },
    editKey(key) {
      this.editKeyData = { ...key }
      this.showEditModal = true
      this.editError = ''
    },
    updateKey() {
      this.editError = ''
      fetch(`/aetheronepysocialplugin/key/${this.editKeyData.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ key: this.editKeyData.key })
      })
        .then(res => res.json())
        .then(data => {
          if (data.status === 'success') {
            this.showEditModal = false
            this.fetchKeys()
          } else {
            this.editError = data.message || 'Failed to update key.'
          }
        })
        .catch(() => {
          this.editError = 'Failed to update key.'
        })
    },
    closeEditModal() {
      this.showEditModal = false
      this.editKeyData = {}
    },
    deleteKey(key) {
      this.deleteKeyData = key
      this.showDeleteModal = true
      this.deleteError = ''
    },
    confirmDeleteKey() {
      fetch(`/aetheronepysocialplugin/key/${this.deleteKeyData.id}`, {
        method: 'DELETE'
      })
        .then(res => res.json())
        .then(data => {
          if (data.status === 'success') {
            this.showDeleteModal = false
            this.deleteKeyData = null
            this.fetchKeys()
          } else {
            this.deleteError = data.message || 'Failed to delete key.'
          }
        })
        .catch(() => {
          this.deleteError = 'Failed to delete key.'
        })
    },
    closeDeleteModal() {
      this.showDeleteModal = false
      this.deleteKeyData = null
    }
  }
}
</script>

<style scoped>
.keys-view {
  max-width: 900px;
  margin: 32px auto;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
  padding: 24px;
}
.breadcrumb-nav {
  margin-bottom: 16px;
}
.breadcrumb {
  display: flex;
  list-style: none;
  padding: 0;
  margin: 0;
  gap: 8px;
  font-size: 1em;
}
.breadcrumb li {
  color: #7e57c2;
}
.breadcrumb li:not(:last-child)::after {
  content: '>';
  margin: 0 8px;
  color: #aaa;
}
.breadcrumb a {
  color: #7e57c2;
  text-decoration: none;
}
.breadcrumb a:hover {
  text-decoration: underline;
}
.create-key-btn {
  background: #7e57c2;
  color: #fff;
  border: none;
  border-radius: 4px;
  padding: 8px 16px;
  cursor: pointer;
  font-size: 1em;
  font-weight: bold;
  margin-bottom: 18px;
  transition: background 0.2s;
}
.create-key-btn:hover {
  background: #5e35b1;
}
.merged-block {
  flex: 1;
  background: #f5f5f5;
  border-radius: 4px;
  padding: 16px;
  font-size: 0.97em;
}
.key-list {
  list-style: none;
  padding: 0;
}
.key-item {
  margin-bottom: 18px;
  border-bottom: 1px solid #eee;
  padding-bottom: 10px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.key-row-flex {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
}
.key-details {
  flex: 1;
}
.key-actions {
  display: flex;
  gap: 12px;
  margin-top: 6px;
}
.key-actions button {
  background: #eee;
  border: none;
  border-radius: 4px;
  padding: 6px 12px;
  cursor: pointer;
  font-size: 0.97em;
  transition: background 0.2s;
}
.key-actions button:hover {
  background: #d1c4e9;
}
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(0,0,0,0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
}
.modal {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 16px rgba(0,0,0,0.12);
  padding: 32px 24px;
  min-width: 320px;
  max-width: 90vw;
}
.modal-actions {
  display: flex;
  gap: 16px;
  justify-content: flex-end;
  margin-top: 18px;
}
.error {
  color: #d93025;
  font-weight: bold;
  margin: 12px 0;
}
</style> 