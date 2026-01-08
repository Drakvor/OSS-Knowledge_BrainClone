package org.ossrag.meta.service;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.client.HttpClientErrorException;
import org.springframework.web.client.ResourceAccessException;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.HashMap;
import java.util.Map;

/**
 * Service for managing Qdrant collections
 * Handles collection lifecycle management (create, delete, status check)
 * Works in coordination with Python embedding backend
 */
@Service
public class QdrantCollectionService {
    
    private static final Logger logger = LoggerFactory.getLogger(QdrantCollectionService.class);
    
    @Value("${embedding.backend.url:http://localhost:8000}")
    private String embeddingBackendUrl;
    
    @Autowired
    private RestTemplate restTemplate;
    
    @Autowired
    private ObjectMapper objectMapper;
    
    /**
     * Create a Qdrant collection for a RAG department
     * 
     * @param departmentName The name of the department (used as collection name)
     * @return true if collection was created successfully, false otherwise
     */
    @SuppressWarnings("unchecked")
    public boolean createCollection(String departmentName) {
        try {
            logger.info("Creating Qdrant collection for department: {}", departmentName);
            
            // Prepare request body
            ObjectNode requestBody = objectMapper.createObjectNode();
            requestBody.put("collection_name", departmentName);
            requestBody.put("vector_size", 3072); // OpenAI text-embedding-3-large embedding size
            requestBody.put("similarity_function", "cosine");
            
            // Prepare headers
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            
            HttpEntity<String> request = new HttpEntity<>(requestBody.toString(), headers);
            
            // Make API call
            String url = embeddingBackendUrl + "/qdrant/collections/create";
            ResponseEntity<Map> response = restTemplate.exchange(
                url, 
                HttpMethod.POST, 
                request, 
                Map.class
            );
            
            if (response.getStatusCode().is2xxSuccessful()) {
                logger.info("Successfully created collection for department: {}", departmentName);
                return true;
            } else {
                logger.warn("Failed to create collection for department: {}. Status: {}", 
                    departmentName, response.getStatusCode());
                return false;
            }
            
        } catch (HttpClientErrorException e) {
            logger.error("HTTP error creating collection for department: {}. Error: {}", 
                departmentName, e.getMessage());
            return false;
        } catch (ResourceAccessException e) {
            logger.error("Connection error creating collection for department: {}. Error: {}", 
                departmentName, e.getMessage());
            return false;
        } catch (Exception e) {
            logger.error("Unexpected error creating collection for department: {}. Error: {}", 
                departmentName, e.getMessage(), e);
            return false;
        }
    }
    
    /**
     * Delete a Qdrant collection for a RAG department
     * 
     * @param departmentName The name of the department (used as collection name)
     * @return true if collection was deleted successfully, false otherwise
     */
    @SuppressWarnings("unchecked")
    public boolean deleteCollection(String departmentName) {
        try {
            logger.info("Deleting Qdrant collection for department: {}", departmentName);
            
            // Prepare headers
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            
            HttpEntity<String> request = new HttpEntity<>(headers);
            
            // Make API call
            String url = embeddingBackendUrl + "/qdrant/collections/" + departmentName;
            ResponseEntity<Map> response = restTemplate.exchange(
                url, 
                HttpMethod.DELETE, 
                request, 
                Map.class
            );
            
            if (response.getStatusCode().is2xxSuccessful()) {
                logger.info("Successfully deleted collection for department: {}", departmentName);
                return true;
            } else {
                logger.warn("Failed to delete collection for department: {}. Status: {}", 
                    departmentName, response.getStatusCode());
                return false;
            }
            
        } catch (HttpClientErrorException e) {
            if (e.getStatusCode().value() == 404) {
                logger.info("Collection for department {} not found, considering deletion successful", departmentName);
                return true; // Collection doesn't exist, consider it deleted
            }
            logger.error("HTTP error deleting collection for department: {}. Error: {}", 
                departmentName, e.getMessage());
            return false;
        } catch (ResourceAccessException e) {
            logger.error("Connection error deleting collection for department: {}. Error: {}", 
                departmentName, e.getMessage());
            return false;
        } catch (Exception e) {
            logger.error("Unexpected error deleting collection for department: {}. Error: {}", 
                departmentName, e.getMessage(), e);
            return false;
        }
    }
    
