import { defineStore } from "pinia";
import { ref, computed } from "vue";
import {
    getRAGDepartmentsAPI,
    getRAGDepartmentByIdAPI,
    createRAGDepartmentAPI,
    updateRAGDepartmentAPI,
    deleteRAGDepartmentAPI,
    updateRAGDepartmentStatusAPI,
    getRAGDepartmentStatsAPI,
} from "@/services/metaApi";

export const useRAGDepartmentsStore = defineStore("ragDepartments", () => {
    // RAG 부서 목록
    const departments = ref([]);
    const loading = ref(false);
    const error = ref(null);

    // 검색어에 따른 필터링된 부서 목록
    const filteredDepartments = computed(() => (searchQuery) => {
        if (!searchQuery) return departments.value;

        const query = searchQuery.toLowerCase();
        return departments.value.filter(
            (dept) =>
                dept.name.toLowerCase().includes(query) ||
                dept.description.toLowerCase().includes(query) ||
                dept.keywords.some((keyword) =>
                    keyword.toLowerCase().includes(query)
                )
        );
    });

    // 부서 ID로 부서 찾기 (로컬 캐시에서)
    const getDepartmentById = (id) => {
        return departments.value.find((dept) => dept.id === id);
    };

    // 부서 이름으로 부서 찾기 (로컬 캐시에서)
    const getDepartmentByName = (name) => {
        return departments.value.find((dept) => dept.name === name);
    };

    // 새 부서 생성
    const createDepartment = async (departmentData) => {
        try {
            loading.value = true;
            error.value = null;

            const response = await createRAGDepartmentAPI(departmentData);
            const newDepartment = response.data;

            // 로컬 상태 업데이트
            departments.value.push(newDepartment);

            return newDepartment;
        } catch (err) {
            error.value = err.message;
            throw new Error("부서 생성에 실패했습니다: " + err.message);
        } finally {
            loading.value = false;
        }
    };

    // 부서 정보 수정
    const updateDepartment = async (id, departmentData) => {
        try {
            loading.value = true;
            error.value = null;

            const response = await updateRAGDepartmentAPI(id, departmentData);
            const updatedDepartment = response.data;

            // 로컬 상태 업데이트
            const index = departments.value.findIndex((dept) => dept.id === id);
            if (index !== -1) {
                departments.value[index] = updatedDepartment;
            }

            return updatedDepartment;
        } catch (err) {
            error.value = err.message;
            throw new Error("부서 수정에 실패했습니다: " + err.message);
        } finally {
            loading.value = false;
        }
    };

    // 부서 삭제
    const deleteDepartment = async (id) => {
        try {
            loading.value = true;
            error.value = null;

            await deleteRAGDepartmentAPI(id);

            // 로컬 상태에서 제거
            const index = departments.value.findIndex((dept) => dept.id === id);
            if (index !== -1) {
                departments.value.splice(index, 1);
            }
        } catch (err) {
            error.value = err.message;
            throw new Error("부서 삭제에 실패했습니다: " + err.message);
        } finally {
            loading.value = false;
        }
    };

    // 부서 상태 변경
    const updateDepartmentStatus = async (id, status) => {
        try {
            loading.value = true;
            error.value = null;

            const response = await updateRAGDepartmentStatusAPI(id, status);
            const updatedDepartment = response.data;

            // 로컬 상태 업데이트
            const index = departments.value.findIndex((dept) => dept.id === id);
            if (index !== -1) {
                departments.value[index] = updatedDepartment;
            }

            return updatedDepartment;
        } catch (err) {
            error.value = err.message;
            throw new Error("부서 상태 변경에 실패했습니다: " + err.message);
        } finally {
            loading.value = false;
        }
    };

    // 부서 데이터 로드 (API에서 가져오기)
    const fetchDepartments = async () => {
        try {
            loading.value = true;
            error.value = null;

            const response = await getRAGDepartmentsAPI();
            departments.value = response.data || [];

            return departments.value;
        } catch (err) {
            error.value = err.message;
            console.error("부서 데이터 로드 실패:", err);

            // API 실패 시 빈 배열 사용 (fallback 제거로 DB와 불일치 방지)
            console.warn("API failed, using empty department list to avoid DB mismatch");
            departments.value = [];

            return departments.value;
        } finally {
            loading.value = false;
        }
    };

    // 부서 통계 조회
    const fetchDepartmentStats = async () => {
        try {
            const response = await getRAGDepartmentStatsAPI();
            return response.data;
        } catch (err) {
            console.error("부서 통계 조회 실패:", err);
            throw new Error("부서 통계 조회에 실패했습니다: " + err.message);
        }
    };

    // 에러 초기화
    const clearError = () => {
        error.value = null;
    };

    return {
        // 상태
        departments,
        loading,
        error,

        // 계산된 속성
        filteredDepartments,

        // 메서드
        getDepartmentById,
        getDepartmentByName,
        createDepartment,
        updateDepartment,
        deleteDepartment,
        updateDepartmentStatus,
        fetchDepartments,
        fetchDepartmentStats,
        clearError,
    };
});
