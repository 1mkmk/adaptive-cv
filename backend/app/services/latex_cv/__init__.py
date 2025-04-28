"""
LaTeX CV generator package.

This package contains modules for generating LaTeX CV documents
and compiling them to PDF.
"""

from .config import (
    BASE_DIR, ASSETS_DIR, TEMPLATE_DIR, 
    LATEX_OUTPUT_DIR, PDF_OUTPUT_DIR,
    TEMPLATES_EXTRACTED_DIR, TEMPLATES_ZIPPED_DIR
)
from .compilation import LaTeXCompiler
from .template_utils import get_available_templates, normalize_template_id
from .document_builder import LaTeXDocumentBuilder
from .template_analyzer import TemplateAnalyzer
from .generator import LaTeXCVGenerator

__all__ = [
    'LaTeXCVGenerator',
    'LaTeXCompiler',
    'LaTeXDocumentBuilder',
    'TemplateAnalyzer',
    'get_available_templates',
    'normalize_template_id',
    'BASE_DIR',
    'ASSETS_DIR',
    'TEMPLATE_DIR',
    'LATEX_OUTPUT_DIR',
    'PDF_OUTPUT_DIR',
    'TEMPLATES_EXTRACTED_DIR',
    'TEMPLATES_ZIPPED_DIR'
]