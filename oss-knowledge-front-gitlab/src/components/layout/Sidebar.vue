<template>
    <!-- 사이드바 (접힌/펼쳐진 상태 통합) -->
    <div
        class="fixed md:relative inset-y-0 left-0 z-40 flex flex-col shadow-sm transform transition-all duration-300 ease-in-out sidebar"
        :class="isCollapsed ? 'w-12' : 'w-80'"
        style="background-color: var(--color-bg-secondary); border-right: 1px solid var(--color-border-light)"
    >
        <!-- 접힌 상태일 때 아이콘들 -->
        <div v-if="isCollapsed" class="flex flex-col h-full">
            <!-- 상단 아이콘들 -->
            <div class="flex flex-col items-center py-4 space-y-2">
                <!-- 펼치기 버튼 -->
                <button
                    @click="toggleCollapse"
                    class="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-all duration-200"
                    title="사이드바 펼치기"
                >
                    <svg
                        class="w-5 h-5"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                    >
                        <path
                            stroke-linecap="round"
                            stroke-linejoin="round"
                            stroke-width="2"
                            d="M4 6h16M4 12h16M4 18h16"
                        />
                    </svg>
                </button>

                <!-- 채팅 페이지 버튼 -->
                <router-link
                    to="/"
                    class="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-all duration-200"
                    :class="{ 'bg-primary-50 text-primary-600': $route.path === '/' }"
                    title="채팅"
                >
                    <svg
                        class="w-5 h-5"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                    >
                        <path
                            stroke-linecap="round"
                            stroke-linejoin="round"
                            stroke-width="2"
                            d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
                        />
                    </svg>
                </router-link>

                <!-- 새 채팅 버튼 -->
                <button
                    @click="conversationStore.createNewConversation()"
                    class="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-all duration-200"
                    title="새 채팅"
                >
                    <svg
                        class="w-5 h-5"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                    >
                        <path
                            stroke-linecap="round"
                            stroke-linejoin="round"
                            stroke-width="2"
                            d="M12 4v16m8-8H4"
                        />
                    </svg>
                </button>

                <!-- 검색 버튼 -->
                <button
                    @click="expandForSearch"
                    class="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-all duration-200"
                    title="검색"
                >
                    <svg
                        class="w-5 h-5"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                    >
                        <path
                            stroke-linecap="round"
                            stroke-linejoin="round"
                            stroke-width="2"
                            d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                        />
                    </svg>
                </button>

                <!-- 모드 토글 (접힌 상태) -->
                <div class="p-2">
                    <div 
                        @click="uiStore.toggleMode()"
                        class="w-6 h-6 rounded-full cursor-pointer transition-all duration-200 flex items-center justify-center"
                        :class="uiStore.isKnowledgeMode ? 'bg-gradient-to-r from-secondary-400 to-secondary-500' : 'bg-gradient-to-r from-primary-400 to-primary-500'"
                        :title="uiStore.isAgentMode ? 'Knowledge 모드로 전환' : 'Agent 모드로 전환'"
                    >
                        <svg v-if="uiStore.isKnowledgeMode" class="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                        </svg>
                        <svg v-else class="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                        </svg>
                    </div>
                </div>

                <!-- 관리 기능 드롭다운 (접힌 상태) -->
                <div class="relative">
                    <button
                        @click="toggleManagementDropdown"
                        class="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-all duration-200"
                        :class="{ 'bg-primary-50 text-primary-600': isManagementRouteActive }"
                        title="관리 기능"
                    >
                        <svg
                            class="w-5 h-5"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                        >
                            <path
                                stroke-linecap="round"
                                stroke-linejoin="round"
                                stroke-width="2"
                                d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
                            />
                            <path
                                stroke-linecap="round"
                                stroke-linejoin="round"
                                stroke-width="2"
                                d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                            />
                        </svg>
                    </button>
                    
                    <!-- 접힌 상태 드롭다운 메뉴 -->
                    <Transition
                        enter-active-class="transition ease-out duration-200"
                        enter-from-class="opacity-0 scale-95"
                        enter-to-class="opacity-100 scale-100"
                        leave-active-class="transition ease-in duration-150"
                        leave-from-class="opacity-100 scale-100"
                        leave-to-class="opacity-0 scale-95"
                    >
                        <div
                            v-if="isManagementDropdownOpen"
                            class="absolute left-full top-0 ml-2 bg-white border border-gray-200 rounded-lg shadow-lg z-50 min-w-40"
                        >
                            <div class="py-1">
                                <router-link
                                    to="/upload"
                                    @click="closeManagementDropdown"
                                    class="flex items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 hover:text-gray-900 transition-colors duration-200"
                                    :class="route.path === '/upload' ? 'bg-primary-50 text-primary-600' : ''"
                                >
                                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"/>
                                    </svg>
                                    데이터 업로드
                                </router-link>
                                
                                <router-link
                                    to="/rag-management"
                                    @click="closeManagementDropdown"
                                    class="flex items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 hover:text-gray-900 transition-colors duration-200"
                                    :class="route.path === '/rag-management' ? 'bg-primary-50 text-primary-600' : ''"
                                >
                                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/>
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
                                    </svg>
                                    RAG 관리
                                </router-link>
                                
                                <router-link
                                    to="/graph-rag"
                                    @click="closeManagementDropdown"
                                    class="flex items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 hover:text-gray-900 transition-colors duration-200"
                                    :class="route.path === '/graph-rag' ? 'bg-primary-50 text-primary-600' : ''"
                                >
                                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7"/>
                                    </svg>
                                    Graph RAG
                                </router-link>
                            </div>
                        </div>
                    </Transition>
                </div>

                <!-- Knowledge 모드: 대화 아이콘들 -->
                <div v-if="uiStore.isKnowledgeMode" class="border-t border-gray-200 pt-2 w-full">
                    <div class="flex flex-col items-center space-y-1">
                        <div
                            v-for="conv in conversationStore.filteredConversations.slice(0, 6)"
                            :key="conv.id"
                            @click="handleConversationClick(conv.id)"
                            :class="[
                                'relative p-1.5 rounded-lg cursor-pointer transition-all duration-200 group',
                                conversationStore.currentConversationId === conv.id
                                    ? 'bg-primary-50 text-primary-600'
                                    : 'hover:bg-gray-100 text-gray-600',
                            ]"
                            :title="conv.title"
                        >
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                            </svg>

                            <div class="absolute left-full ml-2 top-1/2 -translate-y-1/2 bg-gray-800 text-white text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity duration-200 whitespace-nowrap z-50 pointer-events-none">
                                {{ conv.title }}
                            </div>
                        </div>

                        <div v-if="conversationStore.filteredConversations.length > 6" class="text-center">
                            <button
                                @click="toggleCollapse"
                                class="w-full p-1.5 text-xs text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                                title="모든 대화 보기"
                            >
                                ⋯
                            </button>
                        </div>
                    </div>
                </div>

                <!-- Agent 모드: Agent 카테고리 아이콘들 -->
                <div v-else-if="uiStore.isAgentMode" class="border-t border-gray-200 pt-2 w-full">
                    <div class="flex flex-col items-center space-y-1">
                        <div
                            v-for="category in agentCategories.slice(0, 6)"
                            :key="category.id"
                            @click="handleCategoryIconClick(category)"
                            class="relative p-1.5 rounded-lg cursor-pointer transition-all duration-200 group hover:bg-gray-100 text-gray-600"
                            :title="category.name"
                        >
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="category.icon" />
                            </svg>

                            <div class="absolute left-full ml-2 top-1/2 -translate-y-1/2 bg-gray-800 text-white text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity duration-200 whitespace-nowrap z-50 pointer-events-none">
                                {{ category.name }}
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- 하단 아이콘들 -->
            <div
                class="mt-auto flex flex-col items-center pb-4 space-y-2 border-t border-gray-200 pt-2"
            >
                <!-- 사용자 아바타 -->
                <button
                    @click="openUserMenu"
                    class="w-8 h-8 bg-gray-800 rounded-full flex items-center justify-center text-white font-medium text-xs hover:ring-2 hover:ring-blue-200 transition-all"
                    title="사용자 메뉴"
                >
                    {{ getUserInitials }}
                </button>

                <!-- 설정 버튼 -->
                <button
                    @click="openSettings"
                    class="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-all duration-200"
                    title="설정"
                >
                    <svg
                        class="w-4 h-4"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                    >
                        <path
                            stroke-linecap="round"
                            stroke-linejoin="round"
                            stroke-width="2"
                            d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
                        />
                        <path
                            stroke-linecap="round"
                            stroke-linejoin="round"
                            stroke-width="2"
                            d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                        />
                    </svg>
                </button>
            </div>
        </div>

        <!-- 펼쳐진 상태일 때 전체 사이드바 -->
        <div v-else class="flex flex-col h-full">
            <!-- 공통 헤더 (모드에 관계없이 고정) -->
            <div class="p-4 border-b border-gray-200">
                <div class="flex items-center justify-between mb-4">
                    <!-- 햄버거 메뉴 -->
                    <button
                        @click="toggleCollapse"
                        class="p-2 hover:bg-gray-100 rounded-lg transition-all duration-200"
                        title="사이드바 접기"
                    >
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
                        </svg>
                    </button>

                    <!-- 새 채팅 버튼 (Knowledge 모드) / Agent 타이틀 (Agent 모드) -->
                    <div v-if="uiStore.isKnowledgeMode">
                        <button
                            @click="conversationStore.createNewConversation()"
                            class="flex items-center gap-2 px-3 py-2 text-sm font-medium text-gray-700 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-all duration-200"
                        >
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
                            </svg>
                            새 채팅
                        </button>
                    </div>
                    <div v-else class="flex items-center gap-2">
                        <svg class="w-5 h-5 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                        </svg>
                        <span class="text-sm font-medium text-gray-900">AI Agents</span>
                    </div>
                </div>

                <!-- 모드 토글 -->
                <div class="mb-4 flex justify-center">
                    <ModeToggle />
                </div>

                <!-- 네비게이션 버튼들 (Knowledge 모드에서만) -->
                <div v-if="uiStore.isKnowledgeMode" class="flex gap-2">
                    <!-- 메인 채팅 버튼 -->
                    <router-link
                        to="/"
                        class="flex items-center gap-2 px-3 py-2.5 text-sm font-medium rounded-lg transition-all duration-200 flex-1 justify-center"
                        :class="route.path === '/' ? 'bg-primary-50 text-primary-600 border border-primary-200' : 'text-gray-700 hover:text-gray-900 hover:bg-gray-100'"
                    >
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"/>
                        </svg>
                        채팅
                    </router-link>
                    
                    <!-- 관리 기능 드롭다운 -->
                    <div class="relative flex-1">
                        <button
                            @click="toggleManagementDropdown"
                            class="flex items-center gap-2 px-3 py-2.5 text-sm font-medium rounded-lg transition-all duration-200 w-full justify-center"
                            :class="isManagementDropdownOpen || isManagementRouteActive ? 'bg-gray-50 text-gray-900 border border-gray-200' : 'text-gray-700 hover:text-gray-900 hover:bg-gray-100'"
                        >
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/>
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
                            </svg>
                            관리
                            <svg 
                                class="w-4 h-4 transition-transform duration-200"
                                :class="{ 'rotate-180': isManagementDropdownOpen }"
                                fill="none" 
                                stroke="currentColor" 
                                viewBox="0 0 24 24"
                            >
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/>
                            </svg>
                        </button>
                        
                        <!-- 드롭다운 메뉴 -->
                        <Transition
                            enter-active-class="transition ease-out duration-200"
                            enter-from-class="opacity-0 scale-95"
                            enter-to-class="opacity-100 scale-100"
                            leave-active-class="transition ease-in duration-150"
                            leave-from-class="opacity-100 scale-100"
                            leave-to-class="opacity-0 scale-95"
                        >
                            <div
                                v-if="isManagementDropdownOpen"
                                class="absolute top-full left-0 mt-1 bg-white border border-gray-200 rounded-lg shadow-lg z-50 min-w-40"
                            >
                                <div class="py-1">
                                    <router-link
                                        to="/upload"
                                        @click="closeManagementDropdown"
                                        class="flex items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 hover:text-gray-900 transition-colors duration-200"
                                        :class="route.path === '/upload' ? 'bg-primary-50 text-primary-600' : ''"
                                    >
                                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"/>
                                        </svg>
                                        데이터 업로드
                                    </router-link>
                                    
                                    <router-link
                                        to="/rag-management"
                                        @click="closeManagementDropdown"
                                        class="flex items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 hover:text-gray-900 transition-colors duration-200"
                                        :class="route.path === '/rag-management' ? 'bg-primary-50 text-primary-600' : ''"
                                    >
                                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/>
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
                                        </svg>
                                        RAG 관리
                                    </router-link>
                                    
                                    <router-link
                                        to="/graph-rag"
                                        @click="closeManagementDropdown"
                                        class="flex items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 hover:text-gray-900 transition-colors duration-200"
                                        :class="route.path === '/graph-rag' ? 'bg-primary-50 text-primary-600' : ''"
                                    >
                                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7"/>
                                        </svg>
                                        Graph RAG
                                    </router-link>
                                </div>
                            </div>
                        </Transition>
                    </div>
                </div>

                <!-- Agent 채팅 버튼 및 편집 버튼 (Agent 모드에서만) -->
                <div v-else class="flex gap-2">
                    <router-link
                        to="/"
                        class="flex items-center gap-2 px-3 py-2.5 text-sm font-medium rounded-lg transition-all duration-200 flex-1 justify-center"
                        :class="route.path === '/' ? 'bg-primary-50 text-primary-600 border border-primary-200' : 'text-gray-700 hover:text-gray-900 hover:bg-gray-100'"
                    >
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                        </svg>
                        Agent 채팅
                    </router-link>
                    
                    <!-- 편집 모드 토글 버튼 -->
                    <button
                        @click="toggleEditMode"
                        class="flex items-center gap-1 px-2 py-2.5 text-sm font-medium rounded-lg transition-all duration-200"
                        :class="isEditMode ? 'bg-orange-50 text-orange-600 border border-orange-200' : 'text-gray-700 hover:text-gray-900 hover:bg-gray-100'"
                        :title="isEditMode ? '편집 모드 종료' : '편집 모드'"
                    >
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                        </svg>
                    </button>
                </div>
            </div>

            <!-- ============ KNOWLEDGE 모드 컨텐츠 START ============ -->
            <div v-if="uiStore.isKnowledgeMode" class="flex flex-col flex-1 min-h-0">
                <!-- 검색 영역 -->
                <div class="flex-shrink-0 p-4 border-b border-gray-200">
                    <div class="relative">
                        <input
                            v-model="conversationStore.searchQuery"
                            type="text"
                            placeholder="대화 검색..."
                            class="w-full pl-10 pr-4 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200"
                        />
                        <svg class="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                        </svg>
                    </div>
                </div>

                <!-- 대화 목록 -->
                <div class="flex-1 min-h-0 overflow-y-auto overscroll-contain">
                    <div class="p-2">
                        <div
                            v-for="conv in conversationStore.filteredConversations"
                            :key="conv.id"
                            @click="handleConversationClick(conv.id)"
                            :class="[
                                'group flex items-center gap-3 p-2.5 rounded-lg cursor-pointer transition-all duration-200',
                                conversationStore.currentConversationId === conv.id
                                    ? 'bg-blue-50 text-blue-700' 
                                    : 'hover:bg-gray-50 text-gray-700',
                            ]"
                        >
                            <!-- 대화 아이콘 -->
                            <div
                                :class="[
                                    'flex-shrink-0 w-6 h-6 rounded-md flex items-center justify-center',
                                    conversationStore.currentConversationId === conv.id
                                        ? 'bg-blue-100 text-blue-600'
                                        : 'bg-gray-100 text-gray-500',
                                ]"
                            >
                                <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                                </svg>
                            </div>

                            <!-- 대화 정보 -->
                            <div class="flex-1 min-w-0">
                                <div class="text-sm font-medium truncate">{{ conv.title }}</div>
                                <div class="text-xs text-gray-500 mt-0.5">{{ formatTime(conv.updatedAt) }}</div>
                            </div>

                            <!-- 액션 버튼들 -->
                            <div class="flex-shrink-0 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
                                <button
                                    @click.stop="handleDelete(conv.id)"
                                    class="p-1 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded transition-all duration-200"
                                    title="삭제"
                                >
                                    <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                    </svg>
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <!-- ============ KNOWLEDGE 모드 컨텐츠 END ============ -->
            
            <!-- ============ AGENT 모드 컨텐츠 START ============ -->
            <div v-else-if="uiStore.isAgentMode" class="flex flex-col flex-1 min-h-0">
                <!-- Agent 카테고리 목록 -->
                <div class="flex-1 min-h-0 overflow-y-auto overscroll-contain">
                    <div class="p-2">
                        <div
                            v-for="category in agentCategories"
                            :key="category.id"
                            class="mb-2"
                        >
                            <!-- 카테고리 헤더 -->
                            <div
                                @click="!isEditMode && handleCategoryHeaderClick(category)"
                                class="flex items-center justify-between p-2 rounded-lg transition-all duration-200"
                                :class="[
                                    { 'bg-gray-50': expandedAgentCategories.includes(category.id) },
                                    isEditMode ? 'hover:bg-orange-50' : 'cursor-pointer hover:bg-gray-50'
                                ]"
                            >
                                <div class="flex items-center gap-2.5 flex-1">
                                    <div class="w-7 h-7 rounded-lg bg-primary-100 flex items-center justify-center">
                                        <svg class="w-4 h-4 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="category.icon" />
                                        </svg>
                                    </div>
                                    <div class="leading-tight flex-1">
                                        <!-- 편집 모드가 아니거나 편집 중이 아닌 경우 -->
                                        <div v-if="!isEditMode || editingCategoryId !== category.id">
                                            <div class="text-sm font-medium text-gray-900">{{ category.name }}</div>
                                            <div v-if="category.agents && category.agents.length > 0" class="text-xs text-gray-500 -mt-0.5">{{ category.agents.length }}개 Agent</div>
                                            <div v-else-if="category.url" class="text-xs text-gray-500 -mt-0.5">외부 서비스</div>
                                        </div>
                                        
                                        <!-- 편집 모드에서 편집 중인 경우 -->
                                        <div v-else class="space-y-1">
                                            <input
                                                :data-category-id="category.id"
                                                v-model="editingCategoryName"
                                                @keyup.enter="saveCategoryEdit(category.id)"
                                                @keyup.escape="cancelCategoryEdit"
                                                @blur="saveCategoryEdit(category.id)"
                                                class="text-sm font-medium bg-white border border-blue-300 rounded px-2 py-0.5 w-full focus:outline-none focus:ring-1 focus:ring-blue-500"
                                                placeholder="카테고리 이름"
                                            />
                                            <div v-if="category.agents && category.agents.length > 0" class="text-xs text-gray-500">{{ category.agents.length }}개 Agent</div>
                                            <div v-else-if="category.url" class="text-xs text-gray-500">BPMN 프로세스</div>
                                        </div>
                                    </div>
                                </div>
                                
                                <!-- 편집 모드가 아닐 때 -->
                                <div v-if="!isEditMode" class="flex items-center">
                                    <!-- 하위 메뉴가 있는 경우에만 화살표 표시 -->
                                    <svg 
                                        v-if="category.agents && category.agents.length > 0"
                                        class="w-4 h-4 text-gray-400 transition-transform duration-200"
                                        :class="{ 'rotate-180': expandedAgentCategories.includes(category.id) }"
                                        fill="none" 
                                        stroke="currentColor" 
                                        viewBox="0 0 24 24"
                                    >
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/>
                                    </svg>
                                    <!-- 외부 링크인 경우 외부 링크 아이콘 표시 -->
                                    <svg 
                                        v-else-if="category.url"
                                        class="w-4 h-4 text-gray-400"
                                        fill="none" 
                                        stroke="currentColor" 
                                        viewBox="0 0 24 24"
                                    >
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-1M14 4h6m0 0v6m0-6L10 14"/>
                                    </svg>
                                </div>
                                
                                <!-- 편집 모드일 때 편집/삭제 버튼 -->
                                <div v-else class="flex items-center gap-1">
                                    <!-- 하위 Agent 추가 버튼 (외부 링크가 아닌 경우에만) -->
                                    <button
                                        v-if="!category.url"
                                        @click="addAgent(category.id)"
                                        class="p-1 text-green-600 hover:text-green-700 hover:bg-green-50 rounded transition-all duration-200"
                                        title="Agent 추가"
                                    >
                                        <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
                                        </svg>
                                    </button>
                                    
                                    <!-- 카테고리 편집 버튼 -->
                                    <button
                                        @click="editCategory(category.id)"
                                        class="p-1 text-blue-600 hover:text-blue-700 hover:bg-blue-50 rounded transition-all duration-200"
                                        title="카테고리 편집"
                                    >
                                        <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                                        </svg>
                                    </button>
                                    
                                    <!-- 카테고리 삭제 버튼 -->
                                    <button
                                        @click="deleteCategory(category.id)"
                                        class="p-1 text-red-600 hover:text-red-700 hover:bg-red-50 rounded transition-all duration-200"
                                        title="카테고리 삭제"
                                    >
                                        <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                        </svg>
                                    </button>
                                </div>
                            </div>

                            <!-- Agent 목록 (확장된 상태에서만 표시) -->
                            <Transition
                                enter-active-class="transition-all duration-300 ease-out"
                                enter-from-class="opacity-0 max-h-0"
                                enter-to-class="opacity-100 max-h-96"
                                leave-active-class="transition-all duration-300 ease-in"
                                leave-from-class="opacity-100 max-h-96"
                                leave-to-class="opacity-0 max-h-0"
                            >
                                <div v-if="expandedAgentCategories.includes(category.id)" class="ml-4 mt-1.5 space-y-0.5 overflow-hidden">
                                    <div
                                        v-for="agent in category.agents"
                                        :key="agent.id"
                                        @click="!isEditMode && handleAgentClick(agent)"
                                        class="group flex items-center gap-3 p-2 rounded-lg transition-all duration-200"
                                        :class="isEditMode ? 'hover:bg-orange-50' : 'cursor-pointer hover:bg-gray-50'"
                                    >
                                        <div class="w-6 h-6 rounded-md bg-gray-100 flex items-center justify-center">
                                            <svg class="w-3 h-3 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="agent.icon" />
                                            </svg>
                                        </div>
                                        <div class="flex-1">
                                            <!-- 편집 모드가 아니거나 편집 중이 아닌 경우 -->
                                            <div v-if="!isEditMode || editingAgentId !== agent.id">
                                                <div class="text-sm font-medium text-gray-700">{{ agent.name }}</div>
                                                <div class="text-xs text-gray-500 mt-0">{{ agent.description }}</div>
                                            </div>
                                            
                                            <!-- 편집 모드에서 편집 중인 경우 -->
                                            <div v-else class="space-y-1">
                                                <input
                                                    :data-agent-id="agent.id"
                                                    v-model="editingAgentName"
                                                    @keyup.enter="focusAgentDescription(agent.id)"
                                                    @keyup.escape="cancelAgentEdit"
                                                    class="text-sm font-medium bg-white border border-blue-300 rounded px-2 py-0.5 w-full focus:outline-none focus:ring-1 focus:ring-blue-500"
                                                    placeholder="Agent 이름"
                                                />
                                                <input
                                                    :data-agent-description-id="agent.id"
                                                    v-model="editingAgentDescription"
                                                    @keyup.enter="saveAgentEdit(category.id, agent.id)"
                                                    @keyup.escape="cancelAgentEdit"
                                                    @blur="saveAgentEdit(category.id, agent.id)"
                                                    class="text-xs bg-white border border-blue-300 rounded px-2 py-0.5 w-full focus:outline-none focus:ring-1 focus:ring-blue-500"
                                                    placeholder="Agent 설명"
                                                />
                                            </div>
                                        </div>
                                        
                                        <!-- 편집 모드가 아닐 때 화살표 -->
                                        <div v-if="!isEditMode" class="opacity-0 group-hover:opacity-100 transition-opacity">
                                            <svg class="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
                                            </svg>
                                        </div>
                                        
                                        <!-- 편집 모드일 때 편집/삭제 버튼 -->
                                        <div v-else class="flex items-center gap-1">
                                            <!-- Agent 편집 버튼 -->
                                            <button
                                                @click="editAgent(category.id, agent.id)"
                                                class="p-1 text-blue-600 hover:text-blue-700 hover:bg-blue-50 rounded transition-all duration-200"
                                                title="Agent 편집"
                                            >
                                                <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                                                </svg>
                                            </button>
                                            
                                            <!-- Agent 삭제 버튼 -->
                                            <button
                                                @click="deleteAgent(category.id, agent.id)"
                                                class="p-1 text-red-600 hover:text-red-700 hover:bg-red-50 rounded transition-all duration-200"
                                                title="Agent 삭제"
                                            >
                                                <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                                </svg>
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            </Transition>
                        </div>
                        
                        <!-- 새 카테고리 추가 버튼 (편집 모드일 때만) -->
                        <div v-if="isEditMode" class="mt-4 px-2">
                            <button
                                @click="addCategory"
                                class="w-full flex items-center justify-center gap-2 p-3 border-2 border-dashed border-gray-300 rounded-lg text-gray-500 hover:border-primary-300 hover:text-primary-600 hover:bg-primary-50 transition-all duration-200"
                            >
                                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
                                </svg>
                                <span class="text-sm font-medium">새 카테고리 추가</span>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
            <!-- ============ AGENT 모드 컨텐츠 END ============ -->

            <!-- 공통 하단 사용자 영역 -->
            <div class="p-4 border-t border-gray-200">
                <div class="flex items-center gap-3">
                    <div class="w-8 h-8 bg-gray-800 rounded-full flex items-center justify-center text-white font-medium text-sm">
                        {{ getUserInitials }}
                    </div>
                    <div class="flex-1">
                        <div class="text-sm font-medium text-gray-900">{{ getUserDisplayName }}</div>
                        <div class="text-xs text-gray-500">{{ getUserRole }}</div>
                    </div>
                    <button
                        @click="openSettings"
                        class="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-all duration-200"
                        title="설정"
                    >
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.55 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                        </svg>
                    </button>
                </div>
            </div>
        </div>
    </div>

    <!-- 모바일 오버레이 -->
    <Transition
        enter-active-class="transition-opacity duration-300"
        enter-from-class="opacity-0"
        enter-to-class="opacity-100"
        leave-active-class="transition-opacity duration-300"
        leave-from-class="opacity-100"
        leave-to-class="opacity-0"
    >
        <div
            v-if="isOpen && uiStore.isMobile"
            @click="uiStore.toggleSidebar()"
            class="fixed inset-0 bg-black bg-opacity-50 z-30 md:hidden"
        ></div>
    </Transition>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from "vue";
