<template>
  <div class="analysis-list-view">
    <h1>Analyses for Key: {{ key }}</h1>
    <div v-if="loading">Loading analyses...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div v-if="analyses.length === 0">No analyses found for this key.</div>
      <ul v-else class="analysis-list">
        <li v-for="analysis in analyses" :key="analysis.id" class="analysis-item">
          <pre>{{ analysis }}</pre>
        </li>
      </ul>
    </div>
  </div>
</template>

<script>
export default {
  name: 'AnalysisListView',
  data() {
    return {
      key: this.$route.params.key,
      analyses: [],
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
      fetch(`/aetheronepysocial/send_key/${this.key}`)
        .then(res => res.json())
        .then(data => {
          // Assume data.analyses is an array, or just data if it's a list
          this.analyses = data.analyses || data || []
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
  max-width: 700px;
  margin: 32px auto;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
  padding: 24px;
}
.analysis-list {
  list-style: none;
  padding: 0;
}
.analysis-item {
  margin-bottom: 18px;
  background: #f5f5f5;
  border-radius: 4px;
  padding: 12px;
  font-size: 0.97em;
}
.error {
  color: #d93025;
  font-weight: bold;
  margin: 12px 0;
}
</style> 