"""
LaTeX document builder module.

This module is responsible for creating LaTeX documents from templates and data.
"""

import os
import re
import shutil
import logging
import traceback
from pathlib import Path
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

class LaTeXDocumentBuilder:
    """Class responsible for creating LaTeX documents from templates and data"""
    
    def __init__(self, template_dir=None):
        """Initialize the LaTeX document builder"""
        self.template_dir = template_dir
    
    def _find_main_tex_file(self, files_dir):
        """Find the main TeX file in a directory of template files"""
        if not os.path.exists(files_dir):
            return None
            
        # Check for common main file names
        common_names = ["main.tex", "cv.tex", "resume.tex", "template.tex"]
        for name in common_names:
            if os.path.exists(os.path.join(files_dir, name)):
                return name
                
        # Otherwise, find all .tex files and return the first one
        tex_files = [f for f in os.listdir(files_dir) if f.endswith('.tex')]
        if tex_files:
            # Prioritize files that might be the main document
            for tex_file in tex_files:
                # Check if file contains document environment, which indicates it's a main file
                file_path = os.path.join(files_dir, tex_file)
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        if '\\begin{document}' in content and '\\end{document}' in content:
                            return tex_file
                except Exception as e:
                    logger.warning(f"Error reading {tex_file}: {e}")
                    continue
            
            # If no main file identified, just return the first .tex file
            return tex_files[0]
        
        return None
    
    def create_fallback_template(self, output_dir, template_data):
        """
        Create a basic LaTeX template when no template is found
        
        Args:
            output_dir: Directory to write the template
            template_data: CV data to include in the template
            
        Returns:
            Path to the created LaTeX file
        """
        # Ensure the output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Create a simple LaTeX template with the CV data
        with open(os.path.join(output_dir, 'cv.tex'), 'w', encoding='utf-8') as f:
            f.write(r'\documentclass{article}' + '\n')
            f.write(r'\usepackage[utf8]{inputenc}' + '\n')
            f.write(r'\usepackage[margin=1in]{geometry}' + '\n')
            f.write(r'\usepackage{hyperref}' + '\n')
            
            # Title and basic info
            f.write(r'\title{Curriculum Vitae}' + '\n')
            f.write(f'\\author{{{template_data.get("name", "Candidate Name")}}}' + '\n')
            f.write(r'\date{\today}' + '\n\n')
            
            # Start document
            f.write(r'\begin{document}' + '\n')
            f.write(r'\maketitle' + '\n\n')
            
            # Personal info
            f.write(r'\section*{Personal Information}' + '\n')
            f.write(r'\begin{description}' + '\n')
            
            for field, label in [
                ('name', 'Name'),
                ('email', 'Email'),
                ('phone', 'Phone'),
                ('address', 'Address'),
                ('website', 'Website'),
                ('linkedin', 'LinkedIn'),
                ('github', 'GitHub')
            ]:
                if template_data.get(field):
                    f.write(f'\\item[{label}:] {template_data.get(field)}' + '\n')
            
            f.write(r'\end{description}' + '\n\n')
            
            # Profile summary
            if template_data.get('profile_summary'):
                f.write(r'\section*{Profile Summary}' + '\n')
                f.write(f'{template_data.get("profile_summary")}' + '\n\n')
            
            # Experience section
            if template_data.get('experience'):
                f.write(r'\section*{Professional Experience}' + '\n')
                
                for exp in template_data.get('experience', []):
                    title = exp.get('title', '')
                    company = exp.get('company', '')
                    location = exp.get('location', '')
                    start_date = exp.get('start_date', '')
                    end_date = exp.get('end_date', '')
                    description = exp.get('description', '')
                    
                    # Format the heading with job title, company, and dates
                    f.write(f'\\textbf{{{title}}} at {company}')
                    if location:
                        f.write(f', {location}')
                    if start_date:
                        f.write(f' ({start_date}')
                        if end_date:
                            f.write(f' - {end_date}')
                        f.write(')')
                    f.write('\n\n')
                    
                    # Description may contain bullet points, try to format them
                    if description:
                        if isinstance(description, list):
                            f.write('\\begin{itemize}\n')
                            for bullet in description:
                                f.write(f'\\item {bullet}\n')
                            f.write('\\end{itemize}\n\n')
                        else:
                            # Split by new lines and create bullet points
                            bullets = description.split('\n')
                            if len(bullets) > 1:
                                f.write('\\begin{itemize}\n')
                                for bullet in bullets:
                                    bullet = bullet.strip()
                                    if bullet:
                                        # Remove bullet points if they exist
                                        bullet = bullet.lstrip('•').lstrip('-').lstrip('*').strip()
                                        f.write(f'\\item {bullet}\n')
                                f.write('\\end{itemize}\n\n')
                            else:
                                f.write(f'{description}\n\n')
            
            # Education section
            if template_data.get('education'):
                f.write(r'\section*{Education}' + '\n')
                
                for edu in template_data.get('education', []):
                    degree = edu.get('degree', '')
                    institution = edu.get('institution', '')
                    location = edu.get('location', '')
                    start_date = edu.get('start_date', '')
                    end_date = edu.get('end_date', '')
                    description = edu.get('description', '')
                    
                    # Format the heading with degree, institution, and dates
                    f.write(f'\\textbf{{{degree}}} at {institution}')
                    if location:
                        f.write(f', {location}')
                    if start_date:
                        f.write(f' ({start_date}')
                        if end_date:
                            f.write(f' - {end_date}')
                        f.write(')')
                    f.write('\n\n')
                    
                    # Description
                    if description:
                        f.write(f'{description}\n\n')
            
            # Skills section
            if template_data.get('skills'):
                f.write(r'\section*{Skills}' + '\n')
                
                # Group skills by category if available
                skills_by_category = {}
                for skill in template_data.get('skills', []):
                    category = skill.get('category', 'Other')
                    if category not in skills_by_category:
                        skills_by_category[category] = []
                    skills_by_category[category].append(skill)
                
                # If no categories, just list all skills
                if len(skills_by_category) <= 1:
                    f.write(r'\begin{itemize}' + '\n')
                    for skill in template_data.get('skills', []):
                        skill_name = skill.get('name', '')
                        skill_level = skill.get('level', '')
                        if skill_level:
                            f.write(f'\\item {skill_name} ({skill_level})' + '\n')
                        else:
                            f.write(f'\\item {skill_name}' + '\n')
                    f.write(r'\end{itemize}' + '\n\n')
                else:
                    # List skills by category
                    for category, skills in skills_by_category.items():
                        f.write(f'\\textbf{{{category}}}:\n')
                        f.write(r'\begin{itemize}' + '\n')
                        for skill in skills:
                            skill_name = skill.get('name', '')
                            skill_level = skill.get('level', '')
                            if skill_level:
                                f.write(f'\\item {skill_name} ({skill_level})' + '\n')
                            else:
                                f.write(f'\\item {skill_name}' + '\n')
                        f.write(r'\end{itemize}' + '\n\n')
            
            # Languages section
            if template_data.get('languages'):
                f.write(r'\section*{Languages}' + '\n')
                f.write(r'\begin{itemize}' + '\n')
                
                for lang in template_data.get('languages', []):
                    name = lang.get('name', '')
                    level = lang.get('level', '')
                    f.write(f'\\item {name} ({level})' + '\n')
                
                f.write(r'\end{itemize}' + '\n\n')
            
            # End document
            f.write(r'\end{document}' + '\n')
        
        return os.path.join(output_dir, 'cv.tex')
    
    def create_latex_file(self, template_data, output_dir, files_dir):
        """
        Create a LaTeX file from template data
        
        Args:
            template_data: Dictionary with CV content
            output_dir: Directory to output the LaTeX file
            files_dir: Directory with template files
            
        Returns:
            Path to generated LaTeX file
        """
        # Ensure the output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Find main tex file
        main_tex = self._find_main_tex_file(files_dir)
        
        # If no main TEX file found, use a default template
        if not main_tex or not os.path.exists(os.path.join(files_dir, main_tex)):
            logger.warning(f"No main TEX file found in {files_dir}. Using fallback template.")
            return self.create_fallback_template(output_dir, template_data)
        
        # Template exists, copy it and modify the content based on the CV data
        main_tex_path = os.path.join(files_dir, main_tex)
        logger.info(f"Using template file: {main_tex_path}")
        
        # Read the template file
        with open(main_tex_path, 'r', encoding='utf-8', errors='ignore') as f:
            template_content = f.read()
        
        # Create modified content
        modified_content = template_content
        
        # Update personal information
        # This is a simplified approach - in reality, each template may have different commands
        for field, pattern in [
            ('name', r'\\name\{[^}]*\}'),
            ('email', r'\\email\{[^}]*\}'),
            ('phone', r'\\phone\{[^}]*\}'),
            ('address', r'\\address\{[^}]*\}'),
            ('profile_summary', r'\\profilesummary\{[^}]*\}'),
            ('website', r'\\website\{[^}]*\}'),
            ('linkedin', r'\\linkedin\{[^}]*\}'),
            ('github', r'\\github\{[^}]*\}')
        ]:
            if template_data.get(field):
                # Check if pattern exists in the content
                if re.search(pattern, modified_content):
                    # Use raw string and double backslash to ensure correct escaping
                    modified_content = re.sub(
                        pattern,
                        f"\\\\{field}{{{template_data.get(field)}}}",
                        modified_content
                    )
                    logger.debug(f"Replaced {field} with '{template_data.get(field)}'")
                else:
                    logger.warning(f"Pattern for {field} not found in template")
        
        # Write the modified content to the output directory
        with open(os.path.join(output_dir, 'cv.tex'), 'w', encoding='utf-8') as f:
            f.write(modified_content)
        
        # Also copy any supporting files (cls, sty, etc.)
        for file in os.listdir(files_dir):
            if file.endswith(('.cls', '.sty')):
                shutil.copy2(os.path.join(files_dir, file), output_dir)
        
        return os.path.join(output_dir, 'cv.tex')
            
    def create_debug_file(self, output_dir, template_name, job_title, company_name, template_data):
        """
        Create a debug file with template information for troubleshooting
        
        Args:
            output_dir: Directory to write the debug file
            template_name: Name of the template
            job_title: Title of the job
            company_name: Name of the company
            template_data: CV data used to generate the CV
            
        Returns:
            Path to the created debug file
        """
        debug_file = os.path.join(output_dir, "debug.tex")
        
        try:
            with open(debug_file, "w", encoding="utf-8") as f:
                f.write("% Debug information for template generation\n\n")
                f.write(f"Template: {template_name}\n")
                f.write(f"Job: {job_title} at {company_name}\n\n")
                f.write("% Template data:\n")
                for key, value in template_data.items():
                    f.write(f"% {key}: {value}\n")
            
            return debug_file
        except Exception as e:
            logger.error(f"Error creating debug file: {e}")
            return None