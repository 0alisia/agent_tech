import Vue from 'vue'
import Router from 'vue-router'
import Ask from '../views/Ask.vue'
import Dashboard from '../views/Dashboard.vue'
import Login from '../views/Login.vue'
import Drones from '../views/Drones.vue'
import Profile from '../views/Profile.vue'
import Register from '../views/Register.vue'
import Forum from '../views/Forum.vue'
import Weather from '../views/Weather.vue'
import TrainingAgent from '../views/TrainingAgent.vue'

Vue.use(Router)

const router = new Router({
  routes: [
    { path: '/', redirect: '/dashboard' },
    { path: '/login', component: Login },
    { path: '/register', component: Register },
    { path: '/dashboard', component: Dashboard },
    { path: '/profile', component: Profile },
    { path: '/drones', component: Drones },
    { path: '/training-agent', component: TrainingAgent },
    { path: '/ask', component: Ask },
    { path: '/weather', component: Weather },
    { path: '/forum', component: Forum },
  ]
})

router.beforeEach((to, from, next) => {
  if (!['/login', '/register'].includes(to.path) && !localStorage.getItem('token')) {
    next('/login')
  } else {
    next()
  }
})

export default router
