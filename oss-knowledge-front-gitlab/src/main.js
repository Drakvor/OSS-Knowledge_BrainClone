import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router'
import App from './App.vue'
import './styles/main.css'
import { useUIStore } from './stores/ui'
import { useAuthStore } from './stores/auth'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)

// UI 스토어 초기화
const uiStore = useUIStore()
uiStore.initMode()
uiStore.initSidebar()

// 인증 스토어 초기화
const authStore = useAuthStore()
authStore.initializeAuth()

app.mount('#app')