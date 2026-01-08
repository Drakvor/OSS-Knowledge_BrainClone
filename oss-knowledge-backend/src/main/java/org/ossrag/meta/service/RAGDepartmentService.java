package org.ossrag.meta.service;

import org.ossrag.meta.domain.RAGDepartment;
import org.ossrag.meta.dto.RAGDepartmentRequest;
import org.ossrag.meta.dto.RAGDepartmentResponse;
import org.ossrag.meta.repository.RAGDepartmentRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;
import java.util.stream.Collectors;

@Service
public class RAGDepartmentService {
    
    private final RAGDepartmentRepository repository;
    private final QdrantCollectionService qdrantCollectionService;

    public RAGDepartmentService(RAGDepartmentRepository repository, 
                               QdrantCollectionService qdrantCollectionService) {
        this.repository = repository;
        this.qdrantCollectionService = qdrantCollectionService;
    }

    public List<RAGDepartmentResponse> getAllDepartments() {
        List<RAGDepartment> departments = repository.findAll();
        return departments.stream()
                .map(this::convertToResponse)
                .collect(Collectors.toList());
    }

    public RAGDepartmentResponse getDepartmentById(Long id) {
        RAGDepartment department = repository.findById(id)
                .orElseThrow(() -> new RuntimeException("Department not found with id: " + id));
        return convertToResponse(department);
    }

    public RAGDepartmentResponse getDepartmentByName(String name) {
        RAGDepartment department = repository.findByName(name)
                .orElseThrow(() -> new RuntimeException("Department not found with name: " + name));
        return convertToResponse(department);
    }

    @Transactional
    public RAGDepartmentResponse createDepartment(RAGDepartmentRequest request) {
        // 이름 중복 체크
        if (repository.existsByName(request.getName())) {
            throw new RuntimeException("Department with name '" + request.getName() + "' already exists");
        }

        RAGDepartment department = convertToDomain(request);
        department.setCreatedAt(LocalDateTime.now());
        department.setLastUpdated(LocalDateTime.now());
        department.setMonthlyQueries(0);

        RAGDepartment savedDepartment = repository.save(department);

        // Qdrant 컬렉션 생성
        try {
            boolean collectionCreated = qdrantCollectionService.createCollection(department.getName());
            if (!collectionCreated) {
                // 컬렉션 생성 실패 시 로그만 남기고 계속 진행 (PostgreSQL은 이미 저장됨)
                System.err.println("Warning: Failed to create Qdrant collection for department: " + department.getName());
            }
        } catch (Exception e) {
            // 컬렉션 생성 실패 시 로그만 남기고 계속 진행
            System.err.println("Warning: Exception while creating Qdrant collection for department: " + department.getName() + ". Error: " + e.getMessage());
        }

        return convertToResponse(savedDepartment);
    }

    public RAGDepartmentResponse updateDepartment(Long id, RAGDepartmentRequest request) {
        RAGDepartment existingDepartment = repository.findById(id)
                .orElseThrow(() -> new RuntimeException("Department not found with id: " + id));

        // 이름 중복 체크 (자기 자신 제외)
        repository.findByName(request.getName())
                .ifPresent(departmentWithSameName -> {
                    if (!departmentWithSameName.getId().equals(id)) {
                        throw new RuntimeException("Department with name '" + request.getName() + "' already exists");
                    }
                });

        RAGDepartment department = convertToDomain(request);
        department.setId(id);
        department.setCreatedAt(existingDepartment.getCreatedAt());
        department.setLastUpdated(LocalDateTime.now());
        department.setMonthlyQueries(existingDepartment.getMonthlyQueries());

        RAGDepartment updatedDepartment = repository.save(department);
        return convertToResponse(updatedDepartment);
    }

    @Transactional
    public void deleteDepartment(Long id) {
        RAGDepartment department = repository.findById(id)
                .orElseThrow(() -> new RuntimeException("Department not found with id: " + id));

        // Qdrant 컬렉션 삭제 (PostgreSQL 삭제 전에 먼저 실행)
        try {
            boolean collectionDeleted = qdrantCollectionService.deleteCollection(department.getName());
            if (!collectionDeleted) {
                // 컬렉션 삭제 실패 시 로그만 남기고 계속 진행
                System.err.println("Warning: Failed to delete Qdrant collection for department: " + department.getName());
            }
        } catch (Exception e) {
            // 컬렉션 삭제 실패 시 로그만 남기고 계속 진행
            System.err.println("Warning: Exception while deleting Qdrant collection for department: " + department.getName() + ". Error: " + e.getMessage());
        }

        repository.deleteById(id);
    }

    public RAGDepartmentResponse updateDepartmentStatus(Long id, String status) {
        RAGDepartment department = repository.findById(id)
                .orElseThrow(() -> new RuntimeException("Department not found with id: " + id));

        department.setStatus(status);
        department.setLastUpdated(LocalDateTime.now());
        
        RAGDepartment updatedDepartment = repository.save(department);
        return convertToResponse(updatedDepartment);
    }

    public int getActiveDepartmentsCount() {
        return repository.findByStatus("active").size();
    }

    public Integer getTotalMonthlyQueries() {
        return repository.findAll().stream()
                .mapToInt(department -> department.getMonthlyQueries() != null ? department.getMonthlyQueries() : 0)
                .sum();
    }

    private RAGDepartmentResponse convertToResponse(RAGDepartment department) {
        return new RAGDepartmentResponse(
                department.getId(),
                department.getName(),
                department.getDescription(),
                department.getIcon(),
                department.getColor(),
                department.getStatus(),
                department.getKeywords(),
                department.getCreatedAt(),
                department.getLastUpdated(),
                department.getMonthlyQueries()
        );
    }

    private RAGDepartment convertToDomain(RAGDepartmentRequest request) {
        RAGDepartment department = new RAGDepartment();
        department.setName(request.getName());
        department.setDescription(request.getDescription());
        department.setIcon(request.getIcon());
        department.setColor(request.getColor());
        department.setStatus(request.getStatus());
        department.setKeywords(request.getKeywords());
        return department;
    }
}
