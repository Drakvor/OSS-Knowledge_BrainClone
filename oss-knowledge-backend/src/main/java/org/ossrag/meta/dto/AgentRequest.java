package org.ossrag.meta.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.Getter;
import lombok.Setter;

/**
 * 에이전트 생성/수정 요청.
 */
@Getter
@Setter
public class AgentRequest {
    @NotBlank
    private String name;
    @NotBlank
    private String model;
    private String description;
}
