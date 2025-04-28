"""
Functions for AI-based template analysis.

This module contains functions for analyzing templates using OpenAI to generate
comprehensive analysis data.
"""

import logging
from typing import Dict, Any, List

# Import functions from the new modules
from .directory_utils import get_correct_output_dir
from .json_handler import (
    create_profile_json,
    create_job_requirements_json,
    create_merged_json,
    save_template_json
)
from .openai_analyzer import generate_ai_template_analysis
from .ai_template_filler import ai_fill_template

logger = logging.getLogger(__name__)

# Alias the original _get_correct_output_dir function to maintain backward compatibility
_get_correct_output_dir = get_correct_output_dir

# The main module now primarily re-exports the functions from the specialized modules
__all__ = [
    'generate_ai_template_analysis',
    'create_merged_json',
    'ai_fill_template',
    '_get_correct_output_dir',  # Keep for backward compatibility
]