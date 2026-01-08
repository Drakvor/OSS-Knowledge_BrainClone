# syntax=docker/dockerfile:1

# Build stage: Maven 3.9.10 with JDK 21
FROM maven:3.9.10-eclipse-temurin-21 AS build
WORKDIR /workspace

# Copy only the files needed to build (improves layer caching)
COPY pom.xml ./
RUN mvn -B -q -DskipTests dependency:go-offline
COPY src ./src

# Build the Spring Boot fat JAR (skip tests in container build)
RUN mvn -B -q -DskipTests clean package


# Runtime stage: JRE 21 (Debian-based for compatibility)
FROM eclipse-temurin:21-jre AS runtime

# Ensure consistent encoding and UTC timestamps
ENV JAVA_TOOL_OPTIONS="-Dfile.encoding=UTF-8 -Duser.timezone=UTC -XX:MaxRAMPercentage=75.0"

WORKDIR /app

# Create non-root user and own the workdir
RUN useradd -r -u 10001 -g 0 app \
    && chown -R 10001:0 /app

# Copy the built application JAR
# Note: artifactId is ossrag-meta-api (from pom.xml)
COPY --from=build /workspace/target/ossrag-meta-api-*.jar /app/app.jar

EXPOSE 8080
USER 10001:0

ENTRYPOINT ["java","-jar","/app/app.jar"]

