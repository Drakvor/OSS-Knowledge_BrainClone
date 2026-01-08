<template>
  <header class="border-b shadow-sm header" style="border-color: var(--color-border-light); background-color: var(--color-bg-secondary)">
    <div class="px-6 py-4 flex items-center justify-between">
      <div class="flex items-center gap-4">
        <!-- 사이드바 토글 버튼 (모바일에서만 표시) -->
        <button
          @click="uiStore.toggleSidebar()"
          class="p-2 rounded-lg transition-all duration-200 md:hidden"
          style="color: var(--color-gray-600)"
          onmouseover="this.style.backgroundColor='var(--color-gray-100)'"
          onmouseout="this.style.backgroundColor='transparent'"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>

        <!-- 로고와 제목 -->
        <div class="flex items-center gap-3">
          <div class="flex items-center gap-2">
            <div class="w-8 h-8 rounded-lg flex items-center justify-center" style="background: linear-gradient(135deg, var(--color-primary-500), var(--color-primary-600))">
              <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <span class="font-semibold text-lg" style="color: var(--color-gray-900)">Brain Clone</span>
          </div>
          
          <!-- 모드 토글 (데스크톱에서만 표시) -->
          <div class="hidden md:block">
            <ModeToggle />
          </div>
        </div>
      </div>

      <div class="flex items-center gap-3">
        <!-- 사용자 메뉴 -->
        <div class="relative">
          <button
            @click="isUserMenuOpen = !isUserMenuOpen"
            class="flex items-center gap-2 p-2 rounded-lg transition-all duration-200"
            style="color: var(--color-gray-600)"
            onmouseover="this.style.backgroundColor='var(--color-gray-100)'"
            onmouseout="this.style.backgroundColor='transparent'"
          >
            <div class="w-8 h-8 rounded-full flex items-center justify-center font-medium text-sm" style="background-color: var(--color-gray-800); color: white">
              {{ getUserInitials }}
            </div>
          </button>

          <!-- 사용자 드롭다운 메뉴 -->
          <Transition
            enter-active-class="transition-all duration-200 ease-out"
            enter-from-class="opacity-0 scale-95 translate-y-1"
            enter-to-class="opacity-100 scale-100 translate-y-0"
            leave-active-class="transition-all duration-150 ease-in"
            leave-from-class="opacity-100 scale-100 translate-y-0"
            leave-to-class="opacity-0 scale-95 translate-y-1"
          >
            <div
              v-if="isUserMenuOpen"
              class="absolute right-0 top-full mt-2 w-56 rounded-xl shadow-lg py-2 z-50"
              style="background-color: var(--color-bg-primary); border: 1px solid var(--color-border-light)"
            >
              <div class="px-4 py-3" style="border-bottom: 1px solid var(--color-border-light)">
                <p class="text-sm font-medium" style="color: var(--color-gray-900)">{{ getUserDisplayName }}</p>
                <p class="text-xs" style="color: var(--color-gray-500)">{{ getUserRole }}</p>
              </div>

              <button @click="openSettingsModal" class="w-full px-4 py-2 text-left text-sm transition-colors duration-200 flex items-center gap-2" style="color: var(--color-gray-700)" onmouseover="this.style.backgroundColor='var(--color-gray-50)'" onmouseout="this.style.backgroundColor='transparent'">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
                설정
              </button>
              <button class="w-full px-4 py-2 text-left text-sm transition-colors duration-200 flex items-center gap-2" style="color: var(--color-gray-700)" onmouseover="this.style.backgroundColor='var(--color-gray-50)'" onmouseout="this.style.backgroundColor='transparent'">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                도움말
              </button>
              <hr class="my-1" style="border-color: var(--color-border-light)">
              <button @click="handleLogout" class="w-full px-4 py-2 text-left text-sm transition-colors duration-200 flex items-center gap-2" style="color: var(--color-gray-700)" onmouseover="this.style.backgroundColor='var(--color-gray-50)'" onmouseout="this.style.backgroundColor='transparent'">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                </svg>
                로그아웃
              </button>
            </div>
          </Transition>
        </div>
      </div>
    </div>

    <!-- 오버레이 (드롭다운이 열려있을 때) -->
    <div
      v-if="isUserMenuOpen"
      @click="closeAllDropdowns"
      class="fixed inset-0 z-40"
    ></div>

    <!-- 설정 모달 -->
    <Transition
      enter-active-class="transition-all duration-200 ease-out"
      enter-from-class="opacity-0"
      enter-to-class="opacity-100"
      leave-active-class="transition-all duration-150 ease-in"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div
        v-if="isSettingsModalOpen"
        class="fixed inset-0 z-50 flex items-center justify-center p-4"
        style="background-color: rgba(0, 0, 0, 0.5)"
        @click="closeSettingsModal"
      >
        <div
          class="w-full max-w-4xl max-h-[90vh] overflow-y-auto rounded-xl shadow-xl"
          style="background-color: var(--color-bg-primary); border: 1px solid var(--color-border-light)"
          @click.stop
        >
          <div class="p-6">
            <div class="flex items-center justify-between mb-6">
              <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-lg flex items-center justify-center" style="background: linear-gradient(135deg, var(--color-primary-500), var(--color-primary-600))">
                  <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                </div>
                <div>
                  <h2 class="text-xl font-semibold" style="color: var(--color-gray-900)">설정</h2>
                  <p class="text-sm" style="color: var(--color-gray-500)">계정 및 애플리케이션 설정을 관리하세요</p>
                </div>
              </div>
              <button
                @click="closeSettingsModal"
                class="p-2 rounded-lg transition-all duration-200"
                style="color: var(--color-gray-500)"
                onmouseover="this.style.backgroundColor='var(--color-gray-100)'"
                onmouseout="this.style.backgroundColor='transparent'"
              >
                <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <!-- 설정 탭 -->
            <div class="flex space-x-1 mb-6 p-1 rounded-lg" style="background-color: var(--color-bg-secondary)">
              <button
                @click="activeSettingsTab = 'general'"
                class="px-4 py-2 text-sm font-medium rounded-md transition-all duration-200"
                :style="activeSettingsTab === 'general' ? 'background-color: var(--color-bg-primary); color: var(--color-primary-600)' : 'color: var(--color-gray-600)'"
              >
                일반
              </button>
              <button
                @click="activeSettingsTab = 'mem0'"
                class="px-4 py-2 text-sm font-medium rounded-md transition-all duration-200"
                :style="activeSettingsTab === 'mem0' ? 'background-color: var(--color-bg-primary); color: var(--color-primary-600)' : 'color: var(--color-gray-600)'"
              >
                개인 메모리 (MEM0)
              </button>
              <button
                @click="activeSettingsTab = 'privacy'"
                class="px-4 py-2 text-sm font-medium rounded-md transition-all duration-200"
                :style="activeSettingsTab === 'privacy' ? 'background-color: var(--color-bg-primary); color: var(--color-primary-600)' : 'color: var(--color-gray-600)'"
              >
                개인정보
              </button>
            </div>

            <!-- 일반 설정 -->
            <div v-if="activeSettingsTab === 'general'" class="space-y-6">
              <div class="p-4 rounded-lg border" style="background-color: var(--color-bg-secondary); border-color: var(--color-border-light)">
                <h3 class="font-medium mb-4" style="color: var(--color-gray-900)">일반 설정</h3>
                <div class="space-y-4">
                  <div>
                    <label class="block text-sm font-medium mb-2" style="color: var(--color-gray-700)">언어</label>
                    <select class="w-full px-3 py-2 text-sm rounded-lg border" style="background-color: var(--color-bg-primary); border-color: var(--color-border-light); color: var(--color-gray-900)">
                      <option value="ko">한국어</option>
                      <option value="en">English</option>
                    </select>
                  </div>
                  <div>
                    <label class="block text-sm font-medium mb-2" style="color: var(--color-gray-700)">테마</label>
                    <select class="w-full px-3 py-2 text-sm rounded-lg border" style="background-color: var(--color-bg-primary); border-color: var(--color-border-light); color: var(--color-gray-900)">
                      <option value="light">라이트</option>
                      <option value="dark">다크</option>
                      <option value="auto">시스템 설정</option>
                    </select>
                  </div>
                </div>
              </div>
            </div>

            <!-- MEM0 설정 -->
            <div v-if="activeSettingsTab === 'mem0'" class="space-y-6">
              <!-- MEM0 상태 -->
              <div class="p-4 rounded-lg border" style="background-color: var(--color-bg-secondary); border-color: var(--color-border-light)">
                <div class="flex items-center justify-between mb-4">
                  <h3 class="font-medium" style="color: var(--color-gray-900)">MEM0 개인 메모리</h3>
                  <span class="px-3 py-1 text-sm rounded-full" :style="mem0Enabled ? 'background-color: var(--color-green-100); color: var(--color-green-800)' : 'background-color: var(--color-gray-100); color: var(--color-gray-600)'">
                    {{ mem0Enabled ? '활성화' : '비활성화' }}
                  </span>
                </div>
                <p class="text-sm mb-4" style="color: var(--color-gray-600)">
                  MEM0는 사용자의 검색 패턴과 선호도를 학습하여 개인화된 RAG 경험을 제공합니다. 최근 사용자의 검색 패턴에서 SOP 콜렉션을 빈번하게 사용하고 있음을 인지했습니다.
                </p>
                <div class="flex items-center justify-between">
                  <div>
                    <p class="font-medium text-sm" style="color: var(--color-gray-900)">MEM0 활성화</p>
                    <p class="text-xs" style="color: var(--color-gray-500)">개인화된 메모리 기능을 사용합니다</p>
                  </div>
                  <label class="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      v-model="mem0Enabled"
                      class="sr-only peer"
                    >
                    <div class="w-11 h-6 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600 bg-gray-200"></div>
                  </label>
                </div>
              </div>

              <!-- 메모리 통계 -->
              <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div class="p-4 rounded-lg border text-center" style="background-color: var(--color-bg-secondary); border-color: var(--color-border-light)">
                  <div class="text-2xl font-bold mb-1" style="color: var(--color-primary-600)">{{ totalMemoryCount }}</div>
                  <div class="text-sm" style="color: var(--color-gray-600)">총 메모리</div>
                </div>
                <div class="p-4 rounded-lg border text-center" style="background-color: var(--color-bg-secondary); border-color: var(--color-border-light)">
                  <div class="text-2xl font-bold mb-1" style="color: var(--color-primary-600)">{{ preferenceCount }}</div>
                  <div class="text-sm" style="color: var(--color-gray-600)">선호도</div>
                </div>
                <div class="p-4 rounded-lg border text-center" style="background-color: var(--color-bg-secondary); border-color: var(--color-border-light)">
                  <div class="text-2xl font-bold mb-1" style="color: var(--color-primary-600)">{{ patternCount }}</div>
                  <div class="text-sm" style="color: var(--color-gray-600)">패턴</div>
                </div>
                <div class="p-4 rounded-lg border text-center" style="background-color: var(--color-bg-secondary); border-color: var(--color-border-light)">
                  <div class="text-2xl font-bold mb-1" style="color: var(--color-primary-600)">{{ contextCount }}</div>
                  <div class="text-sm" style="color: var(--color-gray-600)">컨텍스트</div>
                </div>
              </div>

              <!-- 최근 메모리 -->
              <div class="p-4 rounded-lg border" style="background-color: var(--color-bg-secondary); border-color: var(--color-border-light)">
                <h3 class="font-medium mb-4" style="color: var(--color-gray-900)">최근 메모리</h3>
                <div class="space-y-3">
                  <div v-for="memory in recentMemories" :key="memory.id" class="p-3 rounded-lg text-sm" style="background-color: var(--color-bg-primary); border: 1px solid var(--color-border-light)">
                    <div class="flex items-start justify-between">
                      <div class="flex-1">
                        <div class="flex items-center gap-2 mb-1">
                          <p class="font-medium" style="color: var(--color-gray-900)">{{ memory.title }}</p>
                          <span class="px-2 py-0.5 text-xs rounded-full" :style="`background-color: ${getMemoryTypeColor(memory.type)}; color: var(--color-gray-700)`">
                            {{ getMemoryTypeLabel(memory.type) }}
                          </span>
                        </div>
                        <p class="text-xs" style="color: var(--color-gray-500)">{{ memory.content }}</p>
                      </div>
                      <span class="text-xs ml-2" style="color: var(--color-gray-400)">{{ memory.timestamp }}</span>
                    </div>
                  </div>
                </div>
              </div>

              <!-- MEM0 설정 -->
              <div class="p-4 rounded-lg border" style="background-color: var(--color-bg-secondary); border-color: var(--color-border-light)">
                <h3 class="font-medium mb-4" style="color: var(--color-gray-900)">고급 설정</h3>
                <div class="space-y-4">
                  <div>
                    <label class="block text-sm font-medium mb-2" style="color: var(--color-gray-700)">메모리 보존 기간</label>
                    <select v-model="memoryRetentionDays" class="w-full px-3 py-2 text-sm rounded-lg border" style="background-color: var(--color-bg-primary); border-color: var(--color-border-light); color: var(--color-gray-900)">
                      <option value="7">7일</option>
                      <option value="30">30일</option>
                      <option value="90">90일</option>
                      <option value="365">1년</option>
                    </select>
                  </div>
                  <div class="flex items-center justify-between">
                    <div>
                      <p class="font-medium text-sm" style="color: var(--color-gray-900)">자동 메모리 생성</p>
                      <p class="text-xs" style="color: var(--color-gray-500)">대화 내용을 자동으로 메모리로 저장합니다</p>
                    </div>
                    <label class="relative inline-flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        v-model="autoMemoryGeneration"
                        class="sr-only peer"
                      >
                      <div class="w-11 h-6 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600 bg-gray-200"></div>
                    </label>
                  </div>
                </div>
              </div>

              <!-- 메모리 관리 -->
              <div class="p-4 rounded-lg border" style="background-color: var(--color-bg-secondary); border-color: var(--color-border-light)">
                <h3 class="font-medium mb-4" style="color: var(--color-gray-900)">메모리 관리</h3>
                <div class="flex gap-3">
                  <button
                    @click="addMockMemory"
                    class="px-4 py-2 text-sm rounded-lg transition-all duration-200 flex items-center gap-2"
                    style="background-color: var(--color-primary-500); color: white"
                    onmouseover="this.style.backgroundColor='var(--color-primary-600)'"
                    onmouseout="this.style.backgroundColor='var(--color-primary-500)'"
                  >
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
                    </svg>
                    새 메모리 추가
                  </button>
                  <button
                    @click="clearAllMemories"
                    class="px-4 py-2 text-sm rounded-lg transition-all duration-200 flex items-center gap-2"
                    style="color: var(--color-gray-700); border: 1px solid var(--color-border-light)"
                    onmouseover="this.style.backgroundColor='var(--color-gray-50)'"
                    onmouseout="this.style.backgroundColor='transparent'"
                  >
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                    모든 메모리 삭제
                  </button>
                </div>
              </div>
            </div>

            <!-- 개인정보 설정 -->
            <div v-if="activeSettingsTab === 'privacy'" class="space-y-6">
              <div class="p-4 rounded-lg border" style="background-color: var(--color-bg-secondary); border-color: var(--color-border-light)">
                <h3 class="font-medium mb-4" style="color: var(--color-gray-900)">개인정보 설정</h3>
                <div class="space-y-4">
                  <div class="flex items-center justify-between">
                    <div>
                      <p class="font-medium text-sm" style="color: var(--color-gray-900)">사용 통계 수집</p>
                      <p class="text-xs" style="color: var(--color-gray-500)">서비스 개선을 위한 익명 통계를 수집합니다</p>
                    </div>
                    <label class="relative inline-flex items-center cursor-pointer">
                      <input type="checkbox" class="sr-only peer" checked>
                      <div class="w-11 h-6 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600 bg-gray-200"></div>
                    </label>
                  </div>
                  <div class="flex items-center justify-between">
                    <div>
                      <p class="font-medium text-sm" style="color: var(--color-gray-900)">마케팅 이메일</p>
                      <p class="text-xs" style="color: var(--color-gray-500)">새로운 기능과 업데이트 소식을 받습니다</p>
                    </div>
                    <label class="relative inline-flex items-center cursor-pointer">
                      <input type="checkbox" class="sr-only peer">
                      <div class="w-11 h-6 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600 bg-gray-200"></div>
                    </label>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </header>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUIStore } from '@/stores/ui'
