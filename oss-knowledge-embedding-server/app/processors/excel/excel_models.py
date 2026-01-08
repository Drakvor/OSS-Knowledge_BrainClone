"""
Excel-Specific Processing Models
Models for Excel file processing options and results
"""

from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, field_validator
from enum import Enum

from app.processors.base.base_models import BaseProcessingOptions, ChunkingStrategy


# ===== EXCEL-SPECIFIC ENUMS =====

class ExcelChunkingStrategy(str, Enum):
    """Excel-specific chunking strategies"""
    ROW_BASED = "row_based"  # Group by rows (default)
    COLUMN_BASED = "column_based"  # Group by columns


# ===== EXCEL PROCESSING OPTIONS =====

class ExcelProcessingOptions(BaseProcessingOptions):
    """Excel-specific processing options"""
    
    # Excel-specific chunking
    chunking_strategy: ExcelChunkingStrategy = ExcelChunkingStrategy.ROW_BASED
    # Override chunk_size and chunk_overlap for Excel (rows/columns, not characters)
    chunk_size: int = Field(default=10, ge=1, le=100)  # Number of rows/columns
    chunk_overlap: int = Field(default=0, ge=0, le=10)  # Overlap rows/columns
    
    # Sheet filtering
    sheet_filter: Optional[List[str]] = None  # Process only specified sheets
    skip_empty_sheets: bool = True
    
    # Excel parsing options
    include_formulas: bool = True
    include_formatting: bool = False
    include_comments: bool = False
    include_hidden_sheets: bool = False
    
    # Header detection
    auto_detect_headers: bool = True
    header_row_hint: Optional[int] = None  # Hint for header row location
    
    # Data analysis options
    detect_domains: bool = True
    detect_data_types: bool = True
    analyze_relationships: bool = True
    statistical_analysis: bool = True
    
    # Quality assessment
    quality_assessment: bool = True
    completeness_threshold: float = Field(default=0.9, ge=0.0, le=1.0)
    consistency_threshold: float = Field(default=0.8, ge=0.0, le=1.0)
    
    # LangChain options
    use_langchain_analysis: bool = True
    langchain_model: str = "gpt-4.1-mini"
    langchain_temperature: float = Field(default=0.1, ge=0.0, le=1.0)
    
    @field_validator('sheet_filter')
    @classmethod
    def validate_sheet_filter(cls, v):
        if v is not None and len(v) == 0:
            return None
        return v


# ===== EXCEL-SPECIFIC CHUNK TYPES =====

class ExcelChunkType(str, Enum):
    """Types of chunks created from Excel files"""
    SCHEMA = "schema"  # Table structure and column information
    DATA_SAMPLE = "data_sample"  # Representative data samples
    STATISTICAL = "statistical"  # Statistical summaries
    RELATIONSHIPS = "relationships"  # Column relationships and patterns
    QUALITY = "quality"  # Data quality assessment
    DOMAIN = "domain"  # Domain classification and business context
    FORMULA = "formula"  # Excel formulas and calculations


# ===== EXCEL ANALYSIS RESULTS =====

class ExcelColumnAnalysis(BaseModel):
    """Analysis results for a single Excel column"""
    column_name: str
    column_index: int
    data_type: str
    semantic_type: Optional[str] = None
    
    # Statistics
    total_values: int
    null_count: int
    unique_count: int
    completeness: float
    
    # Sample values
    sample_values: List[Union[str, int, float]] = Field(default_factory=list)
    top_values: List[Dict[str, Any]] = Field(default_factory=list)  # value: count pairs
    
    # Quality metrics
    format_consistency: Optional[float] = None
    pattern_compliance: Optional[float] = None
    business_rule_violations: List[str] = Field(default_factory=list)
    
    # Semantic analysis
    domain_relevance: Optional[float] = None
    examples: List[str] = Field(default_factory=list)
    patterns: List[str] = Field(default_factory=list)


class ExcelSheetAnalysis(BaseModel):
    """Analysis results for a single Excel sheet"""
    sheet_name: str
    sheet_index: int
    
    # Basic statistics
    total_rows: int
    total_columns: int
    data_rows: int  # Excluding headers
    header_row: int
    
    # Column analysis
    columns: List[ExcelColumnAnalysis]
    
    # Relationships
    relationships: List[Dict[str, Any]] = Field(default_factory=list)
    primary_keys: List[str] = Field(default_factory=list)
    foreign_keys: List[Dict[str, str]] = Field(default_factory=list)
    
    # Quality assessment
    overall_quality_score: Optional[float] = None
    quality_issues: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    
    # Domain analysis
    detected_domain: Optional[str] = None
    domain_confidence: Optional[float] = None
    business_context: Optional[str] = None


class ExcelFileAnalysis(BaseModel):
    """Complete analysis results for Excel file"""
    filename: str
    file_size: int
    
    # Sheet information
    total_sheets: int
    processed_sheets: int
    sheets: List[ExcelSheetAnalysis]
    
    # Cross-sheet analysis
    cross_sheet_relationships: List[Dict[str, Any]] = Field(default_factory=list)
    shared_domains: List[str] = Field(default_factory=list)
    
    # Overall metrics
    overall_quality_score: float
    total_data_points: int
    total_relationships: int
    
    # Processing metadata
    processing_time_seconds: float
    langchain_analysis_used: bool
    embedding_model_used: Optional[str] = None


# ===== EXCEL SEMANTIC TYPES =====

class ExcelSemanticType(BaseModel):
    """Semantic type definition for Excel columns"""
    name: str
    description: str
    patterns: List[str] = Field(default_factory=list)
    examples: List[str] = Field(default_factory=list)
    data_type_constraints: List[str] = Field(default_factory=list)
    business_rules: List[str] = Field(default_factory=list)
    confidence_threshold: float = Field(default=0.7, ge=0.0, le=1.0)


class ExcelDomainDefinition(BaseModel):
    """Domain definition for Excel data classification"""
    domain_name: str
    description: str
    semantic_types: List[ExcelSemanticType]
    relationship_patterns: List[Dict[str, Any]] = Field(default_factory=list)
    quality_rules: List[Dict[str, Any]] = Field(default_factory=list)
    sample_headers: List[str] = Field(default_factory=list)
    business_context: Optional[str] = None


# ===== EXCEL PROCESSING RESULT =====

class ExcelProcessingResult(BaseModel):
    """Complete result of Excel file processing"""
    job_id: str
    filename: str
    
    # Analysis results
    file_analysis: ExcelFileAnalysis
    
    # Generated chunks
    total_chunks: int
    chunks_by_type: Dict[ExcelChunkType, int] = Field(default_factory=dict)
    
    # Embeddings (if generated)
    total_embeddings: int = 0
    embedding_model_used: Optional[str] = None
    
    # Relationships (if detected)
    total_relationships: int = 0
    relationship_types: List[str] = Field(default_factory=list)
    
    # Storage results
    storage_success: bool = False
    storage_errors: List[str] = Field(default_factory=list)
    
    # Processing metadata
    started_at: str
    completed_at: str
    processing_duration_seconds: float
    options_used: ExcelProcessingOptions