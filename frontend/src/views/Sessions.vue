<template>
  <div class="sessions-view">
    <h1>Sessions</h1>
    <div v-if="loading">Loading sessions...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <ul v-else>
      <li v-for="session in sessions" :key="session.id" class="session-item">
        <div class="session-info">
          <div>
            <strong>ID:</strong> {{ session.id }}<br>
            <strong>Description:</strong> {{ session.description }}<br>
            <strong>Intention:</strong> {{ session.intention }}<br>
            <strong>Created:</strong> {{ session.created }}<br>
          </div>
          <button class="share-btn" @click="openShareModal(session)">Share</button>
        </div>
        <hr>
      </li>
    </ul>

    <div v-if="showModal" class="modal-overlay" @click.self="closeModal">
      <div class="modal">
        <h2>Share Session (ID: {{ selectedSession?.id }})</h2>
        <div class="modal-content">
          <label>
            <input type="radio" value="new" v-model="shareMode"> Create new key
          </label>
          <label>
            <input type="radio" value="existing" v-model="shareMode"> Use existing key
          </label>
          <div v-if="shareMode === 'existing'" class="existing-key-select">
            <label for="existingKey">Select Key:</label>
            <select v-model="selectedKey" id="existingKey">
              <option v-for="key in keys" :key="key.key" :value="key.key">{{ key.key }}</option>
            </select>
          </div>
        </div>
        <div class="timeline">
          <div v-for="(msg, i) in timeline" :key="i" :class="['timeline-item', msg.type]">
            <span class="timeline-dot"></span>
            <span class="timeline-msg">{{ msg.text }}</span>
          </div>
        </div>
        <div v-if="loading" class="loading-indicator">Processing...</div>
        <div v-if="shareLoading" class="loading-indicator">Processing...</div>
        <div class="modal-actions">
          <button v-if="!shareComplete" @click="submitShare" :disabled="shareMode === 'existing' && !selectedKey || shareLoading">Submit</button>
          <button @click="closeModal" :disabled="shareLoading || shareComplete">Cancel</button>
          <button v-if="shareComplete" @click="goToAnalysis" class="go-analysis-btn">Go to Analysis</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'SessionsView',
  data() {
    return {
      sessions: [],
      loading: true,
      error: '',
      showModal: false,
      selectedSession: null,
      shareMode: 'new',
      keys: [],
      selectedKey: '',
      timeline: [],
      autoCloseTimeout: null,
      shareComplete: false,
      analysisUrl: '/analysis',
      shareLoading: false
    }
  },
  mounted() {
    this.fetchSessions()
  },
  methods: {
    fetchSessions() {
      fetch('/aetheronepysocial/sessions')
        .then(res => res.json())
        .then(data => {
          this.sessions = data.sessions || []
          this.loading = false
        })
        .catch(() => {
          this.error = 'Failed to load sessions.'
          this.loading = false
        })
    },
    openShareModal(session) {
      this.selectedSession = session
      this.showModal = true
      this.shareMode = 'new'
      this.selectedKey = ''
      this.keys = []
      this.timeline = []
      this.autoCloseTimeout = null
      this.shareComplete = false
      // Fetch existing keys for this session (optional, can be implemented later)
      fetch(`/aetheronepysocial/key?session_id=${session.id}`)
        .then(res => res.json())
        .then(data => {
          this.keys = (data.keys || [])
        })
        .catch(() => { this.keys = [] })
    },
    closeModal() {
      this.showModal = false
      this.selectedSession = null
      this.shareMode = 'new'
      this.selectedKey = ''
      this.keys = []
      this.timeline = []
      this.shareComplete = false
      if (this.autoCloseTimeout) {
        clearTimeout(this.autoCloseTimeout)
        this.autoCloseTimeout = null
      }
    },
    addTimeline(text, type = 'info') {
      this.timeline.push({ text, type })
      console.log(`[${type.toUpperCase()}] ${text}`)
    },
    submitShare() {
      this.timeline = []
      this.shareComplete = false
      this.shareLoading = true
      if (this.shareMode === 'new') {
        this.addTimeline('Creating new key...')
        fetch('/aetheronepysocial/key', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ local_session_id: this.selectedSession.id })
        })
          .then(res => res.json())
          .then(data => {
            if ((data.status === 'success' || data.status === 'exists') && data.local && data.local.key) {
              const key = data.local.key
              if (data.status === 'exists') {
                this.addTimeline('Key already exists for this session. Using existing key: ' + key, 'info')
              } else {
                this.addTimeline('Key created: ' + key, 'success')
              }
              this.addTimeline('Fetching user info...')
              fetch('/aetheronepysocial/user')
                .then(res => res.json())
                .then(userData => {
                  const server_user_id = userData.server_user_id
                  this.addTimeline('User info loaded (server_user_id: ' + server_user_id + ')', 'success')
                  const machine_id = String(window.navigator.userAgent || 'browser')
                  this.addTimeline('Sharing analysis to server...')
                  fetch('/aetheronepysocial/analysis', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                      session_id: this.selectedSession.id,
                      server_user_id,
                      key,
                      machine_id
                    })
                  })
                    .then(res => res.json())
                    .then(analysisData => {
                      console.log('analysisData', analysisData)
                      console.log('analysisData.status:', analysisData.status)
                      if (analysisData.status && analysisData.status.toLowerCase() === 'success') {
                        this.addTimeline(analysisData.message || 'Analysis shared successfully!', 'success')
                        this.shareComplete = true
                      } else {
                        this.addTimeline('Failed to share analysis: ' + (analysisData.message || analysisData.error || 'Unknown error'), 'error')
                        this.shareComplete = true
                      }
                      this.shareLoading = false
                    })
                    .catch(() => {
                      this.addTimeline('Failed to share analysis due to network error.', 'error')
                      this.shareComplete = true
                      this.shareLoading = false
                    })
                })
                .catch(() => {
                  this.addTimeline('Failed to get user info for sharing analysis.', 'error')
                  this.shareComplete = true
                  this.shareLoading = false
                })
            } else {
              this.addTimeline('Failed to create key: ' + (data.message || 'Unknown error'), 'error')
              this.shareComplete = true
              this.shareLoading = false
            }
          })
          .catch(() => {
            this.addTimeline('Failed to create key due to network error.', 'error')
            this.shareComplete = true
            this.shareLoading = false
          })
      } else {
        this.addTimeline('Fetching user info...')
        fetch('/aetheronepysocial/user')
          .then(res => res.json())
          .then(userData => {
            const server_user_id = userData.server_user_id
            this.addTimeline('User info loaded (server_user_id: ' + server_user_id + ')', 'success')
            const machine_id = String(window.navigator.userAgent || 'browser')
            this.addTimeline('Sharing analysis to server...')
            fetch('/aetheronepysocial/analysis', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                session_id: this.selectedSession.id,
                server_user_id,
                key: this.selectedKey,
                machine_id
              })
            })
              .then(res => res.json())
              .then(analysisData => {
                console.log('analysisData', analysisData)
                console.log('analysisData.status:', analysisData.status)
                if (analysisData.status && analysisData.status.toLowerCase() === 'success') {
                  this.addTimeline(analysisData.message || 'Analysis shared successfully!', 'success')
                  this.shareComplete = true
                } else {
                  this.addTimeline('Failed to share analysis: ' + (analysisData.message || analysisData.error || 'Unknown error'), 'error')
                  this.shareComplete = true
                }
                this.shareLoading = false
              })
              .catch(() => {
                this.addTimeline('Failed to share analysis due to network error.', 'error')
                this.shareComplete = true
                this.shareLoading = false
              })
          })
          .catch(() => {
            this.addTimeline('Failed to get user info for sharing analysis.', 'error')
            this.shareComplete = true
            this.shareLoading = false
          })
      }
    },
    goToAnalysis() {
      this.closeModal();
      this.$router.push('/analysis');
    }
  }
}
</script>

