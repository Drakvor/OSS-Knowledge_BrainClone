package org.ossrag.meta.repository;

import org.ossrag.meta.domain.RAGDepartment;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface RAGDepartmentRepository extends JpaRepository<RAGDepartment, Long> {
    Optional<RAGDepartment> findByName(String name);
    List<RAGDepartment> findByStatus(String status);
    Page<RAGDepartment> findByStatus(String status, Pageable pageable);
    boolean existsByName(String name);
}
