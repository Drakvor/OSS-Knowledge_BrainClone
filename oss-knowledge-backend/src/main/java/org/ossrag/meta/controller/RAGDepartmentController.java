package org.ossrag.meta.controller;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import io.swagger.v3.oas.annotations.security.SecurityRequirement;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.ossrag.meta.dto.RAGDepartmentRequest;
import org.ossrag.meta.dto.RAGDepartmentResponse;
import org.ossrag.meta.service.RAGDepartmentService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/rag-departments")
@SecurityRequirement(name = "BearerAuth")
@Validated
@Tag(name = "RAG Department Management", description = "RAG 부서 관리 API")
public class RAGDepartmentController {
    
    private static final Logger logger = LoggerFactory.getLogger(RAGDepartmentController.class);
    private final RAGDepartmentService ragDepartmentService;

    public RAGDepartmentController(RAGDepartmentService ragDepartmentService) {
        this.ragDepartmentService = ragDepartmentService;
    }

    @GetMapping
    @Operation(summary = "모든 RAG 부서 조회", description = "등록된 모든 RAG 부서 목록을 조회합니다.")
    @ApiResponses(value = {
        @ApiResponse(responseCode = "200", description = "성공적으로 조회됨"),
        @ApiResponse(responseCode = "500", description = "서버 오류")
    })
    public ResponseEntity<Map<String, Object>> getAllDepartments() {
        try {
            logger.info("Retrieving all RAG departments");
            List<RAGDepartmentResponse> departments = ragDepartmentService.getAllDepartments();
            Map<String, Object> response = new HashMap<>();
            response.put("data", departments);
            response.put("total", departments.size());
            logger.info("Successfully retrieved {} RAG departments", departments.size());
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            logger.error("Failed to retrieve RAG departments: {}", e.getMessage(), e);
            Map<String, Object> errorResponse = new HashMap<>();
            errorResponse.put("error", e.getMessage());
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(errorResponse);
        }
    }

    @GetMapping("/{id}")
    @Operation(summary = "RAG 부서 상세 조회", description = "ID로 특정 RAG 부서의 상세 정보를 조회합니다.")
    @ApiResponses(value = {
        @ApiResponse(responseCode = "200", description = "성공적으로 조회됨"),
        @ApiResponse(responseCode = "404", description = "부서를 찾을 수 없음"),
        @ApiResponse(responseCode = "500", description = "서버 오류")
    })
    public ResponseEntity<Map<String, Object>> getDepartmentById(
            @Parameter(description = "부서 ID") @PathVariable Long id) {
        try {
            RAGDepartmentResponse department = ragDepartmentService.getDepartmentById(id);
            Map<String, Object> response = new HashMap<>();
            response.put("data", department);
            return ResponseEntity.ok(response);
        } catch (RuntimeException e) {
            Map<String, Object> errorResponse = new HashMap<>();
            errorResponse.put("error", e.getMessage());
            return ResponseEntity.status(HttpStatus.NOT_FOUND).body(errorResponse);
        } catch (Exception e) {
            Map<String, Object> errorResponse = new HashMap<>();
            errorResponse.put("error", e.getMessage());
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(errorResponse);
        }
    }

    @PostMapping
    @Operation(summary = "새 RAG 부서 생성", description = "새로운 RAG 부서를 생성합니다.")
    @ApiResponses(value = {
        @ApiResponse(responseCode = "201", description = "성공적으로 생성됨"),
        @ApiResponse(responseCode = "400", description = "잘못된 요청"),
        @ApiResponse(responseCode = "409", description = "이미 존재하는 부서명"),
        @ApiResponse(responseCode = "500", description = "서버 오류")
    })
    public ResponseEntity<Map<String, Object>> createDepartment(
            @Parameter(description = "부서 생성 정보") @RequestBody RAGDepartmentRequest request) {
        try {
            RAGDepartmentResponse department = ragDepartmentService.createDepartment(request);
            Map<String, Object> response = new HashMap<>();
            response.put("data", department);
            response.put("message", "Department created successfully");
            return ResponseEntity.status(HttpStatus.CREATED).body(response);
        } catch (RuntimeException e) {
            Map<String, Object> errorResponse = new HashMap<>();
            errorResponse.put("error", e.getMessage());
            HttpStatus status = e.getMessage().contains("already exists") ? HttpStatus.CONFLICT : HttpStatus.BAD_REQUEST;
            return ResponseEntity.status(status).body(errorResponse);
        } catch (Exception e) {
            Map<String, Object> errorResponse = new HashMap<>();
            errorResponse.put("error", e.getMessage());
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(errorResponse);
        }
    }

