package org.ossrag.meta.controller;

import io.swagger.v3.oas.annotations.security.SecurityRequirement;
import jakarta.validation.Valid;
import org.ossrag.meta.dto.FileUploadRequest;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

import java.nio.charset.StandardCharsets;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;

@RestController
@SecurityRequirement(name = "BearerAuth")
public class FileController {

    // 허용된 파일 확장자 (백엔드 extractAttachmentSnippets와 동일)
    private static final Set<String> ALLOWED_EXTENSIONS = new HashSet<>(java.util.Arrays.asList(
        "txt", "md", "py", "js", "ts", "json", "yaml", "yml", "sh", "bash", "java"
    ));

    // 최대 파일 크기 (10MB)
    private static final long MAX_FILE_SIZE = 10 * 1024 * 1024;

    // 스니펫 크기 제한 (10KB - extractAttachmentSnippets와 동일)
    private static final int SNIPPET_SIZE_LIMIT = 10 * 1024;

    /**
     * 파일 업로드 엔드포인트
     * JSON 페이로드로 파일 내용을 받아서 첫 10KB를 읽어서 content 필드에 반환
     * 
     * @param request 파일 업로드 요청 (filename, content, contentType)
     * @return 업로드 결과 (name, url, content)
     */
    @PostMapping("/upload")
    public ResponseEntity<Map<String, Object>> uploadFile(@Valid @RequestBody FileUploadRequest request) {
        try {
            // 요청 데이터 검증
            if (request == null || request.getFilename() == null || request.getFilename().isEmpty()) {
                Map<String, Object> error = new HashMap<>();
                error.put("code", "BAD_REQUEST");
                error.put("message", "파일명이 없습니다.");
                return ResponseEntity.badRequest().body(error);
            }

            if (request.getContent() == null || request.getContent().isEmpty()) {
                Map<String, Object> error = new HashMap<>();
                error.put("code", "BAD_REQUEST");
                error.put("message", "파일 내용이 비어있습니다.");
                return ResponseEntity.badRequest().body(error);
            }

            String filename = request.getFilename();
            
            // 파일 크기 확인 (UTF-8 문자열의 바이트 길이로 근사치 계산)
            // Base64는 약 33% 오버헤드가 있지만, 텍스트는 UTF-8이므로 실제 바이트 크기로 계산
            byte[] contentBytes = request.getContent().getBytes(StandardCharsets.UTF_8);
            if (contentBytes.length > MAX_FILE_SIZE) {
                Map<String, Object> error = new HashMap<>();
                error.put("code", "BAD_REQUEST");
                error.put("message", "파일 크기는 10MB 이하여야 합니다.");
                return ResponseEntity.badRequest().body(error);
            }

            // 파일 확장자 확인
            String ext = "";
            int dotIndex = filename.lastIndexOf('.');
            if (dotIndex >= 0 && dotIndex < filename.length() - 1) {
                ext = filename.substring(dotIndex + 1).toLowerCase();
            }

            if (!ALLOWED_EXTENSIONS.contains(ext)) {
                Map<String, Object> error = new HashMap<>();
                error.put("code", "BAD_REQUEST");
                error.put("message", "지원하지 않는 파일 형식입니다. (허용: txt, md, py, js, ts, json, yaml, yml, sh, bash, java)");
                return ResponseEntity.badRequest().body(error);
            }

            // 파일 내용 읽기 (최대 10KB 바이트)
            // contentBytes는 이미 위에서 선언되었으므로 재사용
            int byteLength = Math.min(contentBytes.length, SNIPPET_SIZE_LIMIT);
            
            // 바이트 배열을 다시 문자열로 변환 (UTF-8 문자 경계를 고려)
            String contentSnippet;
            if (byteLength < contentBytes.length) {
                // UTF-8 문자 경계를 찾기 위해 바이트 배열을 안전하게 자르기
                // continuation byte (0x80-0xBF)가 아닐 때까지 뒤로 이동
                int safeLength = byteLength;
                while (safeLength > 0 && safeLength < contentBytes.length && 
                       (contentBytes[safeLength] & 0xC0) == 0x80) {
                    safeLength--; // 중간 바이트를 건너뛰기
                }
                contentSnippet = new String(contentBytes, 0, safeLength, StandardCharsets.UTF_8);
            } else {
                contentSnippet = request.getContent();
            }

            // 응답 구성
            Map<String, Object> data = new HashMap<>();
            data.put("name", filename);
            data.put("url", ""); // content 필드 사용 시 url은 비워둠
            data.put("content", contentSnippet);

            Map<String, Object> response = new HashMap<>();
            response.put("data", data);

            return ResponseEntity.ok(response);

        } catch (Exception e) {
            Map<String, Object> error = new HashMap<>();
            error.put("code", "INTERNAL_ERROR");
            error.put("message", "파일 업로드 중 오류가 발생했습니다: " + e.getMessage());
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(error);
        }
    }
}

