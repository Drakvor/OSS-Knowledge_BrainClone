import { createRouter, createWebHistory } from "vue-router";
import ChatView from "@/views/ChatView.vue";
import MockChatView from "@/views/MockChatView.vue";
import AgentView from "@/views/AgentView.vue";
import DataUploadView from "@/views/DataUploadView.vue";
import RAGManagementView from "@/views/RAGManagementView.vue";
import GraphRAGView from "@/views/GraphRAGView.vue";
import LoginView from "@/views/LoginView.vue";
import { useAuthStore } from "@/stores/auth";

const routes = [
    {
        path: "/login",
        name: "login",
        component: LoginView,
        meta: { requiresAuth: false },
    },
    {
        path: "/",
        name: "home",
        component: () => import("@/views/ChatView.vue"),
        meta: { requiresAuth: true },
    },
    {
        path: "/chat",
        name: "chat",
        component: ChatView,
        meta: { requiresAuth: true },
    },
    {
        path: "/demo-chat",
        name: "demo-chat",
        component: MockChatView,
        meta: { requiresAuth: true },
    },
    {
        path: "/agent",
        name: "agent",
        component: AgentView,
        meta: { requiresAuth: true },
    },
    {
        path: "/upload",
        name: "upload",
        component: DataUploadView,
        meta: { requiresAuth: true },
    },
    {
        path: "/rag-management",
        name: "rag-management",
        component: RAGManagementView,
        meta: { requiresAuth: true },
    },
    {
        path: "/graph-rag",
        name: "graph-rag",
        component: GraphRAGView,
        meta: { requiresAuth: true },
    },
];

const router = createRouter({
    history: createWebHistory(),
    routes,
});

// 라우터 가드
router.beforeEach((to, from, next) => {
    const authStore = useAuthStore();

    // 토큰이 실제로 존재하는지 직접 확인
    const hasValidToken = authStore.token && authStore.isAuthenticated;

    // 로그인 페이지는 인증 체크 제외
    if (to.name === "login") {
        // 이미 로그인된 상태라면 홈으로 리다이렉트
        if (hasValidToken) {
            next("/");
        } else {
            next();
        }
        return;
    }

    // 인증이 필요한 페이지
    if (to.meta.requiresAuth !== false) {
        if (!hasValidToken) {
            // 로그인되지 않은 경우 로그인 페이지로 리다이렉트
            next("/login");
        } else {
            next();
        }
    } else {
        next();
    }
});

export default router;
