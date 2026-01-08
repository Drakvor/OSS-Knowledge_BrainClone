package org.ossrag.meta.domain;

import com.fasterxml.jackson.annotation.JsonFormat;
import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.annotations.UpdateTimestamp;
import org.hibernate.type.SqlTypes;

import java.time.LocalDateTime;
import java.util.List;

@Entity
@Table(name = "rag_departments")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
public class RAGDepartment {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    @Column(unique = true, nullable = false, length = 100)
    private String name;
    
    private String description;
    
    @Column(length = 10)
    private String icon;
    
    @Column(length = 20)
    private String color;
    
    @Column(nullable = false, length = 20)
    private String status;
    
    @JdbcTypeCode(SqlTypes.JSON)
    @Column(columnDefinition = "jsonb")
    private List<String> keywords;
    
    @CreationTimestamp
    @Column(name = "created_at", nullable = false, updatable = false)
    @JsonProperty("created_at")
    @JsonFormat(pattern = "yyyy-MM-dd'T'HH:mm:ss'Z'")
    private LocalDateTime createdAt;
    
    @UpdateTimestamp
    @Column(name = "last_updated", nullable = false)
    @JsonProperty("last_updated")
    @JsonFormat(pattern = "yyyy-MM-dd'T'HH:mm:ss'Z'")
    private LocalDateTime lastUpdated;
    
    @Column(name = "monthly_queries")
    @JsonProperty("monthly_queries")
    private Integer monthlyQueries;

}
