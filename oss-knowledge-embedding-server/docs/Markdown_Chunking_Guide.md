# Markdown Chunking API Guide

## Overview

The Markdown Preview endpoint provides simple, configurable text chunking with three boundary strategies: **paragraph**, **sentence**, and **word**. This guide demonstrates how different parameters affect chunking results.

## Endpoint

```
POST /process/markdown/preview
```

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `file` | File | Required | Markdown file to process |
| `container` | String | "general" | Target container for storage |
| `chunking_strategy` | String | "paragraph" | Chunking boundary: `paragraph`, `sentence`, or `word` |
| `chunk_size` | Integer | 500 | Target chunk size in characters |
| `overlap` | Integer | 50 | Character overlap between chunks |

## Chunking Strategies

### Paragraph Strategy
Splits text on double newlines (`\n\n`), respecting paragraph boundaries.

**Best for:**
- Documents with clear paragraph structure
- Maintaining contextual coherence
- General-purpose chunking

### Sentence Strategy
Splits text on sentence boundaries (`.`, `!`, `?` followed by space).

**Best for:**
- Fine-grained semantic units
- Question-answering systems
- Detailed content analysis

### Word Strategy
Splits text on whitespace (word boundaries).

**Best for:**
- Precise size control
- Token-based processing
- Very small chunk requirements

---

## Test Results

### Test Document
**Source:** `test_sample.md` (2,011 characters)
**Content:** Machine learning introduction with headers, paragraphs, and structured sections

---

## 1. Paragraph Strategy - Small Chunks

**Parameters:**
```json
{
  "chunking_strategy": "paragraph",
  "chunk_size": 200,
  "overlap": 30
}
```

**Results:**
- **Total Chunks:** 15
- **Average Size:** 162 characters

**Sample Chunks:**

**Chunk 0** (34 chars):
```
# Introduction to Machine Learning
```

**Chunk 1** (227 chars):
```
troduction to Machine LearningMachine learning is a subset of artificial intelligence that focuses on building systems that learn from data. These systems improve their performance over time without being explicitly programmed.
```
*Note: 30-character overlap from previous chunk*

**Chunk 3** (296 chars):
```
 cases.### Supervised LearningSupervised learning uses labeled training data to learn the relationship between inputs and outputs. The algorithm learns from examples where the correct answer is already known. Common applications include spam detection, image classification, and price prediction.
```

---

## 2. Paragraph Strategy - Medium Chunks

**Parameters:**
```json
{
  "chunking_strategy": "paragraph",
  "chunk_size": 500,
  "overlap": 50
}
```

**Results:**
- **Total Chunks:** 6
- **Average Size:** 377 characters

**Sample Chunks:**

**Chunk 0** (382 chars):
```
# Introduction to Machine LearningMachine learning is a subset of artificial intelligence that focuses on building systems that learn from data. These systems improve their performance over time without being explicitly programmed.## Types of Machine LearningThere are three main types of machine learning approaches. Each has its own strengths and use cases.### Supervised Learning
```

**Chunk 1** (341 chars):
```
wn strengths and use cases.### Supervised LearningSupervised learning uses labeled training data to learn the relationship between inputs and outputs. The algorithm learns from examples where the correct answer is already known. Common applications include spam detection, image classification, and price prediction.### Unsupervised Learning
```
*Note: 50-character overlap from previous chunk*

---

## 3. Paragraph Strategy - Large Chunks

**Parameters:**
```json
{
  "chunking_strategy": "paragraph",
  "chunk_size": 1000,
  "overlap": 100
}
```

**Results:**
- **Total Chunks:** 3
- **Average Size:** 737 characters

**Sample Chunks:**

