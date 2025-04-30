"""
Functions for generating debug reports.

This module contains functions for generating debug reports about template analysis.
"""

import os
import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

def generate_debug_report(template_info: Dict[str, Any], output_path: str) -> str:
    """
    Generate a debug report for a template analysis
    
    Args:
        template_info: Template analysis information
        output_path: Path to save the report
        
    Returns:
        Path to the generated report
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Replace debug.tex with template.json
    template_json_path = output_path.replace(".tex", ".json")
    
    # Create JSON debug report
    debug_data = {
        "template": {
            "path": template_info.get('path'),
            "structure": template_info.get('structure', 'unknown'),
            "main_files": template_info.get("main_files", []),
            "support_files": template_info.get("support_files", [])
        },
        "detected_fields": {}
    }
    
    # Add detected fields
    for file, fields in template_info.get("detected_fields", {}).items():
        debug_data["detected_fields"][file] = {
            "commands": fields.get("commands", []),
            "environments": fields.get("environments", []),
            "custom_commands": fields.get("custom_commands", []),
            "placeholders": fields.get("placeholders", [])
        }
    
    # Write JSON data
    with open(template_json_path, 'w', encoding='utf-8') as f:
        json.dump(debug_data, f, indent=2, ensure_ascii=False)
    
    # For backward compatibility, also create minimal debug.tex
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("% Template Analysis Debug Report - See template.json for full details\n\n")
        f.write(f"% Template path: {template_info.get('path')}\n")
        f.write(f"% Debug data stored in: {os.path.basename(template_json_path)}\n")
    
    return template_json_path