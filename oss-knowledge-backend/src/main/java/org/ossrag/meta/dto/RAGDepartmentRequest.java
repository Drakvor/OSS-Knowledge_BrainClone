package org.ossrag.meta.dto;

import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.util.List;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
public class RAGDepartmentRequest {
    private String name;
    private String description;
    private String icon;
    private String color;
    private String status;
    private List<String> keywords;
}
