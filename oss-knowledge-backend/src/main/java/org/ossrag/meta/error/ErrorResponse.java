package org.ossrag.meta.error;

import com.fasterxml.jackson.annotation.JsonInclude;

/**
 * 오류 응답.
 */
@JsonInclude(JsonInclude.Include.NON_NULL)
public class ErrorResponse {
    private final String code;
    private final String message;
    private final Object details;
    private final String traceId;

    public ErrorResponse(String code, String message, Object details, String traceId) {
        this.code = code;
        this.message = message;
        this.details = details;
        this.traceId = traceId;
    }

    public String getCode() {
        return code;
    }

    public String getMessage() {
        return message;
    }

    public Object getDetails() {
        return details;
    }

    public String getTraceId() {
        return traceId;
    }
}
