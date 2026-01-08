#!/usr/bin/env python3
"""
Strategy Comparison Runner
=========================

Comprehensive script to test different chunking and embedding strategies
on ITSM Data_Mobile.xlsx and generate detailed analysis report.
"""

import asyncio
import logging
import json
import time
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Imports
from app.strategies.orchestrator import StrategyOrchestrator, StrategyCombo
from app.strategies.chunking.base import ChunkingConfig, ChunkingStrategyType  
from app.strategies.embedding.base import EmbeddingConfig, EmbeddingStrategyType
from app.evaluation.accuracy_tester import AccuracyTester
import pandas as pd


async def load_itsm_data() -> str:
    """Load ITSM Data_Mobile.xlsx and extract text content"""
    
    try:
        file_path = Path("data/ITSM Data_Mobile.xlsx")
        if not file_path.exists():
            raise FileNotFoundError(f"ITSM data file not found: {file_path}")
        
        logger.info(f"Loading ITSM data from: {file_path}")
        
        # Read Excel file
        df = pd.read_excel(file_path)
        logger.info(f"Loaded {len(df)} rows from ITSM data")
        
        # Extract relevant text columns
        text_columns = []
        for col in df.columns:
            if df[col].dtype == 'object':  # Text columns
                text_columns.append(col)
        
        # Combine all text content
        combined_text = []
        
        for _, row in df.iterrows():
            row_text = []
            for col in text_columns:
                if pd.notna(row[col]):
                    row_text.append(f"{col}={row[col]}")
            
            if row_text:
                combined_text.append(", ".join(row_text))
        
        # Join all rows with newlines
        full_text = "\n".join(combined_text)
        
        logger.info(f"Extracted {len(full_text)} characters of text from ITSM data")
        return full_text
        
    except Exception as e:
        logger.error(f"Error loading ITSM data: {e}")
        raise


def create_comprehensive_strategy_combos() -> list:
    """Create comprehensive set of strategy combinations for Excel data testing"""
    
    return [
        # Excel-Specific Strategies
        StrategyCombo(
            name="Excel Row-by-Row (Korean)",
            chunking_config=ChunkingConfig(
                strategy_type=ChunkingStrategyType.EXCEL_ROW,
                chunk_size=1000,
                overlap=0,
                min_chunk_size=100,
                max_chunk_size=2000,
                custom_params={
                    'rows_per_chunk': 1,
                    'include_headers': True,
                    'preserve_structure': True
                }
            ),
            embedding_config=EmbeddingConfig(
                strategy_type=EmbeddingStrategyType.SENTENCE_BERT,
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                batch_size=16
            ),
            description="One row per chunk with Korean BGE-M3 embeddings - ideal for individual ticket analysis"
        ),
        
        StrategyCombo(
            name="Excel Multi-Row Groups",
            chunking_config=ChunkingConfig(
                strategy_type=ChunkingStrategyType.EXCEL_ROW,
                chunk_size=1500,
                overlap=0,
                min_chunk_size=200,
                max_chunk_size=3000,
                custom_params={
                    'rows_per_chunk': 3,
                    'include_headers': True,
                    'preserve_structure': True
                }
            ),
            embedding_config=EmbeddingConfig(
                strategy_type=EmbeddingStrategyType.SENTENCE_BERT,
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                batch_size=16
            ),
            description="Multiple rows per chunk for pattern analysis across related tickets"
        ),
        
        StrategyCombo(
            name="Excel Column Analysis",
            chunking_config=ChunkingConfig(
                strategy_type=ChunkingStrategyType.EXCEL_COLUMN,
                chunk_size=1500,
                overlap=0,
                min_chunk_size=200,
                max_chunk_size=3000,
                custom_params={
                    'columns_per_chunk': 1,
                    'include_column_names': True,
                    'sample_rows': 15,
                    'target_columns': ['상세_설명', '문제_유형', '해결_방법']
                }
            ),
            embedding_config=EmbeddingConfig(
                strategy_type=EmbeddingStrategyType.SENTENCE_BERT,
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                batch_size=16
            ),
            description="Column-focused analysis for field-specific insights and patterns"
        ),
        
        StrategyCombo(
            name="Excel Hybrid Intelligence",
            chunking_config=ChunkingConfig(
                strategy_type=ChunkingStrategyType.EXCEL_HYBRID,
                chunk_size=1200,
                overlap=0,
                min_chunk_size=150,
                max_chunk_size=2500,
                custom_params={
                    'rows_per_chunk': 5,
                    'key_columns': ['문제_유형', '상태', '우선순위'],
                    'chunk_by_similarity': True,
                    'preserve_relationships': True,
                    'min_semantic_similarity': 0.3
                }
            ),
            embedding_config=EmbeddingConfig(
                strategy_type=EmbeddingStrategyType.SENTENCE_BERT,
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                batch_size=16
            ),
            description="Intelligent grouping by semantic similarity with Korean optimization"
        ),
        
        # Traditional Approaches for Comparison
        StrategyCombo(
            name="Traditional Text Processing",
            chunking_config=ChunkingConfig(
                strategy_type=ChunkingStrategyType.FIXED_SIZE,
                chunk_size=512,
                overlap=50
            ),
            embedding_config=EmbeddingConfig(
                strategy_type=EmbeddingStrategyType.SENTENCE_BERT,
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                batch_size=16
            ),
            description="Traditional fixed-size chunking (loses Excel structure)"
        ),
        
        StrategyCombo(
            name="Semantic Text Analysis",
            chunking_config=ChunkingConfig(
                strategy_type=ChunkingStrategyType.SEMANTIC,
                chunk_size=600,
                max_chunk_size=1200
            ),
            embedding_config=EmbeddingConfig(
                strategy_type=EmbeddingStrategyType.SENTENCE_BERT,
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                batch_size=16
            ),
            description="Semantic chunking without Excel structure awareness"
        ),
        
        # Fast Processing Options
        StrategyCombo(
            name="Fast Excel Rows (Lightweight)",
            chunking_config=ChunkingConfig(
                strategy_type=ChunkingStrategyType.EXCEL_ROW,
                chunk_size=800,
                overlap=0,
                custom_params={
                    'rows_per_chunk': 2,
                    'include_headers': True,
                    'preserve_structure': True
                }
            ),
            embedding_config=EmbeddingConfig(
                strategy_type=EmbeddingStrategyType.SENTENCE_BERT,
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                batch_size=32
            ),
            description="Fast Excel processing with lightweight embeddings"
        )
    ]


