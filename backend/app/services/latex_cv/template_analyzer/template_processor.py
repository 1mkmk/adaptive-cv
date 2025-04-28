"""
Template processor for LaTeX CV templates.
Handles template loading, extraction, and analysis.
"""

import os
import shutil
import zipfile
import logging
from pathlib import Path
import json

from backend.app.services.latex_cv.config import (
    TEMPLATES_EXTRACTED_DIR, 
    TEMPLATES_ZIPPED_DIR,
    ALLOWED_TEMPLATE_EXTENSIONS,
    MAX_TEMPLATE_SIZE
)
from backend.app.services.latex_cv.template_analyzer.directory_utils import get_correct_output_dir

logger = logging.getLogger(__name__)

class TemplateProcessor:
    """Handles template extraction and processing"""
    
    def __init__(self):
        """Initialize the template processor"""
        self.extracted_dir = TEMPLATES_EXTRACTED_DIR
        self.zipped_dir = TEMPLATES_ZIPPED_DIR
        # Ensure directories exist
        Path(self.extracted_dir).mkdir(parents=True, exist_ok=True)
        Path(self.zipped_dir).mkdir(parents=True, exist_ok=True)
    
    def extract_template(self, template_zip_path, output_dir=None):
        """
        Extract a template from a zip file to the specified output directory.
        
        Args:
            template_zip_path (str): Path to the template zip file
            output_dir (str, optional): Directory to extract to. If None, extracts to templates_extracted
            
        Returns:
            str: Path to the extracted template directory
            
        Raises:
            ValueError: If the template zip file is invalid
            FileNotFoundError: If the template zip file doesn't exist
            PermissionError: If there's a permission issue
        """
        template_path = Path(template_zip_path)
        
        # Validate the template file
        if not template_path.exists():
            raise FileNotFoundError(f"Template file not found: {template_path}")
            
        if template_path.suffix.lower() not in ALLOWED_TEMPLATE_EXTENSIONS:
            raise ValueError(f"Invalid template file format: {template_path.suffix}. "
                            f"Allowed formats: {', '.join(ALLOWED_TEMPLATE_EXTENSIONS)}")
            
        if template_path.stat().st_size > MAX_TEMPLATE_SIZE:
            raise ValueError(f"Template file too large: {template_path.stat().st_size} bytes. "
                            f"Maximum allowed size: {MAX_TEMPLATE_SIZE} bytes")
        
        # Determine the output directory
        if output_dir:
            extract_dir = Path(output_dir)
        else:
            # Use the template name (without extension) as the directory name
            template_name = template_path.stem
            extract_dir = Path(self.extracted_dir) / template_name
        
        try:
            # Create the output directory if it doesn't exist
            extract_dir.mkdir(parents=True, exist_ok=True)
            
            # Extract the template
            with zipfile.ZipFile(template_path, 'r') as zip_ref:
                # Check for potential path traversal attacks (files trying to extract outside the target dir)
                for file_info in zip_ref.infolist():
                    if file_info.filename.startswith('..') or file_info.filename.startswith('/'):
                        raise ValueError(f"Invalid file path in zip: {file_info.filename}")
                
                zip_ref.extractall(extract_dir)
                logger.info(f"Extracted template to: {extract_dir}")
                
            return str(extract_dir)
            
        except zipfile.BadZipFile:
            raise ValueError(f"Invalid zip file: {template_path}")
        except PermissionError as e:
            raise PermissionError(f"Permission denied when extracting template: {str(e)}")
        except Exception as e:
            logger.error(f"Error extracting template: {str(e)}")
            raise
    
    def save_extracted_data(self, data, output_dir=None, filename="template.json"):
        """
        Save extracted template data to a JSON file.
        
        Args:
            data (dict): Template data to save
            output_dir (str, optional): Directory to save to
            filename (str, optional): Name of the output file
            
        Returns:
            str: Path to the saved file
        """
        # Determine the correct output directory
        save_dir = get_correct_output_dir(output_dir)
        save_dir_path = Path(save_dir)
        
        # Ensure the directory exists
        save_dir_path.mkdir(parents=True, exist_ok=True)
        
        # Create the full file path
        file_path = save_dir_path / filename
        
        try:
            # Save the data to a JSON file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved extracted data to: {file_path}")
            return str(file_path)
            
        except PermissionError as e:
            logger.error(f"Permission denied when saving extracted data: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error saving extracted data: {str(e)}")
            raise
            
    def list_available_templates(self):
        """
        List all available templates in the templates directory.
        
        Returns:
            list: List of template names
        """
        templates = []
        
        # Check extracted templates
        if Path(self.extracted_dir).exists():
            for item in Path(self.extracted_dir).iterdir():
                if item.is_dir():
                    templates.append(item.name)
        
        # Check zipped templates
        if Path(self.zipped_dir).exists():
            for item in Path(self.zipped_dir).iterdir():
                if item.is_file() and item.suffix.lower() in ALLOWED_TEMPLATE_EXTENSIONS:
                    templates.append(item.stem)
        
        return sorted(set(templates))  # Use a set to remove duplicates