<style scoped>
.sessions-view {
  max-width: 600px;
  margin: 32px auto;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
  padding: 24px;
}
h1 {
  margin-bottom: 24px;
}
.error {
  color: #d93025;
  font-weight: bold;
}
ul {
  list-style: none;
  padding: 0;
}
li {
  margin-bottom: 16px;
}
hr {
  border: none;
  border-top: 1px solid #eee;
  margin: 12px 0;
}
.session-item {
  display: flex;
  flex-direction: column;
}
.session-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.share-btn {
  background: #7e57c2;
  color: #fff;
  border: none;
  border-radius: 4px;
  padding: 8px 16px;
  cursor: pointer;
  font-size: 1em;
  transition: background 0.2s;
}
.share-btn:hover {
  background: #5e35b1;
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
.modal-content {
  margin-bottom: 24px;
}
.modal-actions {
  display: flex;
  gap: 16px;
  justify-content: flex-end;
}
.existing-key-select {
  margin-top: 12px;
}
.timeline {
  margin: 18px 0 12px 0;
  padding-left: 0;
  border-left: 3px solid #b39ddb;
}
.timeline-item {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
  font-size: 0.98em;
  color: #444;
}
.timeline-item.success .timeline-dot {
  background: #43a047;
}
.timeline-item.error .timeline-dot {
  background: #d93025;
}
.timeline-item.info .timeline-dot {
  background: #b39ddb;
}
.timeline-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  margin-right: 10px;
  background: #b39ddb;
  display: inline-block;
}
.timeline-msg {
  flex: 1;
}
.loading-indicator {
  text-align: center;
  color: #7e57c2;
  font-weight: bold;
  margin-bottom: 12px;
}
.go-analysis-btn {
  display: inline-block;
  margin-left: 12px;
  padding: 8px 16px;
  background: #7e57c2;
  color: #fff;
  border-radius: 4px;
  text-decoration: none;
  font-weight: bold;
  transition: background 0.2s;
}
.go-analysis-btn:hover {
  background: #5e35b1;
}
</style> 