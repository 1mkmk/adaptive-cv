"""
Base template analyzer class.

This module contains the main TemplateAnalyzer class that integrates all the functionality
from the other modules to analyze and fill LaTeX templates.
"""

import os
import re
import shutil
import logging
from typing import Dict, Any, List, Tuple, Optional, Set

from .file_analyzer import identify_main_file, check_if_included
from .field_detector import analyze_file_for_fields
from .ai_analyzer import generate_ai_template_analysis, ai_fill_template
from .template_filler import fill_file
from .debug_reporter import generate_debug_report

logger = logging.getLogger(__name__)

class TemplateAnalyzer:
    """Analyzes LaTeX templates and fills them with user data"""

    def __init__(self):
        """Initialize the template analyzer"""
        pass

    def analyze_template_directory(self, template_dir: str, job_description: str = None, 
                                  template_data: Dict[str, Any] = None, template_name: str = None) -> Dict[str, Any]:
        """
        Analyze a template directory to identify main files and fields
        
        Args:
            template_dir: Path to template directory
            job_description: Optional job description text for AI analysis
            template_data: Optional candidate profile data for AI analysis
            template_name: Optional template name for reference
            
        Returns:
            Dictionary with template analysis information including AI-generated debug data
        """
        if not os.path.exists(template_dir):
            logger.error(f"Template directory not found: {template_dir}")
            return {"error": "Template directory not found"}
        
        logger.info(f"Analyzing template directory: {template_dir}")
        
        result = {
            "path": template_dir,
            "main_files": [],
            "support_files": [],
            "detected_fields": {},
            "structure": "unknown"
        }
        
        # Collect all template files
        tex_files = []
        support_files = []
        for root, _, files in os.walk(template_dir):
            for file in files:
                file_path = os.path.join(root, file)
                if file.endswith('.tex'):
                    tex_files.append(file_path)
                elif file.endswith(('.cls', '.sty')):
                    support_files.append(file_path)
        
        # Analyze structure to find main files
        main_file, document_structure = identify_main_file(tex_files)
        if main_file:
            logger.info(f"Identified main file: {main_file}")
            result["main_files"].append(os.path.relpath(main_file, template_dir))
            result["structure"] = document_structure
        
        # Find other related template files
        for file_path in tex_files:
            if file_path != main_file:
                # Check if the file is included in the main file
                included = check_if_included(main_file, file_path)
                if included:
                    rel_path = os.path.relpath(file_path, template_dir)
                    logger.info(f"Found included file: {rel_path}")
                    result["main_files"].append(rel_path)
        
        # Add support files
        for file_path in support_files:
            rel_path = os.path.relpath(file_path, template_dir)
            result["support_files"].append(rel_path)
        
        # Analyze all files to find fields
        for file_path in tex_files:
            rel_path = os.path.relpath(file_path, template_dir)
            fields = analyze_file_for_fields(file_path)
            if fields:
                result["detected_fields"][rel_path] = fields
        
        # If we have job description and template data, use OpenAI to generate comprehensive debug.json
        if job_description and template_data and template_name:
            try:
                ai_analysis = generate_ai_template_analysis(
                    result, job_description, template_data, template_name
                )
                if ai_analysis:
                    # Merge AI analysis with our basic template info
                    result.update(ai_analysis)
            except Exception as e:
                logger.error(f"Error generating AI template analysis: {str(e)}")
        
        return result

    def fill_template(self, template_dir: str, output_dir: str, template_data: Dict[str, Any], 
                     job_description: str = None, template_name: str = None) -> Dict[str, Any]:
        """
        Fill a template with user data using AI for enhanced analysis and filling
        
        Args:
            template_dir: Path to source template directory
            output_dir: Path to output directory
            template_data: User data to fill the template with
            job_description: Optional job description for AI analysis
            template_name: Optional template name for reference
            
        Returns:
            Dictionary with information about the filled template
        """
        # Analyze the template with AI if job description is provided
        template_info = self.analyze_template_directory(
            template_dir, 
            job_description=job_description,
            template_data=template_data,
            template_name=template_name
        )
        
        # Add output_dir to template_info so it's available for AI analysis
        template_info["output_dir"] = output_dir
        
        # Create output directories
        os.makedirs(output_dir, exist_ok=True)
        
        # Copy all files from template directory to output directory
        for item in os.listdir(template_dir):
            s = os.path.join(template_dir, item)
            d = os.path.join(output_dir, item)
            if os.path.isdir(s):
                shutil.copytree(s, d, dirs_exist_ok=True)
            else:
                shutil.copy2(s, d)
        
        # If we have AI analysis from template_info, use it to generate LaTeX content
        if job_description and template_name and "template_analysis" in template_info:
            # Use OpenAI to fill the template based on the analysis
            filled_files = ai_fill_template(template_dir, output_dir, template_data, template_info, job_description)
            
            # Create a result report
            result = {
                "template_info": template_info,
                "output_dir": output_dir,
                "modified_files": filled_files,
                "main_file": template_info.get("main_files", [""])[0] if template_info.get("main_files") else ""
            }
            
            return result
        else:
            # Fallback to traditional filling method if no AI analysis
            # Track which files we modified
            modified_files = []
            
            # Identify and fill main files first
            for rel_path in template_info.get("main_files", []):
                input_path = os.path.join(template_dir, rel_path)
                output_path = os.path.join(output_dir, rel_path)
                
                if fill_file(input_path, output_path, template_data):
                    modified_files.append(rel_path)
            
            # Look for any other detected fields in other files
            for rel_path, fields in template_info.get("detected_fields", {}).items():
                if rel_path not in template_info.get("main_files", []) and fields:
                    input_path = os.path.join(template_dir, rel_path)
                    output_path = os.path.join(output_dir, rel_path)
                    
                    if fill_file(input_path, output_path, template_data):
                        modified_files.append(rel_path)
            
            # Create a result report
            result = {
                "template_info": template_info,
                "output_dir": output_dir,
                "modified_files": modified_files,
                "main_file": template_info.get("main_files", [""])[0] if template_info.get("main_files") else ""
            }
            
            return result
  
    def generate_debug_report(self, template_info: Dict[str, Any], output_path: str) -> str:
        """
        Generate a debug report for a template analysis (delegated to debug_reporter module)
        
        Args:
            template_info: Template analysis information
            output_path: Path to save the report
            
        Returns:
            Path to the generated report
        """
        return generate_debug_report(template_info, output_path)