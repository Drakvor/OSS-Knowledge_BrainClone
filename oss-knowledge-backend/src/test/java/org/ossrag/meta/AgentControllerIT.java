package org.ossrag.meta;

import static io.restassured.RestAssured.given;
import static org.hamcrest.Matchers.*;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.server.LocalServerPort;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.testcontainers.containers.PostgreSQLContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;

import org.ossrag.meta.service.JwtService;

@Testcontainers(disabledWithoutDocker = true)
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
class AgentControllerIT {

    @Container
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:16-alpine");

    @DynamicPropertySource
    static void datasourceProps(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", postgres::getJdbcUrl);
        registry.add("spring.datasource.username", postgres::getUsername);
        registry.add("spring.datasource.password", postgres::getPassword);
        registry.add("security.api-key", () -> "test");
        registry.add("security.jwt.secret", () -> "0123456789abcdef0123456789abcdef");
    }

    @LocalServerPort
    int port;

    @Autowired
    JwtService jwtService;

    @Autowired
    JdbcTemplate jdbcTemplate;

    String token;

    @BeforeEach
    void setup() {
        jdbcTemplate.execute("TRUNCATE TABLE agents");
        token = jwtService.generateAccessToken("tester");
    }

    @Test
    void listAgents_empty() {
        given().port(port)
                .header("Authorization", "Bearer " + token)
                .get("/agents")
                .then()
                .statusCode(200)
                .body("total", equalTo(0))
                .body("items.size()", equalTo(0));
    }

    @Test
    void createAndGetAgent() {
        String id = given().port(port)
                .header("Authorization", "Bearer " + token)
                .contentType("application/json")
                .body("{\"name\":\"a1\",\"model\":\"gpt-4\"}")
                .post("/agents")
                .then()
                .statusCode(201)
                .body("name", equalTo("a1"))
                .extract().path("id");

        given().port(port)
                .header("Authorization", "Bearer " + token)
                .get("/agents/" + id)
                .then()
                .statusCode(200)
                .body("id", equalTo(id));
    }

    @Test
    void createAgent_validationError() {
        given().port(port)
                .header("Authorization", "Bearer " + token)
                .contentType("application/json")
                .body("{\"model\":\"gpt-4\"}")
                .post("/agents")
                .then()
                .statusCode(400);
    }

    @Test
    void getAgent_notFound() {
        given().port(port)
                .header("Authorization", "Bearer " + token)
                .get("/agents/01HZX4N3ABCD1234567XYZ999")
                .then()
                .statusCode(404);
    }
}
