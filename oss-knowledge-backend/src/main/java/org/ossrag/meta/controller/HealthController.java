package org.ossrag.meta.controller;

import java.time.Instant;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class HealthController {
    @GetMapping("/healthz")
    public ResponseEntity<Instant> health() {
        return ResponseEntity.ok(Instant.now());
    }

    @GetMapping("/health")
    public ResponseEntity<?> healthSimple() {
        return ResponseEntity.ok(java.util.Map.of("status", "ok", "time", Instant.now().toString()));
    }
}