import { useRoute } from "vue-router";
import { useConversationStore } from "@/stores/conversation";
import { useUIStore } from "@/stores/ui";
import { useAuthStore } from "@/stores/auth";
import ModeToggle from "@/components/common/ModeToggle.vue";

const conversationStore = useConversationStore();
const uiStore = useUIStore();
const authStore = useAuthStore();
const route = useRoute();

const isCollapsed = ref(false);
const isManagementDropdownOpen = ref(false);

// ============ AGENT 모드 관련 데이터 START ============
const expandedAgentCategories = ref(['data-analysis']); // 기본으로 첫 번째 카테고리 확장
const isEditMode = ref(false); // 편집 모드 상태
const editingCategoryId = ref(null); // 편집 중인 카테고리 ID
const editingAgentId = ref(null); // 편집 중인 Agent ID
const editingCategoryName = ref(''); // 편집 중인 카테고리 이름
const editingAgentName = ref(''); // 편집 중인 Agent 이름
const editingAgentDescription = ref(''); // 편집 중인 Agent 설명

// Mock 데이터 - Agent 카테고리 및 기능들
const agentCategories = ref([
    {
        id: 'data-analysis',
        name: '데이터 분석',
        icon: 'M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z',
        agents: [
            {
                id: 'data-visualization',
                name: '데이터 시각화',
                description: '차트와 그래프 생성',
                icon: 'M16 8v8m-4-5v5m-4-2v2m-2 4h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z',
                action: 'chat'
            },
            {
                id: 'statistical-analysis',
                name: '통계 분석',
                description: '고급 통계 분석 수행',
                icon: 'M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z',
                action: 'chat'
            },
            {
                id: 'report-generation',
                name: '리포트 생성',
                description: '자동 분석 리포트 작성',
                icon: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z',
                action: 'chat'
            }
        ]
    },
    {
        id: 'document-processing',
        name: '문서 처리',
        icon: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z',
        agents: [
            {
                id: 'document-summary',
                name: '문서 요약',
                description: '긴 문서를 간결하게 요약',
                icon: 'M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2',
                action: 'chat'
            },
            {
                id: 'translation',
                name: '번역',
                description: '다국어 번역 서비스',
                icon: 'M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129',
                action: 'chat'
            },
            {
                id: 'document-review',
                name: '문서 검토',
                description: '문법과 내용 검토',
                icon: 'M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4',
                action: 'chat'
            }
        ]
    },
    {
        id: 'coding-assistant',
        name: '코딩 도우미',
        icon: 'M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4',
        agents: [
            {
                id: 'code-review',
                name: '코드 리뷰',
                description: '코드 품질 분석 및 개선 제안',
                icon: 'M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4',
                action: 'chat'
            },
            {
                id: 'bug-fix',
                name: '버그 수정',
                description: '버그 탐지 및 수정 도움',
                icon: 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z',
                action: 'chat'
            },
            {
                id: 'refactoring',
                name: '리팩토링',
                description: '코드 구조 개선',
                icon: 'M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15',
                action: 'chat'
            }
        ]
    },
    {
        id: 'process-gpt',
        name: 'Process-GPT',
        icon: 'M13 10V3L4 14h7v7l9-11h-7z',
        url: 'https://oss.process-gpt.4.230.158.187.nip.io/definition-map',
        agents: [] // 하위 메뉴 없음
    }
]);
// ============ AGENT 모드 관련 데이터 END ============

