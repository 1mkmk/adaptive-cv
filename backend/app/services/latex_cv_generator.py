import os
import shutil
import subprocess
import tempfile
import logging
import re
import time
import uuid
import base64
import traceback
from pathlib import Path
import json
from typing import List, Dict
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

# Directory for extracted templates - Fix the path to include "templates" folder
TEMPLATES_EXTRACTED_DIR = ASSETS_DIR / "templates" / "templates_extracted"
TEMPLATES_ZIPPED_DIR = ASSETS_DIR / "templates" / "templates_zipped"

# Create directories if they don't exist
os.makedirs(TEMPLATE_DIR, exist_ok=True)
os.makedirs(LATEX_OUTPUT_DIR, exist_ok=True)
os.makedirs(PDF_OUTPUT_DIR, exist_ok=True)
os.makedirs(TEMPLATES_EXTRACTED_DIR, exist_ok=True)

def get_available_templates() -> List[Dict[str, str]]:
    """
    Get list of available LaTeX CV templates.
    
    This function discovers all LaTeX CV templates by:
    1. Scanning the templates_extracted directory for pre-extracted templates
    2. Scanning the templates_zipped directory for any ZIP files containing templates
    3. Checking for individual template files in the templates directory
    
    Returns:
        List of dictionaries with template information.
    """
    # Helper function for template ID normalization
    def normalize_template_id(temp_id):
        """Creates a normalized version of template ID for better duplicate detection"""
        # First lowercase and replace separators with underscores
        normalized = temp_id.lower().replace('-', '_').replace(' ', '_')
        
        # Remove variations of 'template', 'cv', and 'resume'
        for term in ['template', 'cv', 'resume', 'cv_template']:
            normalized = normalized.replace(term, '')
        
        # Replace multiple underscores with a single one
        while '__' in normalized:
            normalized = normalized.replace('__', '_')
            
        # Remove leading/trailing underscores
        return normalized.strip('_')
    
    templates = []
    # Create a tracking set to detect duplicates by normalized ID
    seen_normalized_ids = set()
    
    # Scan the template folders directory for already extracted templates
    if os.path.exists(TEMPLATES_EXTRACTED_DIR):
        for folder_name in os.listdir(TEMPLATES_EXTRACTED_DIR):
            folder_path = os.path.join(TEMPLATES_EXTRACTED_DIR, folder_name)
            
            # Check if it's a directory
            if os.path.isdir(folder_path):
                # Look for .cls and .tex files
                has_cls = False
                tex_files = []
                
                for file in os.listdir(folder_path):
                    if file.endswith('.cls'):
                        has_cls = True
                    elif file.endswith('.tex'):
                        tex_files.append(file)
                
                # Only add folders that contain at least a .tex file
                if tex_files:
                    # Create a normalized ID for duplicate checking
                    normalized_id = normalize_template_id(folder_name)
                    
                    # Skip if we've already seen a template with this normalized ID
                    if normalized_id in seen_normalized_ids:
                        logger.info(f"Skipping duplicate extracted template: {folder_name}")
                        continue
                    
                    # Add the normalized ID to our tracking set
                    seen_normalized_ids.add(normalized_id)
                    
                    # Create a template dictionary
                    template = {
                        "id": folder_name,
                        "name": folder_name.replace('_', ' ').title(),
                        "path": folder_path,
                        "has_cls": has_cls,
                        "tex_files": tex_files,
                        "main_tex": tex_files[0] if tex_files else None
                    }
                    
                    # Look for a preview image
                    for img_ext in ['.png', '.jpg', '.jpeg']:
                        preview_file = os.path.join(folder_path, f"preview{img_ext}")
                        if os.path.exists(preview_file):
                            template["preview"] = preview_file
                            break
                    
                    templates.append(template)
    
    # Keep track of template IDs and names to avoid duplicates
    existing_ids = [t["id"].lower() for t in templates]
    existing_names = [t["name"].lower() for t in templates]
    
    # Create normalized versions of existing IDs and names for better duplicate detection
    normalized_existing_ids = [normalize_template_id(t_id) for t_id in existing_ids]
    
    # Also keep track of template paths to avoid duplicates from the same folder
    template_paths = [t.get("path", "").lower() for t in templates]
    
    # Scan TEMPLATE_ZIPS_DIR for zip files
    if os.path.exists(TEMPLATES_ZIPPED_DIR):
        # Scan for all ZIP files in the templates_zipped directory
        for filename in os.listdir(TEMPLATES_ZIPPED_DIR):
            if filename.endswith('.zip'):
                zip_path = os.path.join(TEMPLATES_ZIPPED_DIR, filename)
                
                # Generate a template ID from the ZIP file name
                template_id = filename.lower().replace('.zip', '')\
                    .replace(' ', '_')\
                    .replace('-', '_')\
                    .replace('template', '')\
                    .replace('cv', '')\
                    .strip('_')
                
                # Create a nice template name from the filename
                template_name = filename.replace('.zip', '')\
                    .replace('_', ' ')\
                    .replace('-', ' ')\
                    .replace('Template', '')\
                    .replace('template', '')\
                    .strip()
                
                # Create normalized versions for duplicate checking
                normalized_id = normalize_template_id(template_id)
                
                # Skip if we've already seen a template with this normalized ID
                if normalized_id in seen_normalized_ids:
                    logger.info(f"Skipping duplicate template from ZIP: {template_name} ({template_id})")
                    continue
                
                # Also check existing IDs and names as a backup
                if any([
                    template_id in existing_ids,
                    template_name.lower() in existing_names,
                    normalized_id in normalized_existing_ids
                ]):
                    logger.info(f"Skipping duplicate template (by name/ID): {template_name} ({template_id})")
                    continue
                
                # Add the normalized ID to our tracking set
                seen_normalized_ids.add(normalized_id)
                
                # Create a template entry for this ZIP file
                template = {
                    "id": template_id,
                    "name": template_name,
                    "path": str(TEMPLATE_DIR),
                    "has_cls": True,  # Assume most templates have cls files
                    "zip_file": filename,
                    "main_tex": "main.tex"  # Default, will be detected during extraction
                }
                
                # Look for a preview image with matching name
                for img_ext in ['.png', '.jpg', '.jpeg']:
                    preview_patterns = [
                        # Try different naming patterns for preview images
                        filename.replace('.zip', img_ext),
                        filename.replace('.zip', f'_preview{img_ext}'),
                        template_id + img_ext,
                        template_id + f'_preview{img_ext}',
                        'preview_' + template_id + img_ext
                    ]
                    
                    for preview_name in preview_patterns:
                        preview_file = os.path.join(TEMPLATES_EXTRACTED_DIR, preview_name)
                        if os.path.exists(preview_file):
                            template["preview"] = preview_file
                            break
                    
                    if "preview" in template:
                        break
                
                templates.append(template)
                existing_ids.append(template_id)
                existing_names.append(template_name.lower())
                normalized_existing_ids.append(normalized_id)
    
    # If no templates found at all, check for individual template files
    if not templates:
        # Check for the default template files
        resume_cls = os.path.join(TEMPLATE_DIR, 'resume.cls')
        resume_tex = os.path.join(TEMPLATE_DIR, 'resume_faangpath.tex')
        
        if os.path.exists(resume_cls) and os.path.exists(resume_tex):
            templates.append({
                "id": "default",
                "name": "Default FAANGPath Template",
                "path": str(TEMPLATES_EXTRACTED_DIR),
                "has_cls": True,
                "tex_files": ["resume_faangpath.tex"],
                "main_tex": "resume_faangpath.tex"
            })
        else:
            # Add a placeholder if absolutely no templates found
            templates.append({
                "id": "default",
                "name": "Default Template",
                "path": str(TEMPLATES_EXTRACTED_DIR),
                "has_cls": False,
                "tex_files": [],
                "main_tex": None,
                "missing": True
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
        
        # Check for LaTeX installation at initialization
        self.latex_installed, self.latex_version = self._check_latex_installation()
        if self.latex_installed:
            logger.info(f"Using local LaTeX compilation: {self.latex_version}")
        else:
            logger.warning("LaTeX installation not found. PDF generation may fail.")
        
    def _check_latex_installation(self):
        """Check if LaTeX is installed and return version info"""
        try:
            version_check = subprocess.run(["pdflatex", "--version"], 
                                          capture_output=True, text=True, timeout=5)
            if version_check.returncode == 0:
                version = version_check.stdout.splitlines()[0].strip()
                
                # Also check for common LaTeX packages that might be needed
                self._check_latex_packages()
                
                return True, version
            return False, None
        except Exception as e:
            logger.error(f"Error checking LaTeX installation: {e}")
            return False, None
            
    def _check_latex_packages(self):
        """Check if commonly needed LaTeX packages are installed"""
        try:
            # Create a temporary directory for the test
            with tempfile.TemporaryDirectory() as temp_dir:
                # Create a test .tex file that imports common packages
                test_file = os.path.join(temp_dir, "package_test.tex")
                with open(test_file, "w") as f:
                    f.write("\\documentclass{article}\n")
                    f.write("\\usepackage{graphicx}\n")
                    f.write("\\usepackage{hyperref}\n")
                    f.write("\\usepackage{geometry}\n")
                    f.write("\\usepackage{xcolor}\n")
                    f.write("\\usepackage{fontenc}\n")
                    f.write("\\usepackage{enumitem}\n")
                    f.write("\\usepackage{microtype}\n")
                    f.write("\\begin{document}\nTest\n\\end{document}\n")
                
                # Save current directory and change to temp_dir
                orig_dir = os.getcwd()
                os.chdir(temp_dir)
                
                try:
                    # Run pdflatex with the test file
                    result = subprocess.run(
                        ["pdflatex", "-interaction=nonstopmode", "package_test.tex"],
                        capture_output=True, text=True, timeout=10
                    )
                    
                    # Check if PDF was generated
                    if os.path.exists("package_test.pdf"):
                        logger.info("All basic LaTeX packages are installed correctly")
                        return True
                    else:
                        # Extract missing package information
                        missing_packages = []
                        for line in result.stdout.splitlines():
                            if "not found" in line and "package" in line.lower():
                                parts = line.split(":")
                                if len(parts) > 1:
                                    missing_packages.append(parts[-1].strip())
                        
                        if missing_packages:
                            logger.warning(f"Some LaTeX packages may be missing: {', '.join(missing_packages)}")
                        else:
                            logger.warning("LaTeX package test failed but couldn't identify specific missing packages")
                        return False
                finally:
                    # Change back to original directory
                    os.chdir(orig_dir)
        except Exception as e:
            logger.error(f"Error checking LaTeX packages: {e}")
            return False
        
    def compile_latex_locally(self, template_dir):
        """Compile LaTeX document locally"""
        try:
            # Change to template directory
            orig_dir = os.getcwd()
            os.chdir(template_dir)
            
            # Run pdflatex command
            logger.info(f"Compiling LaTeX document locally in {template_dir}")
            
            # Save logs to file for debugging
            log_file = os.path.join(template_dir, "compile_log.txt")
            error_log_file = os.path.join(template_dir, "compile_error.txt")
            
            # Check if pdflatex is available
            try:
                version_check = subprocess.run(["pdflatex", "--version"], capture_output=True, text=True)
                if version_check.returncode != 0:
                    logger.error("pdflatex command not found. Check LaTeX installation.")
                    with open(error_log_file, "w") as f:
                        f.write("pdflatex command not found. Check LaTeX installation.")
                    return False
                
                latex_version = version_check.stdout.splitlines()[0].strip()
                logger.info(f"Using LaTeX: {latex_version}")
                print(f"Using LaTeX: {latex_version}")
            except Exception as e:
                error_msg = f"Error checking LaTeX installation: {e}"
                logger.error(error_msg)
                print(error_msg)
                with open(error_log_file, "w") as f:
                    f.write(error_msg)
                return False
                
            # Run pdflatex command with more detailed output
            pdflatex_cmd = ["pdflatex", "-interaction=nonstopmode", "-file-line-error", "cv.tex"]
            
            # First run
            print(f"Running LaTeX compilation with command: {' '.join(pdflatex_cmd)}")
            result = subprocess.run(pdflatex_cmd, capture_output=True, text=True)
            
            # Save compilation log for debugging
            with open(log_file, "w", encoding="utf-8") as f:
                f.write(result.stdout)
            if result.stderr:
                with open(error_log_file, "w", encoding="utf-8") as f:
                    f.write(result.stderr)
            
            # Run twice for references if first run was successful
            if os.path.exists("cv.pdf"):
                result2 = subprocess.run(pdflatex_cmd, capture_output=True, text=True)
                # Append to log files
                with open(log_file, "a", encoding="utf-8") as f:
                    f.write("\n\n--- SECOND RUN ---\n\n")
                    f.write(result2.stdout)
                if result2.stderr:
                    with open(error_log_file, "a", encoding="utf-8") as f:
                        f.write("\n\n--- SECOND RUN ---\n\n")
                        f.write(result2.stderr)
            
            # Check if PDF was generated successfully
            if result.returncode != 0 or not os.path.exists("cv.pdf"):
                # Extract the most relevant error messages from pdflatex output
                error_lines = []
                error_context = []
                line_number = None
                current_file = None
                
                # Improved error detection from LaTeX output
                for line in result.stdout.splitlines():
                    # Track current file being processed
                    if line.startswith("(") and line.endswith(")") and ".tex" in line:
                        current_file = line.strip("()")
                    
                    # Track line numbers for errors
                    if ":" in line and ".tex" in line and "line" in line:
                        file_match = re.search(r'([^()\s]+\.tex):(\d+):', line)
                        if file_match:
                            current_file = file_match.group(1)
                            line_number = file_match.group(2)
                            error_context.append(f"Error in {current_file} at line {line_number}")
                    
                    # Collect actual errors by looking for common LaTeX error patterns
                    if any(err_type in line.lower() for err_type in [
                        "error:", "fatal error", "emergency stop", "undefined control sequence",
                        "missing", "too many", "file not found", "unknown", "illegal", "missing"
                    ]):
                        error_lines.append(line)
                        
                        # Include additional context for undefined commands
                        if "undefined control sequence" in line.lower():
                            cmd_match = re.search(r'\\[a-zA-Z]+', line)
                            if cmd_match:
                                error_context.append(f"Undefined command: {cmd_match.group(0)}")
                
                # Format detailed error information with context for console output
                if error_lines:
                    detailed_error = "\n".join(error_lines)
                    context = "\n".join(error_context) if error_context else "No additional context available"
                    error_msg = f"LaTeX compilation errors:\n{detailed_error}\n\nContext:\n{context}"
                    
                    logger.error(error_msg)
                    print(f"\n{'-'*50}\nLATEX COMPILATION FAILED\n{'-'*50}")
                    print(error_msg)
                    print(f"{'-'*50}")
                else:
                    # If no specific errors found, log a section of the output
                    last_output = result.stdout[-500:] if len(result.stdout) > 500 else result.stdout
                    error_msg = f"LaTeX compilation failed with output:\n{last_output}"
                    logger.error(error_msg)
                    print(f"\n{'-'*50}\nLATEX COMPILATION FAILED - NO SPECIFIC ERRORS FOUND\n{'-'*50}")
                    print(error_msg)
                    print(f"{'-'*50}")
                
                # Check content of cv.tex for debugging purposes
                try:
                    with open("cv.tex", "r", encoding="utf-8") as f:
                        content_sample = f.read(1000)  # Get first 1000 chars
                    print(f"Content of cv.tex (first 1000 chars):\n{content_sample}...")
                except Exception as e:
                    print(f"Error reading cv.tex: {e}")
                
                # Try fallback if available
                if os.path.exists("fallback.tex"):
                    logger.info("Attempting to compile fallback.tex")
                    print("Attempting to compile fallback template instead...")
                    fallback_cmd = ["pdflatex", "-interaction=nonstopmode", "fallback.tex"]
                    fallback_result = subprocess.run(fallback_cmd, capture_output=True, text=True)
                    
                    with open(log_file, "a", encoding="utf-8") as f:
                        f.write("\n\n--- FALLBACK TEMPLATE ---\n\n")
                        f.write(fallback_result.stdout)
                    
                    if fallback_result.returncode == 0 and os.path.exists("fallback.pdf"):
                        # Rename fallback.pdf to cv.pdf
                        os.rename("fallback.pdf", "cv.pdf")
                        logger.info("Successfully compiled fallback template")
                        print("Successfully compiled fallback template")
                        return True
                    else:
                        fallback_error = "Fallback template compilation also failed"
                        logger.error(fallback_error)
                        print(fallback_error)
                
                # List all files in the directory for debugging
                files_in_dir = os.listdir(".")
                print(f"Files in compilation directory: {files_in_dir}")
                
                return False
            
            logger.info("LaTeX compilation completed successfully")
            print("LaTeX compilation completed successfully")
            return True
        except Exception as e:
            error_msg = f"Error compiling LaTeX locally: {str(e)}"
            logger.error(error_msg)
            print(f"\n{'-'*50}\nEXCEPTION DURING LATEX COMPILATION\n{'-'*50}")
            print(error_msg)
            print(f"{'-'*50}")
            
            # Create error log file
            try:
                with open(os.path.join(template_dir, "exception_error.txt"), "w") as f:
                    f.write(f"Exception during LaTeX compilation: {str(e)}\n\n")
                    f.write(f"Exception traceback:\n{traceback.format_exc()}")
            except:
                pass
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
            
            # Look in the templates_extracted directory first
            template_dir = os.path.join(TEMPLATES_EXTRACTED_DIR, template_name)
            
            # If not found in templates_extracted, try the main template directory
            if not os.path.exists(template_dir):
                template_dir = os.path.join(self.template_path, template_name)
            
            # If still not found, raise an error
            if not os.path.exists(template_dir):
                # Log all available templates for debugging
                available_templates = []
                if os.path.exists(TEMPLATES_EXTRACTED_DIR):
                    available_templates = [d for d in os.listdir(TEMPLATES_EXTRACTED_DIR) 
                                          if os.path.isdir(os.path.join(TEMPLATES_EXTRACTED_DIR, d))]
                
                logger.error(f"Template '{template_name}' not found. Available templates: {available_templates}")
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
                
                # Replace personal information using raw strings for regex patterns
                # This ensures backslashes in LaTeX commands are handled properly
                name_replacements = [
                    (r"\\name\{[^}]*\}", fr"\\name{{{template_data.get('name', 'Your Name')}}}"),
                    (r"\\author\{[^}]*\}", fr"\\author{{{template_data.get('name', 'Your Name')}}}"),
                    (r"\\firstname\{[^}]*\}", fr"\\firstname{{{template_data.get('first_name', 'Your')}}}"),
                    (r"\\lastname\{[^}]*\}", fr"\\lastname{{{template_data.get('last_name', 'Name')}}}"),
                    (r"\\address\{[^}]*\}", fr"\\address{{{template_data.get('address', '')}}}"),
                    (r"\\email\{[^}]*\}", fr"\\email{{{template_data.get('email', '')}}}"),
                    (r"\\phone\{[^}]*\}", fr"\\phone{{{template_data.get('phone', '')}}}"),
                ]
                
                # Simple text replacement approach instead of regex when possible
                for latex_command, field_value in [
                    ("\\name{", template_data.get('name', 'Your Name')),
                    ("\\author{", template_data.get('name', 'Your Name')),
                    ("\\firstname{", template_data.get('first_name', 'Your')),
                    ("\\lastname{", template_data.get('last_name', 'Name')),
                    ("\\address{", template_data.get('address', '')),
                    ("\\email{", template_data.get('email', '')),
                    ("\\phone{", template_data.get('phone', '')),
                ]:
                    try:
                        # Find the command in the content
                        cmd_pos = content.find(latex_command)
                        if cmd_pos >= 0:
                            # Find the closing brace
                            start_pos = cmd_pos + len(latex_command)
                            end_pos = content.find("}", start_pos)
                            if end_pos > start_pos:
                                # Replace only what's inside the braces
                                new_content = content[:start_pos] + field_value + content[end_pos:]
                                content = new_content
                    except Exception as e:
                        logger.warning(f"Error replacing '{latex_command}': {e}")
                
                # Only try regex approach if text replacement failed
                if "\\name{" in content or "\\author{" in content:
                    for pattern, replacement in name_replacements:
                        try:
                            # Using explicit raw strings for regex
                            content = re.sub(pattern, replacement, content, flags=re.DOTALL)
                        except Exception as e:
                            logger.warning(f"Error with regex '{pattern}': {e}")
                
                # Write the modified content
                f.write(content)
        
        return os.path.join(output_dir, 'cv.tex')
    
    def generate_with_template(self, template_name, job_description, user_id=None, format="pdf"):
        """
        Generate a CV using a template and job description
        
        Args:
            template_name: Name of the template to use
            job_description: Job description to use for CV generation
            user_id: Optional user ID
            format: Output format ("pdf" or "latex")
            
        Returns:
            Dictionary with generated CV information
        """
        # Import required modules at the function level to avoid scope issues
        import json
        # Note: re module is already imported at the module level
        
        try:
            logger.info(f"Generating CV with template {template_name} from job description")
            
            # Create a unique output ID
            output_id = str(uuid.uuid4())
            
            # Extract job title and company from description if possible
            job_title = "Position"
            company_name = "Company"
            
            # Try to extract job title from the first line of job description
            if job_description:
                lines = job_description.strip().split('\n')
                if lines:
                    # First line might contain job title
                    first_line = lines[0].strip()
                    if len(first_line) < 100:  # Reasonable job title length
                        job_title = first_line
                    
                    # Try to find company name in first few lines
                    for i in range(min(5, len(lines))):
                        line = lines[i].lower()
                        if "company:" in line or "at" in line or "for" in line:
                            company_match = re.search(r'(?:company:|at|for)\s+([A-Za-z0-9\s&]+)', line, re.IGNORECASE)
                            if company_match:
                                company_name = company_match.group(1).strip()
                                break
            
            # Process job description to extract key information
            # Instead of directly importing extract_job_requirements, we'll create a default requirements dictionary
            job_requirements = {
                "all_requirements": [],
                "required_skills": [],
                "preferred_skills": [],
                "experience_level": "Not specified",
                "experience_years": "Not specified",
                "education": "Not specified",
                "key_responsibilities": [],
                "industry_keywords": [],
                "soft_skills": [],
                "company_values": [],
                "tools_and_technologies": [],
                "certifications": [],
                "exact_phrases": []
            }
            
            # Generate template data
            template_data = {
                'name': 'Candidate Name',
                'email': 'email@example.com',
                'phone': '+1 234 567 890',
                'address': 'City, Country',
                'profile_summary': 'Experienced professional with expertise matching the job requirements.',
                'photo': None,
                'experience': [],
                'education': [],
                'skills': [],
                'languages': [],
                'certifications': []
            }
            
            # If we have a job description, use it to generate better template data
            if job_description:
                try:
                    # Generate a proper CV content based on job description
                    import openai
                    
                    # Define a prompt template for job parsing
                    system_prompt = """You are a CV generator assistant. Extract key information from the job description to create a CV template data structure. Focus on required skills, experience, and qualifications."""
                    
                    user_prompt = f"""
                    Parse this job description and extract key information:
                    
                    {job_description[:2000]}
                    
                    Create a JSON structure with the following:
                    1. A profile summary tailored to this job (max 2 sentences)
                    2. 3-5 key skills required for this job (with proficiency levels)
                    3. 2-3 example job experiences that would be relevant (with dates, titles, companies)
                    4. 1-2 educational qualifications that would be appropriate
                    5. Any certifications mentioned or implied as valuable
                    6. Languages required if mentioned
                    
                    Format the output as valid JSON that fits this structure:
                    {{
                        "profile_summary": "string",
                        "skills": [
                            {{"name": "skill name", "level": "Proficient", "category": "category"}}
                        ],
                        "experience": [
                            {{
                                "title": "job title",
                                "company": "company name",
                                "location": "location",
                                "start_date": "Jan 2020",
                                "end_date": "Present",
                                "description": "key responsibilities and achievements"
                            }}
                        ],
                        "education": [
                            {{
                                "degree": "degree name",
                                "institution": "university name",
                                "location": "location",
                                "start_date": "2015",
                                "end_date": "2019",
                                "description": "relevant coursework or achievements"
                            }}
                        ],
                        "certifications": [
                            {{"name": "certification name", "issuer": "issuing organization", "date": "2021"}}
                        ],
                        "languages": [
                            {{"name": "language name", "level": "fluency level"}}
                        ]
                    }}
                    """
                    
                    # Request for OpenAI key environment variable
                    openai.api_key = os.getenv("OPENAI_API_KEY")
                    
                    if openai.api_key:
                        response = openai.ChatCompletion.create(
                            model="gpt-3.5-turbo",
                            messages=[
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": user_prompt}
                            ],
                            temperature=0.5,
                            max_tokens=1000
                        )
                        
                        generated_content = response.choices[0].message.content.strip()
                        
                        # Extract JSON from the response
                        import json
                        
                        # Find JSON content between curly braces
                        json_match = re.search(r'\{.*\}', generated_content, re.DOTALL)
                        if json_match:
                            json_str = json_match.group(0)
                            try:
                                cv_data = json.loads(json_str)
                                # Merge with template data, keeping default values for missing keys
                                template_data.update(cv_data)
                                logger.info("Successfully generated CV data from job description")
                            except json.JSONDecodeError as e:
                                logger.error(f"Error parsing generated JSON: {e}")
                    else:
                        logger.warning("OpenAI API key not found, using default template data")
                
                except Exception as e:
                    logger.error(f"Error generating CV data from job description: {e}")
            
            try:
                # Generate CV with the template data
                result = self.generate_cv(
                    template_name=template_name,
                    job_title=job_title,
                    company_name=company_name,
                    template_data=template_data,
                    output_id=output_id
                )
                
                # Return based on format
                if format.lower() == "latex":
                    return {
                        "latex_path": result["latex_path"],
                        "output_id": output_id
                    }
                else:
                    # Read PDF content for response
                    pdf_path = result["pdf_path"]
                    
                    with open(pdf_path, "rb") as f:
                        pdf_content = base64.b64encode(f.read()).decode('utf-8')
                    
                    # Try to get preview
                    preview_content = ""
                    preview_path = os.path.join(os.path.dirname(result["latex_path"]), "files", "preview.jpg")
                    if os.path.exists(preview_path):
                        with open(preview_path, "rb") as f:
                            preview_content = base64.b64encode(f.read()).decode('utf-8')
                    
                    return {
                        "pdf": pdf_content,
                        "preview": preview_content,
                        "pdf_path": pdf_path,
                        "latex_path": result["latex_path"],
                        "output_id": output_id
                    }
            except HTTPException as http_e:
                # Handle LaTeX compilation errors from the generate_cv method
                latex_dir = os.path.join(self.output_dir_latex, f"{job_title.lower().replace(' ', '_')}_{time.strftime('%Y%m%d')}_{output_id[:8]}")
                error_details = f"LaTeX compilation failed: {str(http_e)}"
                
                # Check if compilation logs exist
                compile_log_file = os.path.join(latex_dir, "compile_log.txt")
                compile_error_file = os.path.join(latex_dir, "compile_error.txt")
                exception_error_file = os.path.join(latex_dir, "exception_error.txt")
                
                error_info = []
                if os.path.exists(compile_log_file):
                    with open(compile_log_file, "r", encoding="utf-8") as f:
                        log_content = f.read()
                        # Extract critical error lines from the log
                        for line in log_content.split('\n'):
                            if any(err_term in line.lower() for err_term in ["error", "fatal", "undefined", "emergency", "missing"]):
                                error_info.append(line.strip())
                
                if os.path.exists(compile_error_file):
                    with open(compile_error_file, "r", encoding="utf-8") as f:
                        error_info.append("From error log:")
                        error_info.append(f.read().strip())
                
                if os.path.exists(exception_error_file):
                    with open(exception_error_file, "r", encoding="utf-8") as f:
                        error_info.append("From exception log:")
                        error_info.append(f.read().strip())
                
                # Compile detailed error report with useful context
                if error_info:
                    error_details += "\n\nDetailed error information:\n" + "\n".join(error_info[:20])  # Limit to first 20 lines
                
                logger.error(f"Error in generate_with_template: {error_details}")
                return {
                    "error": error_details,
                    "latex_path": latex_dir if os.path.exists(latex_dir) else None
                }
        except Exception as e:
            # Handle other unexpected errors
            error_msg = f"Error in generate_with_template: {str(e)}\n{traceback.format_exc()}"
            logger.error(error_msg)
            print(error_msg)
            return {
                "error": str(e),
                "traceback": traceback.format_exc()
            }