import { useAuthStore } from '@/stores/auth'
import ModeToggle from '@/components/common/ModeToggle.vue'

const router = useRouter()
const uiStore = useUIStore()
const authStore = useAuthStore()

const isModelDropdownOpen = ref(false)
const isUserMenuOpen = ref(false)
const isSettingsModalOpen = ref(false)
const activeSettingsTab = ref('general')

// MEM0 관련 상태 (SOP 기반 장애 대응 시스템 특화)
const mem0Enabled = ref(true)
const memoryRetentionDays = ref('30')
const autoMemoryGeneration = ref(true)
const totalMemoryCount = ref(8)
const preferenceCount = ref(2)
const patternCount = ref(3)
const contextCount = ref(3)
const lastMemoryUpdate = ref('35분 전')

// 메모리 타입별 색상 매핑
const getMemoryTypeColor = (type) => {
  const colors = {
    preference: 'var(--color-blue-100)',
    pattern: 'var(--color-purple-100)', 
    context: 'var(--color-green-100)',
    history: 'var(--color-orange-100)'
  }
  return colors[type] || 'var(--color-gray-100)'
}

const getMemoryTypeLabel = (type) => {
  const labels = {
    preference: '선호도',
    pattern: '패턴',
    context: '컨텍스트', 
    history: '히스토리'
  }
  return labels[type] || '기타'
}