const isOpen = computed(() => uiStore.isSidebarOpen);

// 관리 기능 드롭다운 관련
const isManagementRouteActive = computed(() => {
    return ['/upload', '/rag-management', '/graph-rag'].includes(route.path);
});

// 드롭다운 토글
const toggleManagementDropdown = () => {
    isManagementDropdownOpen.value = !isManagementDropdownOpen.value;
};

// 드롭다운 닫기
const closeManagementDropdown = () => {
    isManagementDropdownOpen.value = false;
};

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

// 사이드바 접기/펼치기
const toggleCollapse = () => {
    isCollapsed.value = !isCollapsed.value;
    // 로컬 스토리지에 상태 저장
    localStorage.setItem("sidebarCollapsed", isCollapsed.value);
};

// 검색을 위해 펼치기
const expandForSearch = () => {
    isCollapsed.value = false;
    // 다음 틱에서 검색 입력창에 포커스
    setTimeout(() => {
        const searchInput = document.querySelector(
            'input[placeholder="대화 검색..."]'
        );
        if (searchInput) {
            searchInput.focus();
        }
    }, 300); // transition 시간 후
};

// 사용자 메뉴 열기
const openUserMenu = () => {
    // 접힌 상태에서 사용자 아바타 클릭 시 펼치기
    if (isCollapsed.value) {
        isCollapsed.value = false;
    }
};