    /**
     * Check if a collection exists for a department
     * 
     * @param departmentName The name of the department
     * @return true if collection exists, false otherwise
     */
    @SuppressWarnings("unchecked")
    public boolean collectionExists(String departmentName) {
        try {
            logger.debug("Checking if collection exists for department: {}", departmentName);
            
            // Prepare headers
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            
            HttpEntity<String> request = new HttpEntity<>(headers);
            
            // Make API call
            String url = embeddingBackendUrl + "/qdrant/collections/" + departmentName + "/info";
            ResponseEntity<Map> response = restTemplate.exchange(
                url, 
                HttpMethod.GET, 
                request, 
                Map.class
            );
            
            if (response.getStatusCode().is2xxSuccessful()) {
                logger.debug("Collection exists for department: {}", departmentName);
                return true;
            } else {
                logger.debug("Collection does not exist for department: {}", departmentName);
                return false;
            }
            
        } catch (HttpClientErrorException e) {
            if (e.getStatusCode().value() == 404) {
                logger.debug("Collection does not exist for department: {}", departmentName);
                return false;
            }
            logger.error("HTTP error checking collection for department: {}. Error: {}", 
                departmentName, e.getMessage());
            return false;
        } catch (ResourceAccessException e) {
            logger.error("Connection error checking collection for department: {}. Error: {}", 
                departmentName, e.getMessage());
            return false;
        } catch (Exception e) {
            logger.error("Unexpected error checking collection for department: {}. Error: {}", 
                departmentName, e.getMessage(), e);
            return false;
        }
    }
    
    /**
     * Get collection information for a department
     * 
     * @param departmentName The name of the department
     * @return Map containing collection information, or null if not found
     */
    @SuppressWarnings("unchecked")
    public Map<String, Object> getCollectionInfo(String departmentName) {
        try {
            logger.debug("Getting collection info for department: {}", departmentName);
            
            // Prepare headers
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            
            HttpEntity<String> request = new HttpEntity<>(headers);
            
            // Make API call
            String url = embeddingBackendUrl + "/qdrant/collections/" + departmentName + "/info";
            ResponseEntity<Map> response = restTemplate.exchange(
                url, 
                HttpMethod.GET, 
                request, 
                Map.class
            );
            
            if (response.getStatusCode().is2xxSuccessful()) {
                logger.debug("Retrieved collection info for department: {}", departmentName);
                return response.getBody();
            } else {
                logger.warn("Failed to get collection info for department: {}. Status: {}", 
                    departmentName, response.getStatusCode());
                return null;
            }
            
        } catch (HttpClientErrorException e) {
            if (e.getStatusCode().value() == 404) {
                logger.debug("Collection info not found for department: {}", departmentName);
                return null;
            }
            logger.error("HTTP error getting collection info for department: {}. Error: {}", 
                departmentName, e.getMessage());
            return null;
        } catch (ResourceAccessException e) {
            logger.error("Connection error getting collection info for department: {}. Error: {}", 
                departmentName, e.getMessage());
            return null;
        } catch (Exception e) {
            logger.error("Unexpected error getting collection info for department: {}. Error: {}", 
                departmentName, e.getMessage(), e);
            return null;
        }
    }
    
    /**
     * List all collections
     * 
     * @return Map containing list of collections, or null if error
     */
    @SuppressWarnings("unchecked")
    public Map<String, Object> listCollections() {
        try {
            logger.debug("Listing all collections");
            
            // Prepare headers
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            
            HttpEntity<String> request = new HttpEntity<>(headers);
            
            // Make API call
            String url = embeddingBackendUrl + "/qdrant/collections/list";
            ResponseEntity<Map> response = restTemplate.exchange(
                url, 
                HttpMethod.GET, 
                request, 
                Map.class
            );
            
            if (response.getStatusCode().is2xxSuccessful()) {
                logger.debug("Retrieved collections list");
                return response.getBody();
            } else {
                logger.warn("Failed to list collections. Status: {}", response.getStatusCode());
                return null;
            }
            
        } catch (HttpClientErrorException e) {
            logger.error("HTTP error listing collections. Error: {}", e.getMessage());
            return null;
        } catch (ResourceAccessException e) {
            logger.error("Connection error listing collections. Error: {}", e.getMessage());
            return null;
        } catch (Exception e) {
            logger.error("Unexpected error listing collections. Error: {}", e.getMessage(), e);
            return null;
        }
    }
}
