<template>
  <div class="analysis-list-view">
    <h1>Analyses for Key: {{ key }}</h1>
    <div v-if="loading">Loading analyses...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div v-if="sessions.length === 0">No analyses found for this key.</div>
      <div v-else>
        <div v-for="session in sessions" :key="session.id" class="session-block">
          <h2>Session: {{ session.description }} ({{ session.created }})</h2>
          <div>
            <strong>Case:</strong> {{ session.case?.name }}<br>
            <strong>Intention:</strong> {{ session.intention }}
          </div>
          <div v-for="analysis in session.analyses" :key="analysis.id" class="analysis-block">
            <h3>Analysis ({{ analysis.created }})</h3>
            <div>
              <strong>Catalog:</strong> {{ analysis.catalog?.name }}<br>
              <strong>Target GV:</strong> {{ analysis.target_gv }}
            </div>
            <table v-if="analysis.rate_analyses && analysis.rate_analyses.length">
              <thead>
                <tr>
                  <th>Signature</th>
                  <th>Energetic Value</th>
                  <th>GV</th>
                  <th>Note</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="rate in analysis.rate_analyses" :key="rate.id">
                  <td>{{ rate.signature }}</td>
                  <td>{{ rate.energetic_value }}</td>
                  <td>{{ rate.gv }}</td>
                  <td>{{ rate.note }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'AnalysisListView',
  data() {
    return {
      key: this.$route.params.key,
      sessions: [],
      loading: true,
      error: ''
    }
  },
  mounted() {
    this.fetchAnalyses()
  },
  watch: {
    '$route.params.key'(newKey) {
      this.key = newKey
      this.fetchAnalyses()
    }
  },
  methods: {
    fetchAnalyses() {
      this.loading = true
      this.error = ''
      fetch(`/aetheronepysocialplugin/analysis_for_key/${this.key}`)
        .then(res => res.json())
        .then(data => {
          if (data.status === 'success' && Array.isArray(data.result.data)) {
            this.sessions = data.result.data
          } else {
            this.sessions = []
            this.error = data.message || 'No analyses found.'
          }
          this.loading = false
        })
        .catch(() => {
          this.error = 'Failed to load analyses.'
          this.loading = false
        })
    }
  }
}
</script>

<style scoped>
.analysis-list-view {
  max-width: 900px;
  margin: 32px auto;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
  padding: 24px;
}
.session-block {
  margin-bottom: 32px;
  border-bottom: 1px solid #eee;
  padding-bottom: 18px;
}
.analysis-block {
  margin-top: 18px;
  margin-bottom: 18px;
  background: #f5f5f5;
  border-radius: 4px;
  padding: 12px;
}
table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 10px;
}
th, td {
  border: 1px solid #ddd;
  padding: 6px 10px;
  text-align: left;
}
th {
  background: #eee;
}
.error {
  color: #d93025;
  font-weight: bold;
  margin: 12px 0;
}
</style> 