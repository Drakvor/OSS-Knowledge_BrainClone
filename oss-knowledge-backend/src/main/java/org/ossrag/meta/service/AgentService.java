package org.ossrag.meta.service;

import java.util.UUID;
import org.ossrag.meta.domain.Agent;
import org.ossrag.meta.dto.AgentRequest;
import org.ossrag.meta.dto.AgentResponse;
import org.ossrag.meta.dto.PageResponse;
import org.ossrag.meta.repository.AgentRepository;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.web.server.ResponseStatusException;

import java.time.Instant;
import java.util.List;
import java.util.stream.Collectors;

/**
 * 에이전트 서비스.
 */
@Service
public class AgentService {
    private final AgentRepository repository;

    public AgentService(AgentRepository repository) {
        this.repository = repository;
    }

    public PageResponse<AgentResponse> list(int page, int size) {
        Pageable pageable = PageRequest.of(page, size);
        Page<Agent> agentPage = repository.findAll(pageable);
        
        List<AgentResponse> items = agentPage.getContent()
                .stream()
                .map(this::toResponse)
                .collect(Collectors.toList());
        
        return new PageResponse<>(agentPage.getTotalElements(), page, size, items);
    }

    public AgentResponse get(String id) {
        Agent agent = repository.findById(id)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Agent not found"));
        return toResponse(agent);
    }

    public AgentResponse create(AgentRequest request) {
        Agent agent = new Agent();
        agent.setId(UUID.randomUUID().toString());
        agent.setName(request.getName());
        agent.setModel(request.getModel());
        agent.setDescription(request.getDescription());
        agent.setCreatedAt(Instant.now());
        
        Agent savedAgent = repository.save(agent);
        return toResponse(savedAgent);
    }

    public AgentResponse update(String id, AgentRequest request) {
        Agent agent = repository.findById(id)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Agent not found"));
        
        agent.setName(request.getName());
        agent.setModel(request.getModel());
        agent.setDescription(request.getDescription());
        
        Agent updatedAgent = repository.save(agent);
        return toResponse(updatedAgent);
    }

    public void delete(String id) {
        if (!repository.existsById(id)) {
            throw new ResponseStatusException(HttpStatus.NOT_FOUND, "Agent not found");
        }
        repository.deleteById(id);
    }

    private AgentResponse toResponse(Agent agent) {
        AgentResponse res = new AgentResponse();
        res.setId(agent.getId());
        res.setName(agent.getName());
        res.setModel(agent.getModel());
        res.setDescription(agent.getDescription());
        res.setCreatedAt(agent.getCreatedAt());
        return res;
    }
}
