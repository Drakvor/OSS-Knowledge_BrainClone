package org.ossrag.meta.domain;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import org.hibernate.annotations.CreationTimestamp;

import java.time.Instant;

/**
 * 에이전트 엔터티.
 */
@Entity
@Table(name = "agents")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
public class Agent {
    @Id
    @Column(length = 26)
    private String id;
    
    @Column(nullable = false)
    private String name;
    
    @Column(nullable = false)
    private String model;
    
    private String description;
    
    @CreationTimestamp
    @Column(name = "created_at", nullable = false, updatable = false)
    private Instant createdAt;

}