// 시간 포맷팅 (formatTime 함수 추가)
const formatTime = (timestamp) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return "방금 전";
    if (diffMins < 60) return `${diffMins}분 전`;
    if (diffHours < 24) return `${diffHours}시간 전`;
    if (diffDays < 7) return `${diffDays}일 전`;

    return date.toLocaleDateString("ko-KR", {
        month: "short",
        day: "numeric",
    });
};


// 대화 클릭 핸들러
const handleConversationClick = async (id) => {
    await conversationStore.selectConversation(id);
};

// 대화 삭제
const handleDelete = async (id) => {
    const conversation = conversationStore.conversations.find(c => c.id === id);
    const title = conversation?.title || '이 대화';
    
    if (confirm(`"${title}" 대화를 삭제하시겠습니까?\n\n이 작업은 되돌릴 수 없습니다.`)) {
        try {
            await conversationStore.deleteConversation(id);
        } catch (error) {
            console.error("Delete failed:", error);
        }
    }
};

// 설정 열기
const openSettings = () => {
    // TODO: 설정 모달 구현
    console.log("설정 열기");
};

// ============ AGENT 모드 관련 함수 START ============
// Agent 카테고리 확장/축소
const toggleAgentCategory = (categoryId) => {
    const index = expandedAgentCategories.value.indexOf(categoryId);
    if (index > -1) {
        expandedAgentCategories.value.splice(index, 1);
    } else {
        expandedAgentCategories.value.push(categoryId);
    }
};

