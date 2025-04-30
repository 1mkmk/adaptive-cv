"""
Functions for filling LaTeX templates with user data.

This module contains functions for filling LaTeX templates with user data,
replacing placeholders and commands with actual content.
"""

import os
import re
import shutil
import logging
from typing import Dict, Any, List

from ..fill_template import escape_latex, prepare_address_format, safe_template_value

logger = logging.getLogger(__name__)

def fill_file(input_path: str, output_path: str, template_data: Dict[str, Any]) -> bool:
    """
    Fill a single LaTeX file with user data (traditional method, fallback when AI is not available)
    
    Args:
        input_path: Path to input LaTeX file
        output_path: Path to output LaTeX file
        template_data: User data to fill the template with
        
    Returns:
        Boolean indicating if any changes were made
    """
    if not os.path.exists(input_path):
        return False
    
    # Read input file
    with open(input_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    original_content = content
    modified = False
    
    # Process common CV commands
    for field, value in template_data.items():
        # Skip empty or non-string values for simple replacement
        if not value or not isinstance(value, str):
            continue
        
        # Try multiple variants of the field name
        field_variants = [field]
        if field == 'name':
            field_variants.extend(['fullname', 'firstname'])
        elif field == 'email':
            field_variants.append('mail')
        elif field == 'phone':
            field_variants.extend(['telephone', 'mobile', 'cell'])
        elif field == 'address':
            field_variants.extend(['location', 'city', 'country'])
        elif field == 'profile_summary':
            field_variants.extend(['summary', 'objective', 'about', 'personal', 'bio'])
            
        # Special case for address formatting - handle differently
        if field == 'address' and 'email' in template_data:
            # Handle special formatting for address and email/linkedin
            address_lines = prepare_address_format(
                value, 
                template_data.get('email'), 
                template_data.get('linkedin')
            )
            
            # Look for any address commands
            address_patterns = [fr'\\address\s*{{\s*[^}}]*\s*}}' for _ in range(len(address_lines))]
            
            # Find all address command instances
            address_matches = []
            for pattern in address_patterns:
                matches = list(re.finditer(pattern, content))
                address_matches.extend(matches)
            
            # Sort by position in the content
            address_matches.sort(key=lambda m: m.start())
            
            # Replace with formatted address values
            for i, match in enumerate(address_matches[:len(address_lines)]):
                safe_value = safe_template_value(address_lines[i])
                replacement = f'\\address{{{safe_value}}}'
                span = match.span()
                content = content[:span[0]] + replacement + content[span[1]:]
                modified = True
            
            continue  # Skip normal processing for address
        
        # Regular replacement for other fields
        for variant in field_variants:
            pattern = fr'\\{variant}\s*{{\s*[^}}]*\s*}}'
            if re.search(pattern, content):
                # Use safe template value to handle escaping properly
                safe_value = safe_template_value(value)
                replacement = f'\\{variant}{{{safe_value}}}'
                content = re.sub(pattern, replacement, content)
                modified = True
                logger.debug(f"Replaced \\{variant}{{...}} with '{safe_value}' in {os.path.basename(input_path)}")
    
    # Handle complex sections if needed (education, experience, etc.)
    for section in ['experience', 'education', 'skills', 'languages', 'certifications', 'projects']:
        if section in template_data and isinstance(template_data[section], list) and template_data[section]:
            content = process_section(content, section, template_data[section])
            modified = True
    
    # Only write if content was modified
    if modified:
        # Ensure the output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Write output file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        logger.info(f"Filled template file: {output_path}")
        
        return True
    
    return False

def process_section(content: str, section_name: str, section_data: List[Dict[str, Any]]) -> str:
    """
    Process a complex section of the CV (experience, education, etc.)
    
    This is a placeholder implementation. In a real-world scenario, this would
    need to understand the specific structure of each template and section.
    
    Args:
        content: LaTeX file content
        section_name: Name of the section (experience, education, etc.)
        section_data: List of dictionaries with section data
        
    Returns:
        Modified LaTeX content
    """
    # For now, we'll just leave this as a placeholder. In a real implementation,
    # we would need to analyze the template's structure for each section and generate
    # the appropriate LaTeX code based on the data.
    
    # This would require template-specific logic, as different templates structure
    # these sections differently.
    
    logger.info(f"Processing {section_name} section with {len(section_data)} items")
    
    return content