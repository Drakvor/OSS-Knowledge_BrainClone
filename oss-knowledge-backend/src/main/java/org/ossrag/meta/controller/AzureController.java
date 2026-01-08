package org.ossrag.meta.controller;

import io.swagger.v3.oas.annotations.security.SecurityRequirement;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

import java.util.HashMap;
import java.util.Map;

@RestController
@SecurityRequirement(name = "BearerAuth")
public class AzureController {
    @GetMapping("/azure/connection-status")
    public Map<String, Object> status() {
        Map<String, Object> res = new HashMap<>();
        res.put("connected", false);
        res.put("message", "Azure File Share not configured");
        return res;
    }

    @PostMapping("/azure/sync")
    @ResponseStatus(HttpStatus.OK)
    public Map<String, Object> sync() {
        Map<String, Object> res = new HashMap<>();
        res.put("status", "queued");
        return res;
    }
}
