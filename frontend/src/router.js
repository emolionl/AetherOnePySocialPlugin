import { createRouter, createWebHistory } from 'vue-router'
import HelloWorld from './components/HelloWorld.vue'
import ServerSetup from './components/ServerSetup.vue'
import AuthForm from './components/Auth.vue'
import SessionsView from './views/Sessions.vue'
import AnalysisView from './views/Analysis.vue'
import AnalysisListView from './views/AnalysisList.vue'
import KeysView from './views/Keys.vue'

const routes = [
  { path: '/setup', component: ServerSetup },
  { path: '/servers', component: ServerSetup },
  { path: '/auth', component: AuthForm },
  { path: '/home', component: HelloWorld },
  { path: '/sessions', component: SessionsView },
  { path: '/analysis', component: AnalysisView },
  { path: '/analysis/:key', component: AnalysisListView },
  { path: '/keys', component: KeysView },
  { path: '/', redirect: '/home' }
]

const router = createRouter({
  history: createWebHistory('/aetheronepysocialplugin/'),
  routes
})

router.beforeEach((to, from, next) => {
  const selectedServerId = localStorage.getItem('selectedServerId')
  const userTokens = JSON.parse(localStorage.getItem('userTokens') || '{}')
  const loggedIn = selectedServerId && userTokens[selectedServerId]
  if (!selectedServerId && to.path !== '/setup' && to.path !== '/servers') {
    next('/setup')
  } else if (selectedServerId && !loggedIn && to.path !== '/auth' && to.path !== '/setup' && to.path !== '/servers') {
    next('/auth')
  } else if (selectedServerId && loggedIn && to.path === '/auth') {
    next('/home')
  } else if (selectedServerId && to.path === '/setup') {
    next('/home')
  } else {
    next()
  }
})

export default router 