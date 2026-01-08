package org.ossrag.meta.controller;

import io.swagger.v3.oas.annotations.Operation;
import jakarta.validation.Valid;
import org.ossrag.meta.domain.User;
import org.ossrag.meta.dto.LoginRequest;
import org.ossrag.meta.dto.TokenRequest;
import org.ossrag.meta.dto.TokenResponse;
import org.ossrag.meta.service.JwtService;
import org.ossrag.meta.service.UserService;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.time.Instant;
import java.util.HashMap;
import java.util.Map;

/** 인증 컨트롤러 */
@RestController
@RequestMapping("/auth")
@Validated
public class AuthController {

    private final JwtService jwtService;
    private final UserService userService;

    public AuthController(JwtService jwtService, UserService userService) {
        this.jwtService = jwtService;
        this.userService = userService;
    }

    @PostMapping("/login")
    @Operation(summary = "사용자 로그인", description = "사용자명과 비밀번호로 로그인하여 JWT 토큰을 발급합니다.")
    public ResponseEntity<Map<String, Object>> login(@Valid @RequestBody LoginRequest request) {
        try {
            // 사용자 인증
            boolean isValid = userService.authenticateUser(request.getUsername(), request.getPassword());
            
            if (!isValid) {
                Map<String, Object> errorResponse = new HashMap<>();
                errorResponse.put("error", "Invalid username or password");
                return ResponseEntity.status(HttpStatus.UNAUTHORIZED).body(errorResponse);
            }

            // 사용자 정보 조회
            User user = userService.findByUsername(request.getUsername());
            
            // JWT 토큰 발급 (사용자 정보 포함)
            String accessToken = jwtService.generateAccessTokenWithUserInfo(user);
            String refreshToken = jwtService.generateRefreshToken(request.getUsername());
            Instant now = Instant.now();
            
            TokenResponse tokenResponse = new TokenResponse(accessToken, refreshToken,
                    now.plusSeconds(jwtService.getAccessExpMin() * 60),
                    now.plusSeconds(jwtService.getRefreshExpDays() * 86400));

            Map<String, Object> response = new HashMap<>();
            response.put("data", tokenResponse);
            response.put("message", "Login successful");
            
            return ResponseEntity.ok(response);
            
        } catch (Exception e) {
            Map<String, Object> errorResponse = new HashMap<>();
            errorResponse.put("error", e.getMessage());
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(errorResponse);
        }
    }

    @PostMapping("/token")
    @Operation(summary = "JWT 발급 (테스트용)", description = "사용자 ID로 직접 JWT 토큰을 발급합니다.")
    public TokenResponse token(@Valid @RequestBody TokenRequest request) {
        String access = jwtService.generateAccessToken(request.getUserId());
        String refresh = jwtService.generateRefreshToken(request.getUserId());
        Instant now = Instant.now();
        return new TokenResponse(access, refresh,
                now.plusSeconds(jwtService.getAccessExpMin() * 60),
                now.plusSeconds(jwtService.getRefreshExpDays() * 86400));
    }


    // 사용자 정보는 이제 JWT 토큰에 포함되므로 별도 API 불필요
    // @GetMapping("/me") - 제거됨
}