// Mock 메모리 데이터 (RAG 시스템 검색 패턴 기반)
const mockMemories = ref([
  {
    id: 1,
    title: 'SOP 콜렉션 검색 패턴',
    content: '최근 7일간 총 검색 중 78%가 SOP 콜렉션에서 이루어졌으며, 특히 IC-PNA와 IC-SOMF 도메인 문서를 집중적으로 검색함.',
    timestamp: '1시간 전',
    type: 'pattern'
  },
  {
    id: 2,
    title: '검색 키워드 선호도',
    content: '사용자는 "장애 대응", "SOP", "트러블슈팅" 키워드를 자주 사용하며, 구체적인 에러 코드나 인스턴스 ID와 함께 검색하는 패턴을 보임.',
    timestamp: '3시간 전',
    type: 'preference'
  },
  {
    id: 3,
    title: '현재 활성 프로젝트 컨텍스트',
    content: 'OSS 지식 관리 시스템 개발 중이며, MEM0 통합과 SOP 현행화 작업을 병행하고 있음. 관련 문서 검색 빈도가 높음.',
    timestamp: '6시간 전',
    type: 'context'
  },
  {
    id: 4,
    title: '검색 결과 선호 형식',
    content: '단계별 체크리스트 형태의 답변을 선호하며, SOP 문서 링크와 함께 구체적인 실행 방법을 요청하는 패턴이 관찰됨.',
    timestamp: '1일 전',
    type: 'preference'
  },
  {
    id: 5,
    title: '콜렉션 사용 빈도 분석',
    content: 'SOP 콜렉션 78%, 기술문서 콜렉션 15%, 일반지식 콜렉션 7% 순으로 사용하며, SOP 관련 질문이 압도적으로 많음.',
    timestamp: '1일 전',
    type: 'pattern'
  },
  {
    id: 6,
    title: '검색 시간대 패턴',
    content: '주로 오전 9-11시, 오후 2-4시에 검색 활동이 집중되며, 긴급 장애 관련 검색은 즉시 수행하는 패턴을 보임.',
    timestamp: '2일 전',
    type: 'pattern'
  },
  {
    id: 7,
    title: '담당 도메인 정보',
    content: 'IC-ADM-EM, IC-PNA, IC-SOMF, IC-WM 도메인을 담당하며, 각 도메인별 SOP 문서에 대한 깊이 있는 이해를 보유함.',
    timestamp: '2일 전',
    type: 'context'
  },
  {
    id: 8,
    title: '검색 결과 활용 패턴',
    content: '검색된 SOP 문서를 북마크하는 빈도가 높으며, 특히 장애 대응 절차와 에스컬레이션 가이드를 자주 참조함.',
    timestamp: '3일 전',
    type: 'preference'
  }
])

