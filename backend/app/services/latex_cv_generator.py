import os
import shutil
import subprocess
import tempfile
import logging
import re
import time
from pathlib import Path
import json
from fastapi import HTTPException

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent.parent.parent.parent  # Path to project root
ASSETS_DIR = BASE_DIR / "assets"

# Directory for LaTeX templates
TEMPLATE_DIR = ASSETS_DIR / "templates"

# Directory for LaTeX output (temporary .tex files)
LATEX_OUTPUT_DIR = ASSETS_DIR / "generated" / "latex"

# Directory for PDF output (final PDF files)
PDF_OUTPUT_DIR = ASSETS_DIR / "generated" / "pdf"

# Directory for extracted templates
TEMPLATES_EXTRACTED_DIR = ASSETS_DIR / "templates_extracted"

# Create directories if they don't exist
os.makedirs(TEMPLATE_DIR, exist_ok=True)
os.makedirs(LATEX_OUTPUT_DIR, exist_ok=True)
os.makedirs(PDF_OUTPUT_DIR, exist_ok=True)
os.makedirs(TEMPLATES_EXTRACTED_DIR, exist_ok=True)

def get_available_templates():
    """
    Get a list of available LaTeX CV templates from templates_extracted directory
    
    Returns:
        List of template dictionaries with name, description and preview image path
    """
    templates = []
    
    # Scan the templates_extracted directory
    if not TEMPLATES_EXTRACTED_DIR.exists():
        logger.warning(f"Templates extracted directory not found: {TEMPLATES_EXTRACTED_DIR}")
        return templates
    
    # Look for template directories that contain a .tex file
    for item in TEMPLATES_EXTRACTED_DIR.iterdir():
        if item.is_dir():
            tex_files = list(item.glob("*.tex"))
            if tex_files:
                # Get the main .tex file
                main_tex = tex_files[0]
                
                # Get template name (folder name)
                template_name = item.name
                
                # Look for template preview image
                preview_image = None
                for img_ext in [".png", ".jpg", ".jpeg"]:
                    img_path = item / f"preview{img_ext}"
                    if img_path.exists():
                        preview_image = str(img_path)
                        break
                
                # Get template description if exists
                description = ""
                desc_file = item / "description.txt"
                if desc_file.exists():
                    with open(desc_file, "r") as f:
                        description = f.read().strip()
                else:
                    # Default description
                    description = f"LaTeX template: {template_name}"
                
                # Add template to list
                templates.append({
                    "name": template_name,
                    "path": str(main_tex),
                    "description": description,
                    "preview": preview_image
                })
    
    return templates