async def run_comprehensive_comparison():
    """Run comprehensive strategy comparison and analysis"""
    
    start_time = time.time()
    logger.info("=" * 60)
    logger.info("Starting Comprehensive Strategy Comparison")
    logger.info("=" * 60)
    
    try:
        # Step 1: Load ITSM data
        logger.info("Step 1: Loading ITSM data...")
        itsm_text = await load_itsm_data()
        
        # Step 2: Initialize orchestrator and accuracy tester
        logger.info("Step 2: Initializing components...")
        orchestrator = StrategyOrchestrator()
        accuracy_tester = AccuracyTester()
        
        # Step 3: Create strategy combinations
        logger.info("Step 3: Creating strategy combinations...")
        strategy_combos = create_comprehensive_strategy_combos()
        logger.info(f"Created {len(strategy_combos)} strategy combinations")
        
        # Step 4: Run strategy comparison
        logger.info("Step 4: Running strategy comparison...")
        source_metadata = {
            "job_id": f"comparison_{int(time.time())}",
            "source_file": "ITSM Data_Mobile.xlsx",
            "test_type": "comprehensive_strategy_comparison"
        }
        
        strategy_results = await orchestrator.compare_strategies(
            itsm_text, strategy_combos, source_metadata
        )
        
        logger.info(f"Completed processing with {len(strategy_results)} strategies")
        
        # Step 5: Performance analysis
        logger.info("Step 5: Analyzing performance...")
        performance_analysis = orchestrator.get_performance_comparison(strategy_results)
        
        # Step 6: Accuracy evaluation
        logger.info("Step 6: Evaluating accuracy...")
        accuracy_analysis = await accuracy_tester.compare_strategy_accuracy(strategy_results)
        
        # Step 7: Generate recommendations
        logger.info("Step 7: Generating recommendations...")
        recommendations = orchestrator.get_strategy_recommendations(strategy_results, "itsm")
        
        # Step 8: Compile comprehensive report
        logger.info("Step 8: Compiling comprehensive report...")
        total_time = time.time() - start_time
        
        comprehensive_report = {
            "experiment_metadata": {
                "timestamp": datetime.now().isoformat(),
                "total_processing_time_seconds": total_time,
                "source_data": "ITSM Data_Mobile.xlsx",
                "text_length_chars": len(itsm_text),
                "strategies_tested": len(strategy_combos),
                "test_framework_version": "1.0.0"
            },
            
            "strategy_configurations": [
                {
                    "name": combo.name,
                    "description": combo.description,
                    "chunking_strategy": combo.chunking_config.strategy_type.value,
                    "chunking_params": {
                        "chunk_size": combo.chunking_config.chunk_size,
                        "overlap": combo.chunking_config.overlap,
                        "max_chunk_size": combo.chunking_config.max_chunk_size
                    },
                    "embedding_strategy": combo.embedding_config.strategy_type.value,
                    "embedding_params": {
                        "model_name": combo.embedding_config.model_name,
                        "batch_size": combo.embedding_config.batch_size
                    }
                }
                for combo in strategy_combos
            ],
            
            "performance_analysis": performance_analysis,
            "accuracy_analysis": accuracy_analysis,
            "recommendations": recommendations,
            
            "detailed_results": [
                {
                    "strategy_name": result.combo_name,
                    "processing_times": {
                        "total_ms": result.processing_time_ms,
                        "chunking_ms": result.chunking_time_ms,
                        "embedding_ms": result.embedding_time_ms
                    },
                    "output_metrics": {
                        "total_chunks": result.total_chunks,
                        "avg_chunk_size": result.avg_chunk_size,
                        "embedding_dimension": result.embedding_dimension
                    },
                    "sample_chunks": [
                        {
                            "chunk_id": chunk.chunk_id,
                            "content": chunk.content[:200] + "..." if len(chunk.content) > 200 else chunk.content,
                            "chunk_type": chunk.chunk_type,
                            "start_position": chunk.start_position,
                            "end_position": chunk.end_position
                        }
                        for chunk in result.chunks[:3]  # First 3 chunks as samples
                    ]
                }
                for result in strategy_results
            ]
        }
        
        # Step 9: Save report
        logger.info("Step 9: Saving comprehensive report...")
        report_path = Path("docs/strategy_comparison_report.json")
        report_path.parent.mkdir(exist_ok=True)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(comprehensive_report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Comprehensive report saved to: {report_path}")
        
        # Step 10: Generate markdown summary
        await generate_markdown_summary(comprehensive_report, strategy_results)
        
        logger.info("=" * 60)
        logger.info(f"Comprehensive Strategy Comparison Complete! ({total_time:.1f}s)")
        logger.info("=" * 60)
        
        return comprehensive_report
        
    except Exception as e:
        logger.error(f"Error during comprehensive comparison: {e}")
        raise


async def generate_markdown_summary(comprehensive_report: dict, strategy_results: list):
    """Generate markdown summary report"""
    
    logger.info("Generating markdown summary report...")
    
    markdown_content = f"""# Chunking & Embedding Strategy Comparison Report

Generated: {comprehensive_report['experiment_metadata']['timestamp']}

## Executive Summary

This report compares {comprehensive_report['experiment_metadata']['strategies_tested']} different combinations of chunking and embedding strategies on ITSM data, evaluating both performance and accuracy metrics.

### Key Findings

**Best Overall Strategy**: {comprehensive_report['accuracy_analysis']['summary']['best_overall_strategy']} 
- Overall Accuracy Score: {comprehensive_report['accuracy_analysis']['summary']['best_overall_score']:.3f}

**Fastest Strategy**: {comprehensive_report['performance_analysis']['comparison_summary']['fastest_combo']}
- Processing Time: {comprehensive_report['performance_analysis']['comparison_summary']['fastest_time_ms']:.1f}ms

**Recommended for ITSM**: {comprehensive_report['recommendations']['recommended_combo']}

## Strategy Configurations

"""
    
    for config in comprehensive_report['strategy_configurations']:
        markdown_content += f"""### {config['name']}

**Description**: {config['description']}

**Configuration**:
- Chunking: {config['chunking_strategy']} (size: {config['chunking_params']['chunk_size']}, overlap: {config['chunking_params']['overlap']})
- Embedding: {config['embedding_strategy']} ({config['embedding_params']['model_name']})

"""

    markdown_content += f"""## Performance Analysis

### Processing Time Comparison

"""
    
    for perf in comprehensive_report['performance_analysis']['detailed_performance']:
        markdown_content += f"""**{perf['combo_name']}**: {perf['total_time_ms']:.1f}ms total ({perf['chunks_per_second']:.1f} chunks/sec)
"""

    markdown_content += f"""
### Average Metrics

- Average Processing Time: {comprehensive_report['performance_analysis']['avg_metrics']['avg_total_time_ms']:.1f}ms
- Average Chunks Generated: {comprehensive_report['performance_analysis']['avg_metrics']['avg_chunks']:.1f}
- Average Chunk Size: {comprehensive_report['performance_analysis']['avg_metrics']['avg_chunk_size']:.1f} characters

## Accuracy Analysis

"""
    
    for result in comprehensive_report['accuracy_analysis']['detailed_results']:
        markdown_content += f"""### {result['strategy_name']}

**Overall Accuracy**: {result['overall_score']:.3f}

**Chunking Quality**:
- Coherence: {result['chunking_scores']['coherence']:.3f}
- Consistency: {result['chunking_scores']['consistency']:.3f}
- Semantic Preservation: {result['chunking_scores']['semantic_preservation']:.3f}

**Embedding Quality**:
- Coherence: {result['embedding_scores']['coherence']:.3f}
- Cluster Quality: {result['embedding_scores']['cluster_quality']:.3f}
- Similarity Preservation: {result['embedding_scores']['similarity_preservation']:.3f}

**Retrieval Performance**:
- Precision@1: {result['retrieval_scores']['precision_at_1']:.3f}
- Precision@3: {result['retrieval_scores']['precision_at_3']:.3f}
- Precision@5: {result['retrieval_scores']['precision_at_5']:.3f}

"""

    markdown_content += f"""## Recommendations

### For ITSM Use Cases

**Primary Recommendation**: {comprehensive_report['recommendations']['recommended_combo']}

**Reasoning**: {comprehensive_report['recommendations']['reasoning']}

### Alternative Recommendations

- **For Speed**: {comprehensive_report['recommendations']['alternatives']['for_speed']}
- **For Quality**: {comprehensive_report['recommendations']['alternatives']['for_quality']}
- **For Context**: {comprehensive_report['recommendations']['alternatives']['for_context']}
- **For Efficiency**: {comprehensive_report['recommendations']['alternatives']['for_efficiency']}

### Performance Tradeoffs

"""
    
    for key, value in comprehensive_report['recommendations']['performance_tradeoffs'].items():
        markdown_content += f"- **{key.replace('_', ' ').title()}**: {value}\n"

    markdown_content += f"""
## Sample Output

### Example Chunks from Top Strategy

"""

    # Find best strategy results
    best_strategy_name = comprehensive_report['accuracy_analysis']['summary']['best_overall_strategy']
    best_result = next((r for r in comprehensive_report['detailed_results'] if r['strategy_name'] == best_strategy_name), None)
    
    if best_result:
        for i, chunk in enumerate(best_result['sample_chunks'][:3], 1):
            markdown_content += f"""#### Chunk {i} ({chunk['chunk_type']})

```
{chunk['content']}
```

Position: {chunk['start_position']}-{chunk['end_position']}

"""

    markdown_content += f"""
## Technical Details

### Experiment Configuration

- **Source Data**: {comprehensive_report['experiment_metadata']['source_data']}
- **Text Length**: {comprehensive_report['experiment_metadata']['text_length_chars']:,} characters
- **Total Processing Time**: {comprehensive_report['experiment_metadata']['total_processing_time_seconds']:.1f} seconds
- **Strategies Tested**: {comprehensive_report['experiment_metadata']['strategies_tested']}

### Evaluation Methodology

This comparison evaluated strategies across multiple dimensions:

1. **Performance Metrics**: Processing time, throughput, resource efficiency
2. **Chunking Quality**: Coherence, consistency, semantic boundary preservation  
3. **Embedding Quality**: Coherence, clustering quality, similarity preservation
4. **Retrieval Accuracy**: Precision at different recall levels using ITSM-specific test queries

### Framework Information

- **Test Framework Version**: {comprehensive_report['experiment_metadata']['test_framework_version']}
- **Generated**: {comprehensive_report['experiment_metadata']['timestamp']}

---

*This report was generated automatically by the OSS Knowledge Embedding Server strategy comparison framework.*
"""

    # Save markdown report
    markdown_path = Path("docs/Strategy_Comparison_Report.md")
    with open(markdown_path, 'w', encoding='utf-8') as f:
        f.write(markdown_content)
    
    logger.info(f"Markdown summary saved to: {markdown_path}")


if __name__ == "__main__":
    asyncio.run(run_comprehensive_comparison())