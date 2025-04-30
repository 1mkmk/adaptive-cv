"""
Template analyzer for LaTeX CV generator.

This module is responsible for analyzing LaTeX templates, detecting fields
that need to be replaced, and filling templates with user data.
"""

import os
import re
import shutil
import glob
import logging
import json
from typing import Dict, Any, List, Optional

# Import the OpenAI analyzer
from .template_analyzer.openai_analyzer import generate_ai_template_analysis

logger = logging.getLogger(__name__)

class TemplateAnalyzer:
    """
    Analyzes LaTeX templates and fills them with user data.
    """
    
    def __init__(self):
        """Initialize the template analyzer"""
        pass
        
    def analyze_template_directory(self, template_dir: str) -> Dict[str, Any]:
        """
        Analyze LaTeX template directory structure
        
        Args:
            template_dir: Path to template directory
            
        Returns:
            Dictionary with template structure information
        """
        template_info = {
            "dir_path": template_dir,
            "name": os.path.basename(template_dir),
            "tex_files": [],
            "cls_files": [],
            "sty_files": [],
            "image_files": [],
            "other_files": [],
            "commands": {},
            "sections": []
        }
        
        # Check for tex files
        tex_files = glob.glob(os.path.join(template_dir, "*.tex"))
        for tex_file in tex_files:
            try:
                with open(tex_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                template_info["tex_files"].append({
                    "name": os.path.basename(tex_file),
                    "path": tex_file,
                    "size": os.path.getsize(tex_file),
                    "has_document_env": "\\begin{document}" in content and "\\end{document}" in content
                })
            except Exception as e:
                logger.warning(f"Error analyzing tex file {tex_file}: {e}")
        
        # Check for class and style files
        cls_files = glob.glob(os.path.join(template_dir, "*.cls"))
        sty_files = glob.glob(os.path.join(template_dir, "*.sty"))
        
        template_info["cls_files"] = [os.path.basename(f) for f in cls_files]
        template_info["sty_files"] = [os.path.basename(f) for f in sty_files]
        
        # Check for image files
        img_extensions = ['.png', '.jpg', '.jpeg', '.pdf']
        for ext in img_extensions:
            img_files = glob.glob(os.path.join(template_dir, f"*{ext}"))
            template_info["image_files"].extend([os.path.basename(f) for f in img_files])
        
        # Find the main tex file (prioritize files with document environment)
        main_file = None
        for tex_file in template_info["tex_files"]:
            if tex_file["has_document_env"]:
                main_file = tex_file["path"]
                break
                
        if main_file is None and template_info["tex_files"]:
            main_file = template_info["tex_files"][0]["path"]
            
        if main_file:
            template_info["main_file"] = os.path.basename(main_file)
            
            # Extract sections and commands from the main file
            with open(main_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
                # Find sections
                section_pattern = r'\\(section|subsection|chapter)\{([^}]+)\}'
                sections = re.findall(section_pattern, content)
                if sections:
                    template_info["sections"] = [{"level": s[0], "title": s[1]} for s in sections]
                    
                # Find custom commands
                cmd_pattern = r'\\newcommand\{?\\([a-zA-Z]+)\}?'
                commands = re.findall(cmd_pattern, content)
                for cmd in commands:
                    template_info["commands"][cmd] = True
        
        return template_info
        
    def fill_template(self, template_dir: str, output_dir: str, template_data: Dict[str, Any], 
                       job_description: str = None, template_name: str = None) -> Dict[str, Any]:
        """
        Fill template with user data
        
        Args:
            template_dir: Path to template directory
            output_dir: Path to output directory
            template_data: User data for template
            job_description: Optional job description text
            template_name: Optional template name
            
        Returns:
            Dictionary with fill results
        """
        try:
            # Ensure output directory exists
            os.makedirs(output_dir, exist_ok=True)
            
            # Analyze template directory
            template_info = self.analyze_template_directory(template_dir)
            
            # Copy all template files to output directory
            for item in os.listdir(template_dir):
                src_path = os.path.join(template_dir, item)
                dst_path = os.path.join(output_dir, item)
                
                if os.path.isdir(src_path):
                    # Copy directories
                    shutil.copytree(src_path, dst_path, dirs_exist_ok=True)
                else:
                    # Copy files
                    shutil.copy2(src_path, dst_path)
            
            # Generate debug.json file
            debug_data = {
                "template_info": template_info,
                "profile_data_keys": list(template_data.keys())
            }
            
            debug_path = os.path.join(output_dir, 'debug.json')
            with open(debug_path, 'w', encoding='utf-8') as f:
                json.dump(debug_data, f, indent=2)
            
            # Find the main tex file
            main_file = None
            if "main_file" in template_info:
                main_file = os.path.join(output_dir, template_info["main_file"])
            else:
                # Look for any .tex file with document environment
                tex_files = glob.glob(os.path.join(output_dir, "*.tex"))
                for tex_file in tex_files:
                    with open(tex_file, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        if "\\begin{document}" in content and "\\end{document}" in content:
                            main_file = tex_file
                            break
                
                # If no document environment found, use the first .tex file
                if main_file is None and tex_files:
                    main_file = tex_files[0]
            
            # Create CV file
            cv_file = os.path.join(output_dir, "cv.tex")
            if main_file and os.path.exists(main_file):
                # Copy main file to cv.tex if it's not already cv.tex
                if os.path.basename(main_file) != "cv.tex":
                    shutil.copy2(main_file, cv_file)
            
            # Return the results
            return {
                "template_info": template_info,
                "output_dir": output_dir,
                "cv_file": cv_file if os.path.exists(cv_file) else None
            }
            
        except Exception as e:
            logger.error(f"Error filling template: {e}")
            return {
                "error": str(e),
                "output_dir": output_dir
            }
    
    def generate_debug_report(self, template_info: Dict[str, Any], output_path: str) -> None:
        """
        Generate debug report from template analysis
        
        Args:
            template_info: Template structure information
            output_path: Path to save debug report
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("% LaTeX CV Template Debug Report\n")
                f.write("% Generated by Adaptive CV\n\n")
                
                f.write("\\documentclass{article}\n")
                f.write("\\usepackage{longtable}\n")
                f.write("\\usepackage{array}\n")
                f.write("\\begin{document}\n\n")
                
                # Template summary
                f.write("\\section*{Template Summary}\n")
                f.write("\\begin{tabular}{ll}\n")
                f.write("Template Name & " + template_info.get("name", "Unknown") + " \\\\\n")
                f.write("Main File & " + template_info.get("main_file", "None") + " \\\\\n")
                f.write("TeX Files & " + str(len(template_info.get("tex_files", []))) + " \\\\\n")
                f.write("Class Files & " + str(len(template_info.get("cls_files", []))) + " \\\\\n")
                f.write("Style Files & " + str(len(template_info.get("sty_files", []))) + " \\\\\n")
                f.write("Image Files & " + str(len(template_info.get("image_files", []))) + " \\\\\n")
                f.write("\\end{tabular}\n\n")
                
                # TeX files
                if template_info.get("tex_files"):
                    f.write("\\section*{TeX Files}\n")
                    f.write("\\begin{longtable}{llc}\n")
                    f.write("Filename & Size & Has Document Env \\\\\n")
                    f.write("\\hline\n")
                    
                    for tex_file in template_info.get("tex_files", []):
                        name = tex_file.get("name", "Unknown")
                        size = tex_file.get("size", 0)
                        has_doc = "Yes" if tex_file.get("has_document_env") else "No"
                        f.write(f"{name} & {size} bytes & {has_doc} \\\\\n")
                        
                    f.write("\\end{longtable}\n\n")
                
                # Sections
                if template_info.get("sections"):
                    f.write("\\section*{Document Sections}\n")
                    f.write("\\begin{longtable}{ll}\n")
                    f.write("Level & Title \\\\\n")
                    f.write("\\hline\n")
                    
                    for section in template_info.get("sections", []):
                        level = section.get("level", "Unknown")
                        title = section.get("title", "Unknown")
                        f.write(f"{level} & {title} \\\\\n")
                        
                    f.write("\\end{longtable}\n\n")
                
                # Custom commands
                if template_info.get("commands"):
                    f.write("\\section*{Custom Commands}\n")
                    f.write("\\begin{longtable}{l}\n")
                    f.write("Command \\\\\n")
                    f.write("\\hline\n")
                    
                    for cmd in template_info.get("commands", {}):
                        f.write(f"\\textbackslash{cmd} \\\\\n")
                        
                    f.write("\\end{longtable}\n\n")
                
                f.write("\\end{document}\n")
        except Exception as e:
            logger.error(f"Error generating debug report: {e}")

# Export the TemplateAnalyzer class
__all__ = ['TemplateAnalyzer']