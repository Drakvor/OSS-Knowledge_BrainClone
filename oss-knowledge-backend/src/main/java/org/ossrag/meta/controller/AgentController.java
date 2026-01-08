package org.ossrag.meta.controller;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.security.SecurityRequirement;
import jakarta.validation.Valid;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import org.ossrag.meta.dto.AgentRequest;
import org.ossrag.meta.dto.AgentResponse;
import org.ossrag.meta.dto.PageResponse;
import org.ossrag.meta.service.AgentService;
import org.springframework.http.HttpStatus;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;

/**
 * 에이전트 컨트롤러.
 */
@RestController
@RequestMapping("/agents")
@SecurityRequirement(name = "BearerAuth")
@Validated
public class AgentController {
    private final AgentService service;

    public AgentController(AgentService service) {
        this.service = service;
    }

    @GetMapping
    @Operation(summary = "에이전트 목록 조회")
    public PageResponse<AgentResponse> list(
            @RequestHeader(value = "X-Request-Id", required = false) String requestId,
            @Min(0) @RequestParam(defaultValue = "0") int page,
            @Min(1) @RequestParam(defaultValue = "20") int size) {
        return service.list(page, size);
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    @Operation(summary = "에이전트 생성")
    public AgentResponse create(
            @RequestHeader(value = "X-Request-Id", required = false) String requestId,
            @Valid @RequestBody AgentRequest request) {
        return service.create(request);
    }

    @GetMapping("/{agentId}")
    @Operation(summary = "에이전트 조회")
    public AgentResponse get(
            @RequestHeader(value = "X-Request-Id", required = false) String requestId,
            @NotBlank @PathVariable String agentId) {
        return service.get(agentId);
    }

    @PutMapping("/{agentId}")
    @Operation(summary = "에이전트 수정")
    public AgentResponse update(
            @RequestHeader(value = "X-Request-Id", required = false) String requestId,
            @NotBlank @PathVariable String agentId,
            @Valid @RequestBody AgentRequest request) {
        return service.update(agentId, request);
    }

    @DeleteMapping("/{agentId}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    @Operation(summary = "에이전트 삭제")
    public void delete(
            @RequestHeader(value = "X-Request-Id", required = false) String requestId,
            @NotBlank @PathVariable String agentId) {
        service.delete(agentId);
    }
}