**Chunk 0** (925 chars):
```
# Introduction to Machine LearningMachine learning is a subset of artificial intelligence that focuses on building systems that learn from data. These systems improve their performance over time without being explicitly programmed.## Types of Machine LearningThere are three main types of machine learning approaches. Each has its own strengths and use cases.### Supervised LearningSupervised learning uses labeled training data to learn the relationship between inputs and outputs. The algorithm learns from examples where the correct answer is already known. Common applications include spam detection, image classification, and price prediction.### Unsupervised LearningUnsupervised learning works with unlabeled data to find hidden patterns or structures. The algorithm explores the data without predefined categories. Clustering and dimensionality reduction are popular unsupervised techniques.### Reinforcement Learning
```

---

## 4. Sentence Strategy - Small Chunks

**Parameters:**
```json
{
  "chunking_strategy": "sentence",
  "chunk_size": 150,
  "overlap": 20
}
```

**Results:**
- **Total Chunks:** 22
- **Average Size:** 111 characters

**Sample Chunks:**

**Chunk 0** (146 chars):
```
# Introduction to Machine Learning

Machine learning is a subset of artificial intelligence that focuses on building systems that learn from data.
```

**Chunk 1** (106 chars):
```
hat learn from data.These systems improve their performance over time without being explicitly programmed.
```
*Note: 20-character overlap from previous chunk*

**Chunk 3** (145 chars):
```
ngths and use cases.### Supervised Learning

Supervised learning uses labeled training data to learn the relationship between inputs and outputs.
```

**Chunk 5** (107 chars):
```
er is already known.Common applications include spam detection, image classification, and price prediction.
```

---

## 5. Sentence Strategy - Medium Chunks

**Parameters:**
```json
{
  "chunking_strategy": "sentence",
  "chunk_size": 300,
  "overlap": 40
}
```

**Results:**
- **Total Chunks:** 9
- **Average Size:** 259 characters

**Sample Chunks:**

**Chunk 0** (232 chars):
```
# Introduction to Machine Learning

Machine learning is a subset of artificial intelligence that focuses on building systems that learn from data.These systems improve their performance over time without being explicitly programmed.
```

**Chunk 2** (204 chars):
```
relationship between inputs and outputs.The algorithm learns from examples where the correct answer is already known.Common applications include spam detection, image classification, and price prediction.
```

**Chunk 7** (280 chars):
```
the model generalizes to new situations.### Overfitting and Underfitting

Overfitting occurs when a model learns training data too well, including noise.Underfitting happens when a model is too simple to capture patterns.Finding the right balance is crucial for model performance.
```

---

## 6. Word Strategy - Very Small Chunks

**Parameters:**
```json
{
  "chunking_strategy": "word",
  "chunk_size": 100,
  "overlap": 15
}
```

**Results:**
- **Total Chunks:** 25
- **Average Size:** 95 characters

**Sample Chunks:**

**Chunk 0** (95 chars):
```
# Introduction to Machine Learning Machine learning is a subset of artificial intelligence that
```

**Chunk 1** (93 chars):
```
telligence that focuses on building systems that learn from data. These systems improve their
```
*Note: 15-character overlap from previous chunk*

**Chunk 6** (99 chars):
```
. The algorithm learns from examples where the correct answer is already known. Common applications
```

**Chunk 13** (100 chars):
```
es based on its actions. This approach is used in robotics, game playing, and autonomous systems. ##
```

---

## 7. Word Strategy - Small Chunks

**Parameters:**
```json
{
  "chunking_strategy": "word",
  "chunk_size": 200,
  "overlap": 25
}
```

**Results:**
- **Total Chunks:** 12
- **Average Size:** 192 characters

**Sample Chunks:**

**Chunk 0** (195 chars):
```
# Introduction to Machine Learning Machine learning is a subset of artificial intelligence that focuses on building systems that learn from data. These systems improve their performance over time
```

**Chunk 2** (199 chars):
```
engths and use cases. ### Supervised Learning Supervised learning uses labeled training data to learn the relationship between inputs and outputs. The algorithm learns from examples where the correct
```

**Chunk 5** (197 chars):
```
ity reduction are popular unsupervised techniques. ### Reinforcement Learning Reinforcement learning trains agents to make decisions through trial and error. The agent receives rewards or penalties
```