// 카테고리 클릭 (접힌 상태에서)
const handleCategoryClick = (categoryId) => {
    // 접힌 상태에서 클릭 시 펼치고 해당 카테고리 확장
    isCollapsed.value = false;
    if (!expandedAgentCategories.value.includes(categoryId)) {
        expandedAgentCategories.value.push(categoryId);
    }
};

// 카테고리 헤더 클릭 핸들러
const handleCategoryHeaderClick = (category) => {
    // 외부 링크가 있는 경우 새 탭에서 열기
    if (category.url) {
        window.open(category.url, '_blank');
        
        // 모바일에서는 사이드바 닫기
        if (uiStore.isMobile) {
            uiStore.toggleSidebar();
        }
        return;
    }
    
    // 하위 메뉴가 있는 경우 토글
    if (category.agents && category.agents.length > 0) {
        toggleAgentCategory(category.id);
    }
};

// 카테고리 아이콘 클릭 핸들러 (접힌 상태에서)
const handleCategoryIconClick = (category) => {
    // 외부 링크가 있는 경우 바로 열기
    if (category.url) {
        window.open(category.url, '_blank');
        return;
    }
    
    // 하위 메뉴가 있는 경우 펼치고 해당 카테고리 확장
    isCollapsed.value = false;
    if (!expandedAgentCategories.value.includes(category.id)) {
        expandedAgentCategories.value.push(category.id);
    }
};