// 최근 메모리 (최대 3개)
const recentMemories = computed(() => {
  return mockMemories.value.slice(0, 3)
})

// 사용자 정보 관련 computed 속성들
const getUserInitials = computed(() => {
    if (!authStore.user) return 'U';
    
    if (authStore.user.fullName) {
        // fullName이 있으면 첫 글자들 사용
        return authStore.user.fullName
            .split(' ')
            .map(name => name.charAt(0))
            .join('')
            .toUpperCase()
            .slice(0, 2);
    } else if (authStore.user.username) {
        // username이 있으면 첫 글자 사용
        return authStore.user.username.charAt(0).toUpperCase();
    }
    
    return 'U';
});

const getUserDisplayName = computed(() => {
    if (!authStore.user) return '사용자';
    
    return authStore.user.fullName || authStore.user.username || '사용자';
});

const getUserRole = computed(() => {
    if (!authStore.user || !authStore.user.role) return '사용자';
    
    const roleMap = {
        'ADMIN': '관리자',
        'USER': '사용자',
        'MANAGER': '매니저'
    };
    
    return roleMap[authStore.user.role] || authStore.user.role;
});

// 로그아웃 처리
const handleLogout = () => {
    authStore.logout()
    isUserMenuOpen.value = false
    router.push('/login')
}