    @PutMapping("/{id}")
    @Operation(summary = "RAG 부서 수정", description = "기존 RAG 부서의 정보를 수정합니다.")
    @ApiResponses(value = {
        @ApiResponse(responseCode = "200", description = "성공적으로 수정됨"),
        @ApiResponse(responseCode = "404", description = "부서를 찾을 수 없음"),
        @ApiResponse(responseCode = "409", description = "이미 존재하는 부서명"),
        @ApiResponse(responseCode = "500", description = "서버 오류")
    })
    public ResponseEntity<Map<String, Object>> updateDepartment(
            @Parameter(description = "부서 ID") @PathVariable Long id,
            @Parameter(description = "부서 수정 정보") @RequestBody RAGDepartmentRequest request) {
        try {
            RAGDepartmentResponse department = ragDepartmentService.updateDepartment(id, request);
            Map<String, Object> response = new HashMap<>();
            response.put("data", department);
            response.put("message", "Department updated successfully");
            return ResponseEntity.ok(response);
        } catch (RuntimeException e) {
            Map<String, Object> errorResponse = new HashMap<>();
            errorResponse.put("error", e.getMessage());
            HttpStatus status;
            if (e.getMessage().contains("not found")) {
                status = HttpStatus.NOT_FOUND;
            } else if (e.getMessage().contains("already exists")) {
                status = HttpStatus.CONFLICT;
            } else {
                status = HttpStatus.BAD_REQUEST;
            }
            return ResponseEntity.status(status).body(errorResponse);
        } catch (Exception e) {
            Map<String, Object> errorResponse = new HashMap<>();
            errorResponse.put("error", e.getMessage());
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(errorResponse);
        }
    }

    @DeleteMapping("/{id}")
    @Operation(summary = "RAG 부서 삭제", description = "특정 RAG 부서를 삭제합니다.")
    @ApiResponses(value = {
        @ApiResponse(responseCode = "200", description = "성공적으로 삭제됨"),
        @ApiResponse(responseCode = "404", description = "부서를 찾을 수 없음"),
        @ApiResponse(responseCode = "500", description = "서버 오류")
    })
    public ResponseEntity<Map<String, Object>> deleteDepartment(
            @Parameter(description = "부서 ID") @PathVariable Long id) {
        try {
            ragDepartmentService.deleteDepartment(id);
            Map<String, Object> response = new HashMap<>();
            response.put("message", "Department deleted successfully");
            return ResponseEntity.ok(response);
        } catch (RuntimeException e) {
            Map<String, Object> errorResponse = new HashMap<>();
            errorResponse.put("error", e.getMessage());
            return ResponseEntity.status(HttpStatus.NOT_FOUND).body(errorResponse);
        } catch (Exception e) {
            Map<String, Object> errorResponse = new HashMap<>();
            errorResponse.put("error", e.getMessage());
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(errorResponse);
        }
    }

    @PatchMapping("/{id}/status")
    @Operation(summary = "RAG 부서 상태 변경", description = "특정 RAG 부서의 상태를 변경합니다.")
    @ApiResponses(value = {
        @ApiResponse(responseCode = "200", description = "성공적으로 상태 변경됨"),
        @ApiResponse(responseCode = "404", description = "부서를 찾을 수 없음"),
        @ApiResponse(responseCode = "500", description = "서버 오류")
    })
    public ResponseEntity<Map<String, Object>> updateDepartmentStatus(
            @Parameter(description = "부서 ID") @PathVariable Long id,
            @Parameter(description = "상태 변경 요청") @RequestBody Map<String, String> request) {
        String status = request.get("status");
        if (status == null || status.trim().isEmpty()) {
            Map<String, Object> errorResponse = new HashMap<>();
            errorResponse.put("error", "Status parameter is required");
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(errorResponse);
        }
        
        try {
            RAGDepartmentResponse department = ragDepartmentService.updateDepartmentStatus(id, status);
            Map<String, Object> response = new HashMap<>();
            response.put("data", department);
            response.put("message", "Department status updated successfully");
            return ResponseEntity.ok(response);
        } catch (RuntimeException e) {
            Map<String, Object> errorResponse = new HashMap<>();
            errorResponse.put("error", e.getMessage());
            return ResponseEntity.status(HttpStatus.NOT_FOUND).body(errorResponse);
        } catch (Exception e) {
            Map<String, Object> errorResponse = new HashMap<>();
            errorResponse.put("error", e.getMessage());
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(errorResponse);
        }
    }

    @GetMapping("/stats")
    @Operation(summary = "RAG 부서 통계 조회", description = "RAG 부서들의 통계 정보를 조회합니다.")
    @ApiResponses(value = {
        @ApiResponse(responseCode = "200", description = "성공적으로 조회됨"),
        @ApiResponse(responseCode = "500", description = "서버 오류")
    })
    public ResponseEntity<Map<String, Object>> getDepartmentStats() {
        try {
            Map<String, Object> stats = new HashMap<>();
            stats.put("totalDepartments", ragDepartmentService.getAllDepartments().size());
            stats.put("activeDepartments", ragDepartmentService.getActiveDepartmentsCount());
            stats.put("totalMonthlyQueries", ragDepartmentService.getTotalMonthlyQueries());
            
            Map<String, Object> response = new HashMap<>();
            response.put("data", stats);
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            Map<String, Object> errorResponse = new HashMap<>();
            errorResponse.put("error", e.getMessage());
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(errorResponse);
        }
    }
}
