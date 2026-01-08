"""
Modular Chunking and Embedding Strategies
=========================================

This module provides pluggable strategies for:
- Text chunking (fixed-size, semantic, sliding-window, etc.)  
- Embedding generation (BGE-M3, Sentence-BERT, OpenAI, etc.)
- Accuracy evaluation and comparison

Each strategy is implemented as an independent, testable component
that can be combined and compared for different use cases.
"""