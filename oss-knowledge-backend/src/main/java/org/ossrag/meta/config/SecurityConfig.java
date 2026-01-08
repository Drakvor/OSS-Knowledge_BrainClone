package org.ossrag.meta.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.annotation.web.configurers.AbstractHttpConfigurer;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;
import org.springframework.security.web.util.matcher.AntPathRequestMatcher;
import org.springframework.web.cors.CorsConfiguration;
import org.springframework.web.cors.CorsConfigurationSource;
import org.springframework.web.cors.UrlBasedCorsConfigurationSource;

import java.util.Arrays;

@Configuration
@EnableWebSecurity
public class SecurityConfig {

    private final JwtAuthFilter jwtAuthFilter;

    public SecurityConfig(JwtAuthFilter jwtAuthFilter) {
        this.jwtAuthFilter = jwtAuthFilter;
    }

    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }

    @Bean
    public CorsConfigurationSource corsConfigurationSource() {
        CorsConfiguration configuration = new CorsConfiguration();
        // Use origin patterns instead of "*" to work with allowCredentials(true)
        configuration.setAllowedOriginPatterns(Arrays.asList(
            "http://localhost:*",
            "http://*.4.230.158.187.nip.io",
            "https://*.4.230.158.187.nip.io"
        ));
        configuration.setAllowedMethods(Arrays.asList("GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"));
        configuration.setAllowedHeaders(Arrays.asList("*"));
        configuration.setAllowCredentials(true);
        configuration.setMaxAge(3600L);
        
        UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();
        source.registerCorsConfiguration("/**", configuration);
        return source;
    }

    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        http
            .csrf(AbstractHttpConfigurer::disable)
            .cors(cors -> cors.configurationSource(corsConfigurationSource()))
            .authorizeHttpRequests(authz -> authz
                // Public endpoints - use AntPathRequestMatcher to avoid MvcRequestMatcher introspection issues
                .requestMatchers(
                    new AntPathRequestMatcher("/auth/**"),
                    new AntPathRequestMatcher("/health"),
                    new AntPathRequestMatcher("/healthz"),
                    new AntPathRequestMatcher("/api-docs/**"),
                    new AntPathRequestMatcher("/swagger-ui/**"),
                    new AntPathRequestMatcher("/documents/add-after-embedding"),
                    // Allow SSE chat streaming endpoint
                    new AntPathRequestMatcher("/chat/search-engine"),
                    // Allow error page to avoid PatternParseException
                    new AntPathRequestMatcher("/error"),
                    // Note: /chat/sessions/** endpoints are handled by JwtAuthFilter.shouldNotFilter()
                    // to avoid Spring Security pattern parsing issues with error pages
                    new AntPathRequestMatcher("/chat/sessions/**")
                ).permitAll()
                // Allow preflight
                .requestMatchers(org.springframework.http.HttpMethod.OPTIONS, "/**").permitAll()
                .anyRequest().authenticated()
            )
            .httpBasic(AbstractHttpConfigurer::disable)
            .formLogin(AbstractHttpConfigurer::disable)
            .addFilterBefore(jwtAuthFilter, UsernamePasswordAuthenticationFilter.class);

        return http.build();
    }
}