// Agent 클릭 핸들러
const handleAgentClick = (agent) => {
    console.log('Agent 클릭:', agent);
    console.log(`${agent.name} Agent 활성화됨`);
    
    // 모바일에서는 사이드바 닫기
    if (uiStore.isMobile) {
        uiStore.toggleSidebar();
    }
};

// ============ 편집 모드 관련 함수 START ============
// 편집 모드 토글
const toggleEditMode = () => {
    isEditMode.value = !isEditMode.value;
    if (!isEditMode.value) {
        // 편집 모드 종료 시 편집 상태 초기화
        editingCategoryId.value = null;
        editingAgentId.value = null;
    }
};

// 카테고리 추가
const addCategory = () => {
    const name = prompt('새 카테고리 이름을 입력하세요:');
    if (!name || !name.trim()) return;
    
    const newCategory = {
        id: `category-${Date.now()}`,
        name: name.trim(),
        icon: 'M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10', // 기본 아이콘
        agents: []
    };
    
    agentCategories.value.push(newCategory);
    console.log('새 카테고리 추가:', newCategory);
};

// 카테고리 편집
const editCategory = (categoryId) => {
    const category = agentCategories.value.find(c => c.id === categoryId);
    if (!category) return;
    
    editingCategoryId.value = categoryId;
    editingCategoryName.value = category.name;
    
    // 다음 틱에서 포커스
    setTimeout(() => {
        const inputEl = document.querySelector(`input[data-category-id="${categoryId}"]`);
        if (inputEl) {
            inputEl.focus();
            inputEl.select();
        }
    }, 50);
};