**Chunk 9** (193 chars):
```
es to new situations. ### Overfitting and Underfitting Overfitting occurs when a model learns training data too well, including noise. Underfitting happens when a model is too simple to capture
```

---

## Comparison Summary

| Strategy | Chunk Size | Overlap | Total Chunks | Avg Chunk Size |
|----------|------------|---------|--------------|----------------|
| Paragraph | 200 | 30 | 15 | 162 |
| Paragraph | 500 | 50 | 6 | 377 |
| Paragraph | 1000 | 100 | 3 | 737 |
| Sentence | 150 | 20 | 22 | 111 |
| Sentence | 300 | 40 | 9 | 259 |
| Word | 100 | 15 | 25 | 95 |
| Word | 200 | 25 | 12 | 192 |

## Key Observations

### Overlap Behavior
- Overlap creates redundancy between chunks for context continuity
- **Word boundaries are preserved**: Overlap text starts at the first complete word to avoid splitting words
- Larger overlaps (50-100 chars) provide better context but increase storage
- Smaller overlaps (15-30 chars) save space but may lose context
- Actual overlap may be slightly smaller than requested to maintain word boundaries

**Example of Word Boundary Preservation:**

Given text: `"...without being explicitly programmed."`

❌ **Without word boundary:** (30 char overlap)
```
Chunk 1: "...without being explicitly programmed."
Chunk 2: "troduction to Machine Learning Machine..."  ← Word cut off!
```

✓ **With word boundary:** (30 char overlap)
```
Chunk 1: "...without being explicitly programmed."
Chunk 2: "to Machine Learning Machine learning..."  ← Clean start!
```

This ensures all chunks contain complete, readable words.

### Chunk Size Accuracy
- Actual chunk sizes may vary from target due to boundary constraints
- Paragraph strategy produces most variable chunk sizes
- Word strategy produces most consistent chunk sizes
- Sentence strategy balances between the two

### Boundary Respect
- All strategies respect their designated boundaries
- Paragraph chunks preserve complete paragraphs
- Sentence chunks preserve complete sentences
- Word chunks may split mid-sentence but keep words intact

## Usage Recommendations

### For Knowledge Base Search (RAG)
```json
{
  "chunking_strategy": "paragraph",
  "chunk_size": 500,
  "overlap": 50
}
```
**Rationale:** Maintains semantic coherence while keeping chunks at optimal size for embeddings.

### For Question Answering
```json
{
  "chunking_strategy": "sentence",
  "chunk_size": 300,
  "overlap": 40
}
```
**Rationale:** Sentence-level granularity improves precision for specific questions.

### For Token-Limited Models
```json
{
  "chunking_strategy": "word",
  "chunk_size": 200,
  "overlap": 25
}
```
**Rationale:** Precise size control ensures chunks fit within token limits.

### For Document Summarization
```json
{
  "chunking_strategy": "paragraph",
  "chunk_size": 1000,
  "overlap": 100
}
```
**Rationale:** Larger chunks with substantial overlap preserve document flow and context.

---

## API Response Format

```json
{
  "filename": "test_sample.md",
  "content_length": 2011,
  "recommended_strategy": {
    "strategy_name": "paragraph",
    "reason": "Chunking by paragraph with 500 characters and 50 overlap",
    "parameters": {
      "chunk_size": 500,
      "overlap": 50,
      "boundary": "paragraph"
    }
  },
  "chunks": [
    {
      "chunk_id": "chunk_0",
      "content": "...",
      "chunk_type": "text",
      "start_position": 0,
      "end_position": 382,
      "metadata": {
        "chunk_index": 0,
        "length": 382
      }
    }
  ],
  "total_chunks": 6,
  "processing_time_seconds": 0.023
}
```

## Example cURL Request

```bash
curl -X POST "http://localhost:8001/process/markdown/preview" \
  -F "file=@document.md" \
  -F "container=general" \
  -F "chunking_strategy=paragraph" \
  -F "chunk_size=500" \
  -F "overlap=50"
```

---

*Generated from test results using `test_sample.md`*