// 설정 모달 관련 함수들
const openSettingsModal = () => {
    isSettingsModalOpen.value = true
    isUserMenuOpen.value = false
}

const closeSettingsModal = () => {
    isSettingsModalOpen.value = false
}

// MEM0 관련 함수들 (RAG 시스템 검색 패턴 기반)
const addMockMemory = () => {
    const ragMemoryTemplates = [
        {
            title: '새로운 검색 패턴 감지',
            content: '최근 "벡터 검색"과 "하이브리드 검색" 키워드 사용 빈도가 증가하고 있으며, 검색 성능 최적화에 대한 관심이 높아지고 있음',
            type: 'pattern'
        },
        {
            title: '콜렉션 선호도 변화',
            content: '기술문서 콜렉션 사용률이 15%에서 22%로 증가했으며, API 문서와 아키텍처 가이드 검색이 늘어나고 있음',
            type: 'preference'
        },
        {
            title: '검색 세션 컨텍스트',
            content: '현재 MEM0 통합 작업 중이며, 관련 기술 문서와 벡터 DB 설정 가이드를 집중적으로 검색하고 있음',
            type: 'context'
        },
        {
            title: '검색 결과 만족도 패턴',
            content: '상세한 코드 예시가 포함된 답변에 대한 만족도가 높으며, 단계별 구현 가이드를 선호하는 패턴이 관찰됨',
            type: 'pattern'
        },
        {
            title: '검색 필터 사용 패턴',
            content: '최근 검색 시 날짜 범위 필터를 자주 사용하며, 최신 문서를 우선적으로 검색하는 경향이 강해지고 있음',
            type: 'preference'
        }
    ]
    
    const randomTemplate = ragMemoryTemplates[Math.floor(Math.random() * ragMemoryTemplates.length)]
    const newMemory = {
        id: mockMemories.value.length + 1,
        ...randomTemplate,
        timestamp: '방금 전'
    }
    mockMemories.value.unshift(newMemory)
    
    // 통계 업데이트
    totalMemoryCount.value += 1
    if (randomTemplate.type === 'preference') preferenceCount.value += 1
    else if (randomTemplate.type === 'pattern') patternCount.value += 1
    else if (randomTemplate.type === 'context') contextCount.value += 1
    
    lastMemoryUpdate.value = '방금 전'
}

