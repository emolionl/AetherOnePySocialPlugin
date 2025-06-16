<template>
  <div class="analysis-view">
    <nav class="breadcrumb-nav">
      <ul class="breadcrumb">
        <li><router-link to="/home">Home</router-link></li>
        <li>Analysis</li>
      </ul>
    </nav>
    <h1>Analysis</h1>
    <div v-if="loadingKeys">Loading keys...</div>
    <div v-else-if="error" class="error">
      {{ error }}
      <div v-if="errorDetails">
        <div v-if="errorDetails.explanation">Explanation: {{ errorDetails.explanation }}</div>
        <div v-if="errorDetails.searched_key">Searched Key: {{ errorDetails.searched_key }}</div>
        <div v-if="errorDetails.suggestions && errorDetails.suggestions.length">
          <h4>Suggestions:</h4>
          <ul>
            <li v-for="s in errorDetails.suggestions" :key="s">{{ s }}</li>
          </ul>
        </div>
      </div>
    </div>
    <div v-else>
      <div v-if="mergedKeys.length === 0">No keys found for this user.</div>
      <div class="key-lists">
        <div class="merged-block">
          <h2>All Keys (Merged)</h2>
          <ul>
            <li v-for="item in mergedKeys" :key="item.key" class="key-item">
              <div class="key-row-flex">
                <div class="key-details">
                  <div><strong>Key:</strong> {{ item.key }}</div>
                  <template v-if="item.local">
                    <div><strong>Local Key ID:</strong> {{ item.local.id }}</div>
                    <div><strong>Created:</strong> {{ item.local.created_at }}</div>
                    <div><strong>Session ID:</strong> {{ item.local.session_id }}</div>
                  </template>
                  <template v-if="item.server">
                    <div><strong>Server Key ID:</strong> {{ item.server.id }}</div>
                    <div><strong>My Key:</strong> {{ item.server.my_key ? 'Yes' : 'No' }}</div>
                    <div><strong>Server Session ID:</strong> {{ item.server.session_id }}</div>
                    <div v-if="item.server.local_session_id"><strong>Local Session ID:</strong> {{ item.server.local_session_id }}</div>
                  </template>
                  <button @click="showMore[item.key] = !showMore[item.key]">
                    {{ showMore[item.key] ? 'Hide' : 'View More' }}
                  </button>
                  <pre v-if="showMore[item.key]">{{ item }}</pre>
                </div>
                <div class="key-actions-right">
                  <button class="view-analyses-btn" @click="goToAnalyses(item.key)">View Analyses</button>
                </div>
              </div>
            </li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'AnalysisView',
  data() {
    return {
      localKeys: [],
      serverKeys: [],
      mergedKeys: [],
      loadingKeys: true,
      error: '',
      errorDetails: null,
      userId: '',
      showMore: {}
    }
  },
  mounted() {
    this.fetchUserIdAndKeys()
  },
  methods: {
    fetchUserIdAndKeys() {
      fetch('/aetheronepysocialplugin/user')
        .then(res => res.json())
        .then(user => {
          this.userId = user.server_user_id
          return fetch(`/aetheronepysocialplugin/key/${this.userId}`)
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
        .catch((err) => {
          if (err && err.error && err.error.detail) {
            this.error = err.error.detail.message || 'Failed to load keys.'
            this.errorDetails = err.error.detail
          } else {
            this.error = 'Failed to load keys.'
            this.errorDetails = null
          }
          this.loadingKeys = false
        })
    },
    goToAnalyses(key) {
      this.$router.push(`/analysis/${key}`);
    }
  }
}
</script>

<style scoped>
.analysis-view {
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
.key-lists {
  display: flex;
  gap: 32px;
}
.merged-block {
  flex: 1;
  background: #f5f5f5;
  border-radius: 4px;
  padding: 16px;
  font-size: 0.97em;
}
.key-item {
  margin-bottom: 18px;
  border-bottom: 1px solid #eee;
  padding-bottom: 10px;
}
.key-header {
  display: flex;
  align-items: center;
  gap: 16px;
  justify-content: space-between;
}
.key-value {
  font-family: monospace;
  font-size: 1.1em;
  color: #7e57c2;
}
.loading-indicator {
  color: #7e57c2;
  font-weight: bold;
  margin: 8px 0;
}
.error {
  color: #d93025;
  font-weight: bold;
  margin: 12px 0;
}
.view-analyses-btn {
  background: #7e57c2;
  color: #fff;
  border: none;
  border-radius: 4px;
  padding: 8px 16px;
  cursor: pointer;
  font-size: 1em;
  font-weight: bold;
  transition: background 0.2s;
}
.view-analyses-btn:hover {
  background: #5e35b1;
}
.key-row-flex {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
}
.key-details {
  flex: 1;
}
.key-actions-right {
  display: flex;
  align-items: flex-start;
  margin-left: 24px;
}
</style> 