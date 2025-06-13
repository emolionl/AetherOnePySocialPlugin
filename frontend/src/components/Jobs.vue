<template>
  <div class="jobs-setup">
    <h2>Jobs</h2>
    <div v-if="loading">Loading...</div>
    <div v-else>
      <form v-if="editId" @submit.prevent="saveEdit">
        <label>Edit Job Name:<br>
          <input v-model="editName" required />
        </label><br>
        <label>Edit Description:<br>
          <input v-model="editDescription" />
        </label><br>
        <button type="submit">Save</button>
        <button type="button" @click="cancelEdit">Cancel</button>
      </form>
      <div v-else>
        <form @submit.prevent="addJob">
          <label>Job Name:<br>
            <input v-model="name" required placeholder="Job name" />
          </label><br>
          <label>Description:<br>
            <input v-model="description" placeholder="Description (optional)" />
          </label><br>
          <button type="submit">Add Job</button>
        </form>
      </div>
      <h3 style="margin-top:2em;">All Jobs</h3>
      <table class="jobs-table">
        <thead>
          <tr><th>Name</th><th>Description</th><th>Actions</th></tr>
        </thead>
        <tbody>
          <tr v-for="j in jobs" :key="j.id">
            <td>{{ j.name }}</td>
            <td>{{ j.description }}</td>
            <td>
              <button @click="startEdit(j)">Edit</button>
              <button @click="deleteJob(j.id)">Delete</button>
            </td>
          </tr>
        </tbody>
      </table>
      <div v-if="error" class="error">{{ error }}</div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'Jobs',
  data() {
    return {
      jobs: [],
      loading: false,
      name: '',
      description: '',
      error: '',
      editId: null,
      editName: '',
      editDescription: ''
    }
  },
  mounted() {
    this.fetchJobs()
  },
  methods: {
    fetchJobs() {
      // Placeholder: use static data for now
      this.loading = false
      this.jobs = [
        { id: 1, name: 'Example Job', description: 'Demo job' }
      ]
    },
    addJob() {
      if (!this.name) return
      this.jobs.push({
        id: Date.now(),
        name: this.name,
        description: this.description
      })
      this.name = ''
      this.description = ''
    },
    startEdit(job) {
      this.editId = job.id
      this.editName = job.name
      this.editDescription = job.description
    },
    cancelEdit() {
      this.editId = null
      this.editName = ''
      this.editDescription = ''
    },
    saveEdit() {
      const idx = this.jobs.findIndex(j => j.id === this.editId)
      if (idx !== -1) {
        this.jobs[idx].name = this.editName
        this.jobs[idx].description = this.editDescription
      }
      this.cancelEdit()
    },
    deleteJob(id) {
      if (!confirm('Are you sure you want to delete this job?')) return
      this.jobs = this.jobs.filter(j => j.id !== id)
    }
  }
}
</script>

<style scoped>
.jobs-setup {
  max-width: 600px;
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
.jobs-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 1em;
}
.jobs-table th, .jobs-table td {
  border: 1px solid #eee;
  padding: 0.5em 1em;
}
.jobs-table th {
  background: #f8f9fa;
}
.error {
  color: #d93025;
  margin-top: 1em;
}
</style> 