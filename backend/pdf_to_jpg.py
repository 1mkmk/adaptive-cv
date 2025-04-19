#!/usr/bin/env python3

import os
import sys
import fitz  # PyMuPDF
import glob
import zipfile
import tempfile
import shutil
import subprocess
from pathlib import Path

def convert_pdf_to_jpg(pdf_path, jpg_path):
    """Convert a PDF to JPG image"""
    if os.path.exists(pdf_path):
        print(f"Converting {pdf_path} to JPG...")
        try:
            # Open the PDF file
            doc = fitz.open(pdf_path)
            
            # Get the first page
            page = doc.load_page(0)
            
            # Render page to an image with higher resolution
            pix = page.get_pixmap(matrix=fitz.Matrix(3, 3))
            
            # Save the image
            pix.save(jpg_path)
            
            print(f"Created {jpg_path}")
            return True
        except Exception as e:
            print(f"Error converting {pdf_path}: {e}")
            return False
    else:
        print(f"File not found: {pdf_path}")
        return False

def extract_and_process_template(zip_path, base_dir):
    """Extract a template ZIP file and generate a preview image"""
    # Create a unique template ID from the ZIP name, using same logic as in latex_cv_generator.py
    template_id = os.path.basename(zip_path).lower().replace('.zip', '')\
        .replace(' ', '_')\
        .replace('-', '_')\
        .replace('template', '')\
        .replace('cv', '')\
        .strip('_')
    template_name = os.path.basename(zip_path).replace('.zip', '')
    
    # Create extraction paths
    temp_dir = tempfile.mkdtemp(prefix=f"template_{template_id}_")
    templates_extracted_dir = os.path.join(base_dir, "templates_extracted")
    template_output_dir = os.path.join(templates_extracted_dir, template_id)
    
    # Create extraction directory if it doesn't exist
    if not os.path.exists(template_output_dir):
        os.makedirs(template_output_dir, exist_ok=True)
    
    print(f"Processing template: {template_name}")
    print(f"Temporary directory: {temp_dir}")
    
    try:
        # Extract the ZIP file
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        
        # Find the main .tex file
        tex_files = []
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                if file.endswith('.tex'):
                    tex_files.append(os.path.join(root, file))
        
        if not tex_files:
            print(f"No .tex files found in {zip_path}")
            return False
        
        # Prioritize templates with certain keywords in the filename
        main_tex = None
        for tex in tex_files:
            base_name = os.path.basename(tex).lower()
            if any(keyword in base_name for keyword in ['main', 'cv', 'resume', 'template']):
                main_tex = tex
                break
        
        # If no prioritized file found, use the first one
        if not main_tex:
            main_tex = tex_files[0]
        
        print(f"Found main TeX file: {main_tex}")
        
        # Run pdflatex to generate a PDF
        tex_dir = os.path.dirname(main_tex)
        tex_filename = os.path.basename(main_tex)
        
        os.chdir(tex_dir)  # Change to the directory containing the .tex file
        
        try:
            print(f"Compiling {tex_filename} with pdflatex...")
            subprocess.run(
                ['pdflatex', '-interaction=nonstopmode', tex_filename],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=30  # 30 second timeout
            )
            
            # Run a second time for cross-references
            subprocess.run(
                ['pdflatex', '-interaction=nonstopmode', tex_filename],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=30  # 30 second timeout
            )
        except Exception as e:
            print(f"Error compiling {tex_filename}: {e}")
        
        # Check if PDF was generated
        pdf_filename = os.path.splitext(tex_filename)[0] + '.pdf'
        pdf_path = os.path.join(tex_dir, pdf_filename)
        
        if os.path.exists(pdf_path):
            # Generate preview image
            preview_jpg = os.path.join(template_output_dir, "preview.jpg")
            if convert_pdf_to_jpg(pdf_path, preview_jpg):
                # Copy essential template files to the output directory
                for ext in ['.tex', '.cls', '.sty']:
                    for file in glob.glob(os.path.join(temp_dir, f"**/*{ext}"), recursive=True):
                        dest = os.path.join(template_output_dir, os.path.basename(file))
                        shutil.copy2(file, dest)
                        print(f"Copied {file} to {dest}")
                
                print(f"Successfully processed template: {template_id}")
                return True
        else:
            print(f"Failed to generate PDF for {tex_filename}")
            return False
    
    except Exception as e:
        print(f"Error processing template {template_id}: {e}")
        return False
    finally:
        # Clean up temporary directory
        try:
            shutil.rmtree(temp_dir)
            print(f"Cleaned up temporary directory: {temp_dir}")
        except Exception as e:
            print(f"Error cleaning up {temp_dir}: {e}")

def main():
    # Define base path
    base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "templates")
    
    # Create extracted templates directory if it doesn't exist
    templates_extracted_dir = os.path.join(base_dir, "templates_extracted")
    os.makedirs(templates_extracted_dir, exist_ok=True)
    
    # Create zipped templates directory if it doesn't exist
    templates_zipped_dir = os.path.join(base_dir, "templates_zipped")
    os.makedirs(templates_zipped_dir, exist_ok=True)
    
    # Get all ZIP files in the templates_zipped directory
    zip_files = glob.glob(os.path.join(templates_zipped_dir, "*.zip"))
    
    if not zip_files:
        print(f"No ZIP files found in {templates_zipped_dir}")
        return
    
    print(f"Found {len(zip_files)} template ZIP files")
    
    # Process each template
    success_count = 0
    for zip_path in zip_files:
        # Create a template ID from the ZIP file name, using same logic as in latex_cv_generator.py
        template_id = os.path.basename(zip_path).lower().replace('.zip', '')\
            .replace(' ', '_')\
            .replace('-', '_')\
            .replace('template', '')\
            .replace('cv', '')\
            .strip('_')
            
        preview_jpg = os.path.join(templates_extracted_dir, template_id, "preview.jpg")
        
        # Only process templates that don't already have preview images
        if not os.path.exists(preview_jpg):
            print(f"Generating preview for {os.path.basename(zip_path)}...")
            if extract_and_process_template(zip_path, base_dir):
                success_count += 1
        else:
            print(f"Preview already exists for {os.path.basename(zip_path)}, skipping")
            success_count += 1
    
    print(f"Successfully processed {success_count} of {len(zip_files)} templates")

if __name__ == "__main__":
    main()