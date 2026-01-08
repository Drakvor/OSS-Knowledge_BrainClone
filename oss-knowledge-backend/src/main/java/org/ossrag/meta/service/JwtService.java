package org.ossrag.meta.service;

import io.jsonwebtoken.JwtException;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.Date;
import java.util.Optional;
import javax.crypto.SecretKey;
import org.ossrag.meta.domain.User;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

/** JWT 생성/검증 */
@Service
public class JwtService {

    private static final Logger logger = LoggerFactory.getLogger(JwtService.class);
    private final SecretKey key;
    private final long accessExpMin;
    private final long refreshExpDays;

    public JwtService(
            @Value("${security.jwt.secret}") String secret,
            @Value("${security.jwt.access-exp-min:15}") long accessExpMin,
            @Value("${security.jwt.refresh-exp-days:7}") long refreshExpDays) {
        this.key = Keys.hmacShaKeyFor(secret.getBytes(StandardCharsets.UTF_8));
        this.accessExpMin = accessExpMin;
        this.refreshExpDays = refreshExpDays;
    }

    public String generateAccessToken(String userId) {
        Instant now = Instant.now();
        return Jwts.builder()
                .setSubject(userId)
                .setIssuedAt(Date.from(now))
                .setExpiration(Date.from(now.plusSeconds(accessExpMin * 60)))
                .signWith(key)
                .compact();
    }

    public String generateAccessTokenWithUserInfo(User user) {
        Instant now = Instant.now();
        return Jwts.builder()
                .setSubject(user.getUsername())
                .claim("userId", user.getId())
                .claim("email", user.getEmail())
                .claim("fullName", user.getFullName())
                .claim("role", user.getRole())
                .claim("status", user.getStatus())
                .setIssuedAt(Date.from(now))
                .setExpiration(Date.from(now.plusSeconds(accessExpMin * 60)))
                .signWith(key)
                .compact();
    }

    public String generateRefreshToken(String userId) {
        Instant now = Instant.now();
        return Jwts.builder()
                .setSubject(userId)
                .setIssuedAt(Date.from(now))
                .setExpiration(Date.from(now.plusSeconds(refreshExpDays * 86400)))
                .signWith(key)
                .compact();
    }

    public boolean validate(String token) {
        try {
            Jwts.parserBuilder().setSigningKey(key).build().parseClaimsJws(token);
            return true;
        } catch (JwtException | IllegalArgumentException e) {
            logger.debug("JWT token validation failed: {}", e.getMessage());
            return false;
        }
    }

    public Optional<String> extractSubject(String token) {
        try {
            return Optional.ofNullable(
                    Jwts.parserBuilder().setSigningKey(key).build()
                            .parseClaimsJws(token).getBody().getSubject());
        } catch (JwtException | IllegalArgumentException e) {
            return Optional.empty();
        }
    }

    public long getAccessExpMin() {
        return accessExpMin;
    }

    public long getRefreshExpDays() {
        return refreshExpDays;
    }
}