// 카테고리 편집 저장
const saveCategoryEdit = (categoryId) => {
    if (!editingCategoryName.value.trim()) {
        alert('카테고리 이름을 입력하세요.');
        return;
    }
    
    const category = agentCategories.value.find(c => c.id === categoryId);
    if (category) {
        category.name = editingCategoryName.value.trim();
        console.log('카테고리 수정됨:', category);
    }
    
    // 편집 상태 초기화
    editingCategoryId.value = null;
    editingCategoryName.value = '';
};

// 카테고리 편집 취소
const cancelCategoryEdit = () => {
    editingCategoryId.value = null;
    editingCategoryName.value = '';
};

// 카테고리 삭제
const deleteCategory = (categoryId) => {
    const category = agentCategories.value.find(c => c.id === categoryId);
    if (!category) return;
    
    if (confirm(`"${category.name}" 카테고리를 삭제하시겠습니까?\n\n모든 하위 Agent도 함께 삭제됩니다.`)) {
        const index = agentCategories.value.findIndex(c => c.id === categoryId);
        if (index > -1) {
            agentCategories.value.splice(index, 1);
            console.log('카테고리 삭제:', categoryId);
        }
    }
};

// Agent 추가
const addAgent = (categoryId) => {
    const name = prompt('새 Agent 이름을 입력하세요:');
    if (!name || !name.trim()) return;
    
    const description = prompt('Agent 설명을 입력하세요:');
    if (!description || !description.trim()) return;
    
    const category = agentCategories.value.find(c => c.id === categoryId);
    if (!category) return;
    
    const newAgent = {
        id: `agent-${Date.now()}`,
        name: name.trim(),
        description: description.trim(),
        icon: 'M13 10V3L4 14h7v7l9-11h-7z', // 기본 아이콘
        action: 'chat'
    };
    
    category.agents.push(newAgent);
    
    // 카테고리 확장
    if (!expandedAgentCategories.value.includes(categoryId)) {
        expandedAgentCategories.value.push(categoryId);
    }
    
    console.log('새 Agent 추가:', newAgent);
};

