import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { loginAPI, getAuthTokenAPI, setAuthToken } from '@/services/metaApi'
import { extractUserFromToken, isValidToken } from '@/utils/jwt'

export const useAuthStore = defineStore('auth', () => {
  // 상태
  const isAuthenticated = ref(false)
  const user = ref(null)
  const token = ref(null)
  const loading = ref(false)
  const error = ref(null)

  // 계산된 속성
  const isLoggedIn = computed(() => isAuthenticated.value && token.value)

  // 메서드
  const login = async (username, password) => {
    try {
      loading.value = true
      error.value = null

      // 실제 로그인 API 호출
      const loginData = await loginAPI(username, password)
      
      // 상태 업데이트
      token.value = loginData.data.accessToken
      isAuthenticated.value = true
      
      // JWT 토큰에서 사용자 정보 추출
      const userInfo = extractUserFromToken(loginData.data.accessToken)
      user.value = userInfo
      
      // 로컬 스토리지에 저장
      localStorage.setItem('authToken', loginData.data.accessToken)
      localStorage.setItem('refreshToken', loginData.data.refreshToken)
      localStorage.setItem('username', username)
      
      // 로그인 성공 후 대화 목록 로드
      try {
        const { useConversationStore } = await import('@/stores/conversation')
        const conversationStore = useConversationStore()
        await conversationStore.loadConversations()
      } catch (error) {
        console.error('Failed to load conversations after login:', error)
      }
      
      return loginData
    } catch (err) {
      error.value = err.message || '로그인에 실패했습니다.'
      throw err
    } finally {
      loading.value = false
    }
  }

  const logout = () => {
    // 상태 초기화
    isAuthenticated.value = false
    user.value = null
    token.value = null
    error.value = null
    
    // API 서비스에서 토큰 제거
    setAuthToken(null)
    
    // 로컬 스토리지에서 제거
    localStorage.removeItem('authToken')
    localStorage.removeItem('refreshToken')
    localStorage.removeItem('username')
    
    // 대화 목록 초기화
    try {
      const { useConversationStore } = require('@/stores/conversation')
      const conversationStore = useConversationStore()
      conversationStore.conversations = []
      conversationStore.currentConversationId = null
    } catch (error) {
      console.error('Failed to clear conversations on logout:', error)
    }
  }

  const initializeAuth = () => {
    // 로컬 스토리지에서 토큰 복원
    const savedToken = localStorage.getItem('authToken')
    
    if (savedToken && isValidToken(savedToken)) {
      // 토큰이 유효하면 사용자 정보 추출
      const userInfo = extractUserFromToken(savedToken)
      
      if (userInfo) {
        token.value = savedToken
        user.value = userInfo
        isAuthenticated.value = true
        setAuthToken(savedToken)
      } else {
        // 토큰에서 사용자 정보를 추출할 수 없으면 로그아웃 처리
        logout()
      }
    } else if (savedToken) {
      // 토큰이 만료되었거나 유효하지 않으면 로그아웃 처리
      logout()
    }
  }

  const clearError = () => {
    error.value = null
  }

  return {
    // 상태
    isAuthenticated,
    user,
    token,
    loading,
    error,
    
    // 계산된 속성
    isLoggedIn,
    
    // 메서드
    login,
    logout,
    initializeAuth,
    clearError
  }
})
