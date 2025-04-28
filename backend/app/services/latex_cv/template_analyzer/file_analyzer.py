"""
Functions for analyzing LaTeX file structure.

This module contains functions for identifying main LaTeX files and their dependencies.
"""

import os
import re
import logging
from typing import List, Tuple, Optional

logger = logging.getLogger(__name__)

def identify_main_file(tex_files: List[str]) -> Tuple[Optional[str], str]:
    """
    Find the main LaTeX file from a list of .tex files
    
    Args:
        tex_files: List of .tex file paths
        
    Returns:
        Tuple with (main file path, document structure type)
    """
    # Sort by likelihood of being the main file
    candidates = []
    
    for file_path in tex_files:
        # Check if file contains document environment
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
            # Check for document environment
            has_document = '\\begin{document}' in content and '\\end{document}' in content
            
            # Check for common main file names
            file_name = os.path.basename(file_path).lower()
            name_score = 0
            for name in ['main', 'cv', 'resume', 'template', 'index']:
                if name in file_name:
                    name_score += 1
            
            # Determine document structure
            structure = "unknown"
            if has_document:
                if "\\documentclass{article}" in content:
                    structure = "article"
                elif "\\documentclass{resume}" in content:
                    structure = "resume"
                elif "\\documentclass{cv}" in content:
                    structure = "cv"
                elif "\\documentclass" in content:
                    # Extract the class name
                    class_match = re.search(r'\\documentclass(?:\[.*?\])?\{(.*?)\}', content)
                    if class_match:
                        structure = class_match.group(1)
                else:
                    structure = "custom"
            
            candidates.append((file_path, has_document, name_score, structure))
    
    # Filter and sort candidates
    doc_candidates = [c for c in candidates if c[1]]  # Has document environment
    
    if doc_candidates:
        # Sort by name score (higher is better)
        doc_candidates.sort(key=lambda x: x[2], reverse=True)
        return doc_candidates[0][0], doc_candidates[0][3]
    
    # If no document environment found, try to find the most promising file
    if candidates:
        candidates.sort(key=lambda x: x[2], reverse=True)
        return candidates[0][0], "incomplete"
    
    return None, "unknown"

def check_if_included(main_file: str, file_path: str) -> bool:
    """
    Check if a file is included or imported by the main file
    
    Args:
        main_file: Path to main .tex file
        file_path: Path to file to check
        
    Returns:
        Boolean indicating if the file is included
    """
    if not main_file or not os.path.exists(main_file):
        return False
    
    rel_path = os.path.relpath(file_path, os.path.dirname(main_file))
    file_name = os.path.basename(file_path)
    file_name_no_ext = os.path.splitext(file_name)[0]
    
    # Read main file content
    with open(main_file, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # Check for various include/input patterns
    include_patterns = [
        fr'\\include\s*{{\s*{re.escape(file_name_no_ext)}\s*}}',
        fr'\\input\s*{{\s*{re.escape(file_name_no_ext)}\s*}}',
        fr'\\input\s*{{\s*{re.escape(file_name)}\s*}}',
        fr'\\import\s*{{\s*[^{{}}]*\s*}}\s*{{\s*{re.escape(file_name)}\s*}}',
        fr'\\subimport\s*{{\s*[^{{}}]*\s*}}\s*{{\s*{re.escape(file_name)}\s*}}'
    ]
    
    for pattern in include_patterns:
        if re.search(pattern, content):
            return True
    
    return False