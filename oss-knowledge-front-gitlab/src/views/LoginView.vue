<template>
  <div class="h-screen relative overflow-hidden">
    <!-- Background Image -->
    <div class="absolute inset-0">
      <img 
        :src="backgroundImage" 
        alt="Background" 
        class="absolute inset-0 w-full h-full object-cover"
      />
    </div>

    <!-- Main Content -->
    <div class="relative z-10 h-screen flex items-center justify-center p-4 sm:p-6 lg:p-8">
      <div class="w-full max-w-6xl">
        <!-- Book Layout Container -->
        <div class="bg-white rounded-3xl shadow-xl border border-gray-200 overflow-hidden max-h-[calc(100vh-2rem)] flex relative">
          <!-- Book Center Line -->
          <div class="absolute left-1/2 top-4 bottom-4 w-px bg-gradient-to-b from-gray-200 via-gray-300 to-gray-200 transform -translate-x-1/2 z-10 shadow-sm"></div>
          <!-- Left Page - Logo and Welcome -->
          <div class="flex-1 bg-white flex flex-col items-center justify-center p-8 space-y-6">
            <div class="text-center space-y-4">
              <img 
                :src="logoImage" 
                alt="BrainClone Logo" 
                class="h-80 w-auto object-contain mx-auto"
              />
              <div>
                <p class="text-gray-600 text-sm">
                  인간과 AI가 협력하는<br>
                  지능형 지식 관리 시스템에 오신 것을 환영합니다
                </p>
              </div>
            </div>
          </div>

          <!-- Right Page - Login Form -->
          <div class="flex-1 flex flex-col justify-center p-8">
            <div class="max-w-sm mx-auto w-full">
              <div class="text-center mb-8">
                <h2 class="text-2xl font-bold text-gray-900 mb-2">로그인</h2>
                <p class="text-gray-600 text-sm">계정에 로그인하여 시작하세요</p>
              </div>

              <!-- Login Form -->
              <form class="space-y-6" @submit.prevent="handleLogin">
            <!-- Username Input -->
            <div class="space-y-2">
              <label for="username" class="block text-sm font-medium text-gray-700">
                사용자명
              </label>
              <div class="relative">
                <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <svg class="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                  </svg>
                </div>
                <input
                  id="username"
                  v-model="loginForm.username"
                  name="username"
                  type="text"
                  autocomplete="username"
                  required
                  class="block w-full pl-10 pr-3 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent transition-all duration-200 bg-white"
                  placeholder="사용자명을 입력하세요"
                />
              </div>
            </div>

            <!-- Password Input -->
            <div class="space-y-2">
              <label for="password" class="block text-sm font-medium text-gray-700">
                비밀번호
              </label>
              <div class="relative">
                <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <svg class="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                  </svg>
                </div>
                <input
                  id="password"
                  v-model="loginForm.password"
                  name="password"
                  type="password"
                  autocomplete="current-password"
                  required
                  class="block w-full pl-10 pr-3 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent transition-all duration-200 bg-white"
                  placeholder="비밀번호를 입력하세요"
                />
              </div>
            </div>

            <!-- Error Message -->
            <div v-if="authStore.error" class="rounded-xl bg-red-50 border border-red-200 p-4 animate-fadeIn">
              <div class="flex">
                <div class="flex-shrink-0">
                  <svg class="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
                  </svg>
                </div>
                <div class="ml-3">
                  <h3 class="text-sm font-medium text-red-800">
                    로그인 실패
                  </h3>
                  <div class="mt-2 text-sm text-red-700">
                    {{ authStore.error }}
                  </div>
                </div>
              </div>
            </div>

            <!-- Login Button -->
            <div>
              <button
                type="submit"
                :disabled="authStore.loading"
                class="group relative w-full flex justify-center py-3 px-4 border border-transparent text-sm font-medium rounded-xl text-white bg-gradient-to-r from-teal-600 to-emerald-600 hover:from-teal-700 hover:to-emerald-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-teal-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 transform hover:scale-[1.02] shadow-lg hover:shadow-xl"
              >
                <span v-if="authStore.loading" class="absolute left-0 inset-y-0 flex items-center pl-3">
                  <svg class="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                </span>
                <span class="flex items-center">
                  <svg v-if="!authStore.loading" class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1" />
                  </svg>
                  {{ authStore.loading ? '로그인 중...' : '로그인' }}
                </span>
              </button>
            </div>

            <!-- Test Account Info -->
            <div class="text-center space-y-2">
              <div class="bg-gradient-to-r from-teal-50 to-emerald-50 rounded-xl p-4 border border-teal-200">
                <p class="text-sm font-medium text-gray-700 mb-2">테스트 계정</p>
                <div class="space-y-1">
                  <p class="text-xs text-gray-600">
                    사용자명: <span class="font-mono bg-teal-100 px-2 py-1 rounded text-teal-800">oss</span>
                  </p>
                  <p class="text-xs text-gray-600">
                    또는: <span class="font-mono bg-emerald-100 px-2 py-1 rounded text-emerald-800">test-user</span>
                  </p>
                  <p class="text-xs text-gray-600">
                    비밀번호: <span class="font-mono bg-blue-100 px-2 py-1 rounded text-blue-800">changeme</span>
                  </p>
                </div>
              </div>
            </div>
              </form>
            </div>
          </div>
        </div>

        <!-- Footer -->
        <div class="text-center mt-8">
          <p class="text-gray-600 text-sm">
            © 2025 BrainClone. All rights reserved.
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import logoImage from '@/images/brainclone_logo_4K_nobackground.png'
import backgroundImage from '@/images/brainclone_background_image_4K.png'