const clearAllMemories = () => {
    if (confirm('모든 메모리를 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.')) {
        mockMemories.value = []
        totalMemoryCount.value = 0
        preferenceCount.value = 0
        patternCount.value = 0
        contextCount.value = 0
        lastMemoryUpdate.value = '방금 전'
    }
}

// 사용 가능한 모델들
const models = ref([
  {
    id: 'brain-clone-standard',
    name: 'Brain Clone Standard',
    description: '균형잡힌 성능과 속도를 제공하는 일반적인 용도의 모델'
  },
  {
    id: 'brain-clone-pro',
    name: 'Brain Clone Pro',
    description: '최고 성능의 모델, 복잡한 작업에 최적화'
  },
  {
    id: 'brain-clone-fast',
    name: 'Brain Clone Fast',
    description: '빠른 응답 속도를 제공하는 경량 모델'
  }
])

const selectedModel = ref(models.value[0])

// 모델 선택
const selectModel = (model) => {
  selectedModel.value = model
}

// 드롭다운 닫기
const closeAllDropdowns = () => {
  isUserMenuOpen.value = false
  isModelDropdownOpen.value = false
}

// ESC 키로 드롭다운 닫기
const handleEscape = (event) => {
  if (event.key === 'Escape') {
    closeAllDropdowns()
  }
}

onMounted(() => {
  document.addEventListener('keydown', handleEscape)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleEscape)
})
</script>