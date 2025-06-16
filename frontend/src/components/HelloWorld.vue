<template>
  <div class="home-view">
    <div class="instructions">
      <h2>Welcome to AetherOnePy Social!</h2>
      <ul>
        <li>Use the navigation menu to access sessions, share analyses, and manage your keys.</li>
        <li>To get started, select a server and log in or register.</li>
        <li>After logging in, you can view and share your analysis sessions with others.</li>
        <li>Visit the Analysis page to see all your shared analyses by key</li>
      </ul>
    </div>
    <div class="video-container">
      <iframe width="560" height="315" src="https://www.youtube.com/embed/16EuKQ7Nku0" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe>
    </div>
  </div>
</template>

<script>
export default {
  name: 'HelloWorld'
}
</script>

<style scoped>
.home-view {
  max-width: 700px;
  margin: 32px auto;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
  padding: 24px;
  text-align: center;
}
.instructions {
  margin-bottom: 24px;
  text-align: left;
}
.instructions h2 {
  margin-bottom: 12px;
  color: #7e57c2;
}
.instructions ul {
  padding-left: 20px;
}
.video-container {
  display: flex;
  justify-content: center;
}
iframe {
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}
</style>