const router = useRouter()
const authStore = useAuthStore()

const loginForm = reactive({
  username: '',
  password: ''
})

const handleLogin = async () => {
  try {
    await authStore.login(loginForm.username, loginForm.password)
    router.push('/')
  } catch (err) {
    console.error('Login error:', err)
  }
}
</script>

<style scoped>
@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.animate-fadeIn {
  animation: fadeIn 0.3s ease-out;
}

/* Glass morphism effect */
.backdrop-blur-sm {
  backdrop-filter: blur(8px);
}

/* Custom gradient animations */
@keyframes gradientShift {
  0% {
    background-position: 0% 50%;
  }
  50% {
    background-position: 100% 50%;
  }
  100% {
    background-position: 0% 50%;
  }
}

.bg-gradient-to-r {
  background-size: 200% 200%;
  animation: gradientShift 3s ease infinite;
}

/* Enhanced focus states */
input:focus {
  transform: translateY(-1px);
  box-shadow: 0 10px 25px -5px rgba(20, 184, 166, 0.1), 0 10px 10px -5px rgba(20, 184, 166, 0.04);
}

/* Button hover effects */
button:hover:not(:disabled) {
  transform: translateY(-2px);
}

/* Logo glow effect */
.logo-glow {
  filter: drop-shadow(0 0 20px rgba(20, 184, 166, 0.3));
}

/* Responsive adjustments */
@media (max-width: 1024px) {
  .max-w-6xl {
    max-width: 100%;
  }
  
  .flex {
    flex-direction: column;
  }
  
  .flex-1 {
    flex: none;
  }
  
  /* Hide center line on mobile */
  .absolute.left-1\/2 {
    display: none;
  }
  
  .bg-gradient-to-br {
    background: linear-gradient(135deg, #f0fdfa 0%, #ecfeff 100%);
  }
}

@media (max-width: 640px) {
  .h-screen {
    padding: 1rem;
  }
  
  .rounded-3xl {
    border-radius: 1.5rem;
  }
  
  .p-8 {
    padding: 1.5rem;
  }
  
  .h-48 {
    height: 8rem;
  }
}
</style>
