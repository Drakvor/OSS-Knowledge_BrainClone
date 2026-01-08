package org.ossrag.meta.dto;

import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.time.Instant;

/**
 * 에이전트 응답.
 */
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
public class AgentResponse {
    private String id;
    private String name;
    private String model;
    private String description;
    private Instant createdAt;
}
