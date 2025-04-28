"""
Functions for detecting fields and commands in LaTeX files.

This module contains functions for analyzing LaTeX files to find commands, environments,
and placeholders that might need replacement.
"""

import os
import re
import logging
from typing import Dict, Any, List

from .constants import CV_COMMANDS, PLACEHOLDER_PATTERNS

logger = logging.getLogger(__name__)

def analyze_file_for_fields(file_path: str) -> Dict[str, Any]:
    """
    Analyze a LaTeX file to find fields/commands that might need replacement
    
    Args:
        file_path: Path to .tex file
        
    Returns:
        Dictionary with field information
    """
    if not os.path.exists(file_path):
        return {}
    
    fields = {
        "commands": [],
        "environments": [],
        "custom_commands": [],
        "placeholders": []
    }
    
    # Read file content
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # Find LaTeX commands from our CV_COMMANDS list
    for cmd in CV_COMMANDS:
        pattern = fr'\\{cmd}\s*{{\s*([^}}]*)\s*}}'
        matches = re.findall(pattern, content)
        if matches:
            for match in matches:
                fields["commands"].append({
                    "command": cmd,
                    "value": match.strip()
                })
    
    # Find environments related to CV sections
    env_pattern = r'\\begin\{(\w+)[^}]*\}(.*?)\\end\{\1\}'
    for match in re.finditer(env_pattern, content, re.DOTALL):
        env_name = match.group(1)
        env_content = match.group(2)
        
        # Only include relevant CV environments
        cv_env_names = ['education', 'experience', 'skills', 'projects', 'publications', 'awards']
        if any(name in env_name.lower() for name in cv_env_names):
            fields["environments"].append({
                "name": env_name,
                "sample_content": env_content[:100] + ('...' if len(env_content) > 100 else '')
            })
    
    # Find custom command definitions
    custom_cmd_pattern = r'\\newcommand\s*{\\(\w+)}\s*\[?.*?\]?\s*{([^}]*)}'
    for match in re.finditer(custom_cmd_pattern, content):
        cmd_name = match.group(1)
        cmd_def = match.group(2)
        fields["custom_commands"].append({
            "name": cmd_name,
            "definition": cmd_def[:100] + ('...' if len(cmd_def) > 100 else '')
        })
    
    # Look for common placeholder patterns
    placeholders = set()
    for pattern in PLACEHOLDER_PATTERNS:
        matches = re.findall(pattern, content, re.IGNORECASE)
        for match in matches:
            placeholders.add(match)
    
    fields["placeholders"] = list(placeholders)
    
    return fields