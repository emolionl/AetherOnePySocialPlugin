<template>
  <div class="analysis-view">
    <h1>Analysis</h1>
    <div v-if="loadingKeys">Loading keys...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div v-if="keys.length === 0">No keys found for this user.</div>
      <ul v-else class="key-list">
        <li v-for="key in keys" :key="key.key" class="key-item">
          <div class="key-header">
            <span class="key-value">{{ key.key }}</span>
            <button class="view-analyses-btn" @click="goToAnalyses(key.key)">View Analyses</button>
          </div>
        </li>
      </ul>
    </div>
  </div>
</template>

<script>
export default {
  name: 'AnalysisView',
  data() {
    return {
      keys: [],
      analyses: {},
      analysisDetails: {},
      loadingKeys: true,
      loadingAnalysesKey: '',
      error: '',
      userId: ''
    }
  },
  mounted() {
    this.fetchUserIdAndKeys()
  },
  methods: {
    fetchUserIdAndKeys() {
      // Fetch user info to get user_id
      fetch('/aetheronepysocial/user')
        .then(res => res.json())
        .then(user => {
          this.userId = user.server_user_id
          return fetch(`/aetheronepysocial/key/${this.userId}`)
        })
        .then(res => res.json())
        .then(data => {
          this.keys = (data.data && data.data.local) ? data.data.local : []
          this.loadingKeys = false
        })
        .catch(() => {
          this.error = 'Failed to load keys.'
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
  max-width: 700px;
  margin: 32px auto;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
  padding: 24px;
}
.key-list {
  list-style: none;
  padding: 0;
}
.key-item {
  margin-bottom: 24px;
  border-bottom: 1px solid #eee;
  padding-bottom: 12px;
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
.analysis-list {
  list-style: none;
  padding: 0 0 0 16px;
}
.analysis-item {
  margin-bottom: 10px;
}
.analysis-detail {
  background: #f5f5f5;
  border-radius: 4px;
  padding: 8px;
  margin-top: 6px;
  font-size: 0.95em;
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
</style> 