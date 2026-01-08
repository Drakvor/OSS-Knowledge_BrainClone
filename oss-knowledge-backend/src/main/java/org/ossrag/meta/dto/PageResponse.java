package org.ossrag.meta.dto;

import lombok.AllArgsConstructor;
import lombok.Getter;

import java.util.List;

/**
 * 페이지 응답.
 */
@Getter
@AllArgsConstructor
public class PageResponse<T> {
    private long total;
    private int page;
    private int size;
    private List<T> items;
}
