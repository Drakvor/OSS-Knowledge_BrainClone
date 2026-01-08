package org.ossrag.meta.dto;

import jakarta.validation.constraints.NotBlank;

/**
 * 파일 업로드 요청 DTO
 * JSON 페이로드로 파일 내용을 받음
 */
public class FileUploadRequest {
    @NotBlank(message = "파일명은 필수입니다")
    private String filename;
    
    @NotBlank(message = "파일 내용은 필수입니다")
    private String content;
    
    private String contentType;

    public FileUploadRequest() {}

    public FileUploadRequest(String filename, String content, String contentType) {
        this.filename = filename;
        this.content = content;
        this.contentType = contentType;
    }

    public String getFilename() {
        return filename;
    }

    public void setFilename(String filename) {
        this.filename = filename;
    }

    public String getContent() {
        return content;
    }

    public void setContent(String content) {
        this.content = content;
    }

    public String getContentType() {
        return contentType;
    }

    public void setContentType(String contentType) {
        this.contentType = contentType;
    }
}

