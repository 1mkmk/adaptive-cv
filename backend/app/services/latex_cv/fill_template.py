"""
Template filling helper for LaTeX CV generator.

This module contains specialized functions for properly filling LaTeX templates
with candidate data.
"""

import re
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

def escape_latex(text: str) -> str:
    """
    Escape special LaTeX characters in text
    
    Args:
        text: Text to escape
        
    Returns:
        Escaped text
    """
    if not isinstance(text, str):
        return text
        
    # Characters that need to be escaped in LaTeX
    special_chars = {
        '&': '\\&',
        '%': '\\%',
        '$': '\\$',
        '#': '\\#',
        '_': '\\_',
        '{': '\\{',
        '}': '\\}',
        '~': '\\textasciitilde{}',
        '^': '\\textasciicircum{}',
        '\\': '\\textbackslash{}'
    }
    
    # Replace special characters
    for char, replacement in special_chars.items():
        text = text.replace(char, replacement)
    
    return text

def prepare_address_format(address_text: str, email: Optional[str] = None, linkedin: Optional[str] = None) -> List[str]:
    """
    Format address string for LaTeX template
    
    Args:
        address_text: Raw address text
        email: Optional email to add to address
        linkedin: Optional linkedin to add to address
        
    Returns:
        List of formatted address lines for LaTeX
    """
    # Split address into lines if it contains line breaks
    address_lines = address_text.split('\n') if '\n' in address_text else [address_text]
    
    # Clean lines
    address_lines = [line.strip() for line in address_lines if line.strip()]
    
    # Format output for LaTeX
    result = []
    
    # First address line
    if address_lines:
        first_line = address_lines[0]
        if len(address_lines) > 1:
            first_line += ' \\\\ ' + address_lines[1]
        result.append(first_line)
    
    # Second address with email and linkedin if available
    components = []
    if email:
        components.append(f"\\href{{mailto:{email}}}{{{email}}}")
    if linkedin:
        components.append(f"\\href{{https://{linkedin}}}{{{linkedin}}}")
    
    if components:
        result.append(' \\\\ '.join(components))
    
    return result

def safe_template_value(value: Any) -> str:
    """
    Convert a value to a string representation safe for LaTeX templates
    
    Args:
        value: Any value to convert
        
    Returns:
        String representation safe for LaTeX
    """
    if value is None:
        return ""
    elif isinstance(value, str):
        return escape_latex(value)
    elif isinstance(value, bool):
        return "true" if value else "false"
    elif isinstance(value, (int, float)):
        return str(value)
    elif isinstance(value, list):
        # Convert list to comma-separated string
        return ", ".join(safe_template_value(item) for item in value)
    elif isinstance(value, dict):
        # For dictionaries, we'll just use a simplified representation
        return f"{{{', '.join(f'{k}: {safe_template_value(v)}' for k, v in value.items())}}}"
    else:
        # For any other type, convert to string
        return escape_latex(str(value))