// Agent 편집
const editAgent = (categoryId, agentId) => {
    const category = agentCategories.value.find(c => c.id === categoryId);
    if (!category) return;
    
    const agent = category.agents.find(a => a.id === agentId);
    if (!agent) return;
    
    editingAgentId.value = agentId;
    editingAgentName.value = agent.name;
    editingAgentDescription.value = agent.description;
    
    // 다음 틱에서 포커스
    setTimeout(() => {
        const inputEl = document.querySelector(`input[data-agent-id="${agentId}"]`);
        if (inputEl) {
            inputEl.focus();
            inputEl.select();
        }
    }, 50);
};

// Agent 편집 저장
const saveAgentEdit = (categoryId, agentId) => {
    if (!editingAgentName.value.trim() || !editingAgentDescription.value.trim()) {
        alert('Agent 이름과 설명을 모두 입력하세요.');
        return;
    }
    
    const category = agentCategories.value.find(c => c.id === categoryId);
    if (!category) return;
    
    const agent = category.agents.find(a => a.id === agentId);
    if (agent) {
        agent.name = editingAgentName.value.trim();
        agent.description = editingAgentDescription.value.trim();
        console.log('Agent 수정됨:', agent);
    }
    
    // 편집 상태 초기화
    editingAgentId.value = null;
    editingAgentName.value = '';
    editingAgentDescription.value = '';
};

// Agent 편집 취소
const cancelAgentEdit = () => {
    editingAgentId.value = null;
    editingAgentName.value = '';
    editingAgentDescription.value = '';
};

// Agent 설명 입력으로 포커스 이동
const focusAgentDescription = (agentId) => {
    setTimeout(() => {
        const inputEl = document.querySelector(`input[data-agent-description-id="${agentId}"]`);
        if (inputEl) {
            inputEl.focus();
        }
    }, 50);
};

// Agent 삭제
const deleteAgent = (categoryId, agentId) => {
    const category = agentCategories.value.find(c => c.id === categoryId);
    if (!category) return;
    
    const agent = category.agents.find(a => a.id === agentId);
    if (!agent) return;
    
    if (confirm(`"${agent.name}" Agent를 삭제하시겠습니까?`)) {
        const index = category.agents.findIndex(a => a.id === agentId);
        if (index > -1) {
            category.agents.splice(index, 1);
            console.log('Agent 삭제:', agentId);
        }
    }
};
// ============ 편집 모드 관련 함수 END ============
// ============ AGENT 모드 관련 함수 END ============

// 컴포넌트 마운트 시 저장된 상태 복원
const restoreCollapsedState = () => {
    const saved = localStorage.getItem("sidebarCollapsed");
    if (saved !== null) {
        isCollapsed.value = saved === "true";
    }
};

// 외부 클릭으로 드롭다운 닫기
const handleClickOutside = (event) => {
    const dropdown = event.target.closest('.relative');
    if (!dropdown) {
        isManagementDropdownOpen.value = false;
    }
};

// 컴포넌트 마운트/언마운트 시 이벤트 리스너 등록/해제
onMounted(() => {
    document.addEventListener('click', handleClickOutside);
});

onUnmounted(() => {
    document.removeEventListener('click', handleClickOutside);
});

// 초기화
restoreCollapsedState();
</script>