class LaTeXCVGenerator:
    """Service for generating LaTeX documents and compiling to PDF"""
    
    def __init__(self, template_path, output_dir_latex, output_dir_pdf):
        """Initialize the LaTeX CV Generator with template path and output directories"""
        self.template_path = template_path
        self.output_dir_latex = output_dir_latex
        self.output_dir_pdf = output_dir_pdf
        
        # Ensure output directories exist
        os.makedirs(output_dir_latex, exist_ok=True)
        os.makedirs(output_dir_pdf, exist_ok=True)
        
        logger.info("Using local LaTeX compilation")
    
    def compile_latex_locally(self, template_dir):
        """Compile LaTeX document locally"""
        try:
            # Change to template directory
            orig_dir = os.getcwd()
            os.chdir(template_dir)
            
            # Run pdflatex command
            logger.info(f"Compiling LaTeX document locally in {template_dir}")
            
            pdflatex_cmd = ["pdflatex", "-interaction=nonstopmode", "cv.tex"]
            result = subprocess.run(pdflatex_cmd, capture_output=True, text=True)
            
            # Run twice for references
            if os.path.exists("cv.pdf"):
                result = subprocess.run(pdflatex_cmd, capture_output=True, text=True)
            
            if result.returncode != 0 or not os.path.exists("cv.pdf"):
                logger.error(f"Failed to compile LaTeX document: {result.stderr}")
                
                # Try fallback if available
                if os.path.exists("fallback.tex"):
                    logger.info("Attempting to compile fallback.tex")
                    fallback_cmd = ["pdflatex", "-interaction=nonstopmode", "fallback.tex"]
                    result = subprocess.run(fallback_cmd, capture_output=True, text=True)
                    
                    if result.returncode == 0 and os.path.exists("fallback.pdf"):
                        # Rename fallback.pdf to cv.pdf
                        os.rename("fallback.pdf", "cv.pdf")
                        return True
                
                return False
            
            return True
        except Exception as e:
            logger.error(f"Error compiling LaTeX locally: {e}")
            return False
        finally:
            os.chdir(orig_dir)
    
    def generate_cv(self, template_name, job_title, company_name, template_data, output_id):
        """Generate CV from template using LaTeX"""
        try:
            # Create sanitized output directories
            # Replace unwanted characters and limit length
            sanitized_name = re.sub(r'[^a-zA-Z0-9_]', '_', job_title.lower())[:50]
            if company_name:
                sanitized_company = re.sub(r'[^a-zA-Z0-9_]', '_', company_name.lower())[:30]
                output_dirname = f"{sanitized_name}_{sanitized_company}_{time.strftime('%Y%m%d')}_{output_id[:8]}"
            else:
                output_dirname = f"{sanitized_name}_{time.strftime('%Y%m%d')}_{output_id[:8]}"
            
            latex_output_dir = os.path.join(self.output_dir_latex, output_dirname)
            pdf_output_dir = os.path.join(self.output_dir_pdf, output_dirname)
            
            # Create directories
            os.makedirs(latex_output_dir, exist_ok=True)
            os.makedirs(pdf_output_dir, exist_ok=True)
            
            # Get template directory
            template_dir = os.path.join(self.template_path, template_name)
            if not os.path.exists(template_dir):
                raise HTTPException(status_code=404, detail=f"Template '{template_name}' not found")
            
            # Copy template files to output directory
            files_output_dir = os.path.join(latex_output_dir, "files")
            os.makedirs(files_output_dir, exist_ok=True)
            for item in os.listdir(template_dir):
                if item.endswith('.tex') or item.endswith('.cls') or item.endswith('.sty'):
                    shutil.copy2(os.path.join(template_dir, item), files_output_dir)
            
            # Copy any subdirectories
            for item in os.listdir(template_dir):
                src_path = os.path.join(template_dir, item)
                if os.path.isdir(src_path):
                    dst_path = os.path.join(files_output_dir, item)
                    shutil.copytree(src_path, dst_path, dirs_exist_ok=True)
            
            # Create main LaTeX file from template data
            self.create_latex_file(template_data, latex_output_dir, files_output_dir)
            
            # Create debug file with the input data
            with open(os.path.join(latex_output_dir, 'debug.tex'), 'w', encoding='utf-8') as f:
                f.write('% Debug information - template data used for generation\n')
                f.write(json.dumps(template_data, indent=2))
            
            # Create fallback.tex if template has one
            fallback_template = os.path.join(template_dir, 'fallback.tex')
            if os.path.exists(fallback_template):
                shutil.copy2(fallback_template, os.path.join(latex_output_dir, 'fallback.tex'))
            
            # Process user's photo if it exists
            if 'photo' in template_data and template_data['photo']:
                photo_path = template_data['photo']
                if os.path.exists(photo_path):
                    # Create photos directory if it doesn't exist
                    photos_dir = os.path.join(files_output_dir, 'photos')
                    os.makedirs(photos_dir, exist_ok=True)
                    
                    # Copy photo to files directory with different extensions for compatibility
                    shutil.copy2(photo_path, os.path.join(files_output_dir, 'photo.jpg'))
                    shutil.copy2(photo_path, os.path.join(photos_dir, 'photo.jpg'))
                    
                    # Try alternative names that templates might use
                    for alt_name in ['profile', 'picture']:
                        try:
                            shutil.copy2(photo_path, os.path.join(files_output_dir, f'{alt_name}.jpg'))
                            shutil.copy2(photo_path, os.path.join(photos_dir, f'{alt_name}.jpg'))
                            
                            # Also create PNG versions
                            png_output = os.path.join(files_output_dir, f'{alt_name}.png')
                            png_photos_output = os.path.join(photos_dir, f'{alt_name}.png')
                            subprocess.run(['convert', photo_path, png_output], check=False)
                            subprocess.run(['convert', photo_path, png_photos_output], check=False)
                        except Exception as e:
                            logger.warning(f"Failed to create alternative photo name {alt_name}: {e}")
                    
                    # Try to create PNG version
                    try:
                        subprocess.run(['convert', photo_path, os.path.join(files_output_dir, 'photo.png')], check=False)
                        subprocess.run(['convert', photo_path, os.path.join(photos_dir, 'photo.png')], check=False)
                    except Exception as e:
                        logger.warning(f"Failed to convert photo to PNG: {e}")
            
            # Compile locally
            success = self.compile_latex_locally(latex_output_dir)
            if success:
                # Copy PDF to output directory
                shutil.copy2(os.path.join(latex_output_dir, 'cv.pdf'), os.path.join(pdf_output_dir, 'cv.pdf'))
            
            if not success:
                logger.error("LaTeX compilation failed")
                raise HTTPException(status_code=500, detail="Failed to compile LaTeX document")
            
            # Generate preview image
            try:
                preview_path = os.path.join(files_output_dir, 'preview.jpg')
                pdf_path = os.path.join(pdf_output_dir, 'cv.pdf')
                
                # Use pdftoppm or convert to create preview
                tools = [
                    ['pdftoppm', '-jpeg', '-singlefile', '-scale-to', '800', pdf_path, os.path.join(files_output_dir, 'preview')],
                    ['convert', '-density', '150', f'{pdf_path}[0]', '-quality', '90', '-resize', '800x', preview_path]
                ]
                
                for tool_cmd in tools:
                    try:
                        result = subprocess.run(tool_cmd, capture_output=True, text=True)
                        if result.returncode == 0 and os.path.exists(preview_path):
                            break
                    except Exception as e:
                        logger.warning(f"Failed to use {tool_cmd[0]} for preview: {e}")
            except Exception as e:
                logger.warning(f"Failed to generate preview: {e}")
            
            return {
                'success': True,
                'latex_path': latex_output_dir,
                'pdf_path': os.path.join(pdf_output_dir, 'cv.pdf'),
                'output_id': output_id
            }
        except Exception as e:
            logger.error(f"Error generating CV: {e}")
            raise HTTPException(status_code=500, detail=f"Error generating CV: {str(e)}")
    
    def create_latex_file(self, template_data, output_dir, files_dir):
        """Create main LaTeX file from template data"""
        # Find main template file
        main_tex_file = None
        structure_file = os.path.join(files_dir, "structure.tex")
        template_file = os.path.join(files_dir, "cv_15.tex")
        
        # Check which template file exists
        if os.path.exists(structure_file):
            main_tex_file = structure_file
        elif os.path.exists(template_file):
            main_tex_file = template_file
        
        if not main_tex_file:
            # If no template file found, look for any .tex file
            for file in os.listdir(files_dir):
                if file.endswith('.tex'):
                    main_tex_file = os.path.join(files_dir, file)
                    break
        
        if not main_tex_file:
            raise HTTPException(status_code=500, detail="No LaTeX template file found")
        
        # Read template file
        with open(main_tex_file, 'r', encoding='utf-8') as f:
            template_content = f.read()
        
        # Create main cv.tex file
        with open(os.path.join(output_dir, 'cv.tex'), 'w', encoding='utf-8') as f:
            # Include files from template directory
            f.write("% Generated LaTeX CV\n")
            f.write("% Using template: " + os.path.basename(main_tex_file) + "\n\n")
            
            # For structure.tex template, include it
            if os.path.basename(main_tex_file) == "structure.tex":
                f.write("\\input{files/structure}\n\n")
                
                # Create document with personalized content
                f.write("\\begin{document}\n\n")
                
                # Add personal info section
                f.write("% Personal information\n")
                f.write(f"\\name{{{template_data.get('name', 'Your Name')}}}\n")
                f.write(f"\\address{{{template_data.get('address', '')}}}\n")
                
                # Add contacts
                contacts = []
                if template_data.get('phone'):
                    contacts.append(f"\\phone{{{template_data.get('phone')}}}")
                if template_data.get('email'):
                    contacts.append(f"\\email{{{template_data.get('email')}}}")
                if template_data.get('website'):
                    contacts.append(f"\\homepage{{{template_data.get('website')}}}")
                if template_data.get('github'):
                    contacts.append(f"\\github{{{template_data.get('github')}}}")
                if template_data.get('linkedin'):
                    contacts.append(f"\\linkedin{{{template_data.get('linkedin')}}}")
                
                f.write("\n% Contact information\n")
                for contact in contacts:
                    f.write(contact + "\n")
                
                # Add profile section
                if template_data.get('profile_summary'):
                    f.write("\n% Profile summary\n")
                    f.write("\\begin{quote}\n")
                    f.write(template_data.get('profile_summary', '') + "\n")
                    f.write("\\end{quote}\n")
                
                # Add experience section
                if template_data.get('experience'):
                    f.write("\n% Experience section\n")
                    f.write("\\section{Experience}\n\n")
                    
                    for job in template_data.get('experience', []):
                        f.write("\\begin{entrylist}\n")
                        job_title = job.get('title', '')
                        company = job.get('company', '')
                        location = job.get('location', '')
                        start_date = job.get('start_date', '')
                        end_date = job.get('end_date', 'Present')
                        description = job.get('description', '')
                        
                        date_range = f"{start_date}--{end_date}"
                        
                        f.write(f"\\entry\n")
                        f.write(f"  {{{date_range}}}\n")
                        f.write(f"  {{{job_title}}}\n")
                        f.write(f"  {{{company}}}\n")
                        f.write(f"  {{{location}}}\n")
                        f.write(f"  {{{description}}}\n")
                        f.write("\\end{entrylist}\n\n")
                
                # Add education section
                if template_data.get('education'):
                    f.write("\n% Education section\n")
                    f.write("\\section{Education}\n\n")
                    
                    for edu in template_data.get('education', []):
                        f.write("\\begin{entrylist}\n")
                        degree = edu.get('degree', '')
                        institution = edu.get('institution', '')
                        location = edu.get('location', '')
                        start_date = edu.get('start_date', '')
                        end_date = edu.get('end_date', 'Present')
                        description = edu.get('description', '')
                        
                        date_range = f"{start_date}--{end_date}"
                        
                        f.write(f"\\entry\n")
                        f.write(f"  {{{date_range}}}\n")
                        f.write(f"  {{{degree}}}\n")
                        f.write(f"  {{{institution}}}\n")
                        f.write(f"  {{{location}}}\n")
                        f.write(f"  {{{description}}}\n")
                        f.write("\\end{entrylist}\n\n")
                
                # Add skills section
                if template_data.get('skills'):
                    f.write("\n% Skills section\n")
                    f.write("\\section{Skills}\n\n")
                    
                    skills_by_category = {}
                    for skill in template_data.get('skills', []):
                        category = skill.get('category', 'Other')
                        name = skill.get('name', '')
                        level = skill.get('level', '')
                        
                        if category not in skills_by_category:
                            skills_by_category[category] = []
                        
                        skills_by_category[category].append((name, level))
                    
                    for category, skills in skills_by_category.items():
                        f.write(f"\\subsection{{{category}}}\n")
                        
                        for skill_name, skill_level in skills:
                            # Different templates use different skill formats
                            # Try to accomodate by using a simple list
                            f.write(f"\\skill{{{skill_name}}}{{{skill_level}}}\n")
                        
                        f.write("\n")
                
                # Add certifications
                if template_data.get('certifications'):
                    f.write("\n% Certifications section\n")
                    f.write("\\section{Certifications}\n\n")
                    
                    f.write("\\begin{entrylist}\n")
                    for cert in template_data.get('certifications', []):
                        name = cert.get('name', '')
                        issuer = cert.get('issuer', '')
                        date = cert.get('date', '')
                        
                        f.write(f"\\entry\n")
                        f.write(f"  {{{date}}}\n")
                        f.write(f"  {{{name}}}\n")
                        f.write(f"  {{{issuer}}}\n")
                        f.write(f"  {{}}\n")
                        f.write(f"  {{}}\n")
                    f.write("\\end{entrylist}\n\n")
                
                # Add languages
                if template_data.get('languages'):
                    f.write("\n% Languages section\n")
                    f.write("\\section{Languages}\n\n")
                    
                    for lang in template_data.get('languages', []):
                        name = lang.get('name', '')
                        level = lang.get('level', '')
                        f.write(f"\\language{{{name}}}{{{level}}}\n")
                
                # End document
                f.write("\n\\end{document}\n")
            
            # For cv_15.tex template
            elif os.path.basename(main_tex_file) == "cv_15.tex":
                f.write("\\documentclass[a4paper]{article}\n")
                f.write("\\input{files/cv_15}\n\n")
                
                # Create document with personalized content
                f.write("\\begin{document}\n\n")
                
                # Add personal info section
                f.write("% Personal information\n")
                f.write(f"\\name{{{template_data.get('name', 'Your Name')}}}\n")
                f.write(f"\\address{{{template_data.get('address', '')}}}\n")
                f.write(f"\\mailaddress{{{template_data.get('email', '')}}}\n")
                f.write(f"\\phone{{{template_data.get('phone', '')}}}\n")
                
                if template_data.get('website'):
                    f.write(f"\\website{{{template_data.get('website', '')}}}\n")
                if template_data.get('github'):
                    f.write(f"\\github{{{template_data.get('github', '')}}}\n")
                if template_data.get('linkedin'):
                    f.write(f"\\linkedin{{{template_data.get('linkedin', '')}}}\n")
                
                f.write("\\photo{photo}\n")
                
                # Add profile summary
                if template_data.get('profile_summary'):
                    f.write("\n% Profile summary\n")
                    f.write(f"\\objective{{{template_data.get('profile_summary', '')}}}\n")
                
                # Add experience section
                if template_data.get('experience'):
                    f.write("\n% Experience section\n")
                    f.write("\\cvsection{Professional Experience}\n\n")
                    
                    for job in template_data.get('experience', []):
                        job_title = job.get('title', '')
                        company = job.get('company', '')
                        location = job.get('location', '')
                        start_date = job.get('start_date', '')
                        end_date = job.get('end_date', 'Present')
                        description = job.get('description', '')
                        
                        date_range = f"{start_date} -- {end_date}"
                        
                        f.write(f"\\cventry{{{date_range}}}{{{job_title}}}{{{company}}}{{{location}}}{{{description}}}\n\n")
                
                # Add education section
                if template_data.get('education'):
                    f.write("\n% Education section\n")
                    f.write("\\cvsection{Education}\n\n")
                    
                    for edu in template_data.get('education', []):
                        degree = edu.get('degree', '')
                        institution = edu.get('institution', '')
                        location = edu.get('location', '')
                        start_date = edu.get('start_date', '')
                        end_date = edu.get('end_date', 'Present')
                        description = edu.get('description', '')
                        
                        date_range = f"{start_date} -- {end_date}"
                        
                        f.write(f"\\cventry{{{date_range}}}{{{degree}}}{{{institution}}}{{{location}}}{{{description}}}\n\n")
                
                # Add skills section
                if template_data.get('skills'):
                    f.write("\n% Skills section\n")
                    f.write("\\cvsection{Skills}\n\n")
                    
                    skills_by_category = {}
                    for skill in template_data.get('skills', []):
                        category = skill.get('category', 'Other')
                        name = skill.get('name', '')
                        
                        if category not in skills_by_category:
                            skills_by_category[category] = []
                        
                        skills_by_category[category].append(name)
                    
                    for category, skills in skills_by_category.items():
                        f.write(f"\\cvsubsection{{{category}}}\n")
                        f.write("\\begin{itemize}\n")
                        
                        for skill_name in skills:
                            f.write(f"  \\item {skill_name}\n")
                        
                        f.write("\\end{itemize}\n\n")
                
                # Add certifications
                if template_data.get('certifications'):
                    f.write("\n% Certifications section\n")
                    f.write("\\cvsection{Certifications}\n\n")
                    
                    for cert in template_data.get('certifications', []):
                        name = cert.get('name', '')
                        issuer = cert.get('issuer', '')
                        date = cert.get('date', '')
                        
                        f.write(f"\\cventry{{{date}}}{{{name}}}{{{issuer}}}{{}}{{}}\n\n")
                
                # Add languages
                if template_data.get('languages'):
                    f.write("\n% Languages section\n")
                    f.write("\\cvsection{Languages}\n\n")
                    f.write("\\begin{itemize}\n")
                    
                    for lang in template_data.get('languages', []):
                        name = lang.get('name', '')
                        level = lang.get('level', '')
                        f.write(f"  \\item {name} ({level})\n")
                    
                    f.write("\\end{itemize}\n\n")
                
                # End document
                f.write("\n\\end{document}\n")
            
            # For other templates, just use the full template content
            else:
                # Copy the template but replace relevant fields
                content = template_content
                
                # Replace personal information
                name_replacements = [
                    (r'\\name{[^}]*}', f"\\name{{{template_data.get('name', 'Your Name')}}}"),
                    (r'\\author{[^}]*}', f"\\author{{{template_data.get('name', 'Your Name')}}}"),
                    (r'\\firstname{[^}]*}', f"\\firstname{{{template_data.get('first_name', 'Your')}}}"),
                    (r'\\lastname{[^}]*}', f"\\lastname{{{template_data.get('last_name', 'Name')}}}"),
                    (r'\\address{[^}]*}', f"\\address{{{template_data.get('address', '')}}}"),
                    (r'\\email{[^}]*}', f"\\email{{{template_data.get('email', '')}}}"),
                    (r'\\phone{[^}]*}', f"\\phone{{{template_data.get('phone', '')}}}"),
                ]
                
                for pattern, replacement in name_replacements:
                    content = re.sub(pattern, replacement, content)
                
                # Write the modified content
                f.write(content)
        
        return os.path.join(output_dir, 'cv.tex')