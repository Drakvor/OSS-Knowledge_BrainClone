"""
Utility functions for Task Planner
"""

import json
import re
from typing import Any, Dict


def sanitize_json_string(value: Any) -> Any:
    """
    Recursively sanitize strings in a data structure to remove control characters.
    
    Args:
        value: Any value (dict, list, str, etc.)
        
    Returns:
        Sanitized value with control characters removed from strings
    """
    if isinstance(value, str):
        # Replace newlines, tabs, carriage returns with spaces (JSON-safe)
        sanitized = value.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
        # Remove ALL remaining control characters (0x00-0x1F, 0x7F)
        sanitized = re.sub(r'[\x00-\x1F\x7F]', '', sanitized)
        # Remove multiple consecutive spaces
        sanitized = re.sub(r' +', ' ', sanitized).strip()
        return sanitized
    elif isinstance(value, dict):
        return {k: sanitize_json_string(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [sanitize_json_string(item) for item in value]
    else:
        return value


def safe_json_dumps(obj: Any, **kwargs) -> str:
    """
    Safely serialize object to JSON string, removing control characters.
    
    Args:
        obj: Object to serialize
        **kwargs: Additional arguments for json.dumps
        
    Returns:
        JSON string with control characters removed
    """
    # First sanitize the object
    sanitized = sanitize_json_string(obj)
    
    # Then serialize to JSON
    return json.dumps(sanitized, ensure_ascii=False, **kwargs)


def safe_dict_to_json(obj: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert dict to JSON-safe dict by sanitizing all string values.
    
    Args:
        obj: Dictionary to sanitize
        
    Returns:
        Sanitized dictionary
    """
    return sanitize_json_string(obj)
