#!/usr/bin/env python3

import os
import sys
import zipfile
import tempfile
import shutil
import subprocess
import logging
from pathlib import Path
import fitz  # PyMuPDF

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Define paths
BASE_DIR = Path(os.path.dirname(os.path.abspath(__file__))).parent
ASSETS_DIR = BASE_DIR / "assets"
TEMPLATE_DIR = ASSETS_DIR / "templates"
TEMPLATE_EXTRACTED_DIR = TEMPLATE_DIR / "templates_extracted"
TEMP_DIR = Path(tempfile.mkdtemp(prefix="cv_templates_"))

def ensure_dirs():
    """Ensure all required directories exist"""
    dirs = [TEMPLATE_DIR, TEMPLATE_EXTRACTED_DIR]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured directories exist: {', '.join(str(d) for d in dirs)}")

def extract_template_zip(zip_path, output_dir):
    """Extract a template ZIP file to the specified directory"""
    template_id = os.path.basename(zip_path).replace('.zip', '').lower().replace(' ', '_')
    template_dir = output_dir / template_id
    
    if not template_dir.exists():
        template_dir.mkdir(parents=True)
    
    logger.info(f"Extracting {zip_path} to {template_dir}")
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(template_dir)
        return template_dir
    except Exception as e:
        logger.error(f"Failed to extract {zip_path}: {e}")
        return None

def find_main_tex_file(directory):
    """Find the main .tex file in a template directory"""
    tex_files = list(directory.glob('**/*.tex'))
    
    if not tex_files:
        return None
    
    # Try to find the main file by common naming patterns
    priority_files = []
    for tex_file in tex_files:
        filename = tex_file.name.lower()
        for keyword in ['main', 'cv', 'resume', 'template']:
            if keyword in filename:
                priority_files.append(tex_file)
                break
    
    # Return the first priority file or the first .tex file if no priorities found
    return priority_files[0] if priority_files else tex_files[0]

def compile_tex_to_pdf(tex_file):
    """Compile a .tex file to PDF using pdflatex"""
    tex_dir = tex_file.parent
    tex_filename = tex_file.name
    
    logger.info(f"Compiling {tex_file} with pdflatex")
    
    try:
        process = subprocess.run(
            ['pdflatex', '-interaction=nonstopmode', '-halt-on-error', tex_filename],
            cwd=tex_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            timeout=30  # 30 second timeout to prevent hanging
        )
        
        if process.returncode != 0:
            logger.error(f"pdflatex failed: {process.stderr}")
            return None
        
        # Run a second time for references
        subprocess.run(
            ['pdflatex', '-interaction=nonstopmode', tex_filename],
            cwd=tex_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30
        )
        
        pdf_file = tex_dir / f"{tex_file.stem}.pdf"
        if pdf_file.exists():
            return pdf_file
        else:
            logger.error(f"PDF file not found: {pdf_file}")
            return None
    except subprocess.TimeoutExpired:
        logger.error(f"pdflatex timed out after 30 seconds on {tex_file}")
        return None
    except Exception as e:
        logger.error(f"Error compiling {tex_file}: {e}")
        return None

def generate_preview(pdf_file, output_path):
    """Generate a preview image from the first page of a PDF"""
    logger.info(f"Generating preview for {pdf_file}")
    
    try:
        # Open the PDF file
        doc = fitz.open(pdf_file)
        
        # Get the first page
        page = doc.load_page(0)
        
        # Render page to an image with higher resolution
        pix = page.get_pixmap(matrix=fitz.Matrix(3, 3))
        
        # Save the image
        pix.save(output_path)
        
        logger.info(f"Created preview: {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"Error generating preview for {pdf_file}: {e}")
        return None

def process_template(zip_path):
    """Process a template ZIP file: extract, find main tex, compile, generate preview"""
    template_id = os.path.basename(zip_path).replace('.zip', '').lower().replace(' ', '_')
    logger.info(f"Processing template: {template_id}")
    
    # Create a temporary directory for this template
    temp_template_dir = TEMP_DIR / template_id
    os.makedirs(temp_template_dir, exist_ok=True)
    
    try:
        # Extract the template
        extracted_dir = extract_template_zip(zip_path, temp_template_dir)
        if not extracted_dir:
            return False
        
        # Find the main tex file
        main_tex = find_main_tex_file(extracted_dir)
        if not main_tex:
            logger.error(f"No .tex files found in {extracted_dir}")
            return False
        
        # Compile the tex file to PDF
        pdf_file = compile_tex_to_pdf(main_tex)
        if not pdf_file:
            return False
        
        # Generate preview image
        preview_path = TEMPLATE_EXTRACTED_DIR / template_id / "preview.jpg"
        os.makedirs(os.path.dirname(preview_path), exist_ok=True)
        
        if generate_preview(pdf_file, preview_path):
            # Copy needed template files to templates_extracted directory
            target_dir = TEMPLATE_EXTRACTED_DIR / template_id
            os.makedirs(target_dir, exist_ok=True)
            
            # Copy the main tex file and any cls files
            for file in extracted_dir.glob('**/*.tex'):
                target_file = target_dir / file.name
                shutil.copy(file, target_file)
                logger.info(f"Copied {file.name} to {target_dir}")
            
            for file in extracted_dir.glob('**/*.cls'):
                target_file = target_dir / file.name
                shutil.copy(file, target_file)
                logger.info(f"Copied {file.name} to {target_dir}")
            
            # Copy additional resource files that might be needed (images, etc.)
            for ext in ['.png', '.jpg', '.jpeg', '.pdf']:
                for file in extracted_dir.glob(f'**/*{ext}'):
                    target_file = target_dir / file.name
                    shutil.copy(file, target_file)
                    logger.info(f"Copied {file.name} to {target_dir}")
            
            return True
        
        return False
    except Exception as e:
        logger.error(f"Error processing template {template_id}: {e}")
        return False
    finally:
        # Clean up the temporary directory for this template
        try:
            shutil.rmtree(temp_template_dir)
        except Exception as e:
            logger.warning(f"Failed to remove temp directory {temp_template_dir}: {e}")

def main():
    """Main function to scan templates and generate previews"""
    ensure_dirs()
    
    try:
        # Find all ZIP files in the templates directory
        zip_files = list(TEMPLATE_DIR.glob('*.zip'))
        
        if not zip_files:
            logger.warning(f"No template ZIP files found in {TEMPLATE_DIR}")
            return
        
        logger.info(f"Found {len(zip_files)} template ZIP files")
        
        # Process each template
        successful = 0
        for zip_path in zip_files:
            if process_template(zip_path):
                successful += 1
        
        logger.info(f"Successfully generated previews for {successful} of {len(zip_files)} templates")
    
    except Exception as e:
        logger.error(f"Error in main execution: {e}")
    finally:
        # Clean up the main temporary directory
        try:
            shutil.rmtree(TEMP_DIR)
            logger.info(f"Removed temporary directory: {TEMP_DIR}")
        except Exception as e:
            logger.warning(f"Failed to remove main temp directory: {e}")

if __name__ == "__main__":
    main()