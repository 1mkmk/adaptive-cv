"""
Script to fix path issues in backend when generating latex files
"""
import os
import sys
from pathlib import Path

# Print current working directory
print(f"Current working directory: {os.getcwd()}")

# Print PATH environment variable
print(f"PATH: {os.environ.get('PATH', 'PATH not found')}")

# Check if pdflatex is in PATH
from shutil import which
pdflatex_path = which("pdflatex")
print(f"pdflatex path: {pdflatex_path}")

# Check assets folder structure
assets_dir = Path(os.path.abspath(os.path.join(os.getcwd(), '../assets')))
print(f"Assets directory: {assets_dir}")
print(f"Assets exists: {os.path.exists(assets_dir)}")

templates_dir = assets_dir / 'templates'
print(f"Templates directory: {templates_dir}")
print(f"Templates exists: {os.path.exists(templates_dir)}")

# Print all files in templates directory
if os.path.exists(templates_dir):
    print("Files in templates directory:")
    for file in os.listdir(templates_dir):
        print(f"  - {file}")

# Check generated folders
generated_dir = assets_dir / 'generated'
print(f"Generated directory: {generated_dir}")
print(f"Generated exists: {os.path.exists(generated_dir)}")

latex_dir = generated_dir / 'latex'
pdf_dir = generated_dir / 'pdf'

print(f"LaTeX directory: {latex_dir}")
print(f"LaTeX exists: {os.path.exists(latex_dir)}")

print(f"PDF directory: {pdf_dir}")
print(f"PDF exists: {os.path.exists(pdf_dir)}")

# Create directories if they don't exist
if not os.path.exists(generated_dir):
    os.makedirs(generated_dir)
    print(f"Created generated directory: {generated_dir}")

if not os.path.exists(latex_dir):
    os.makedirs(latex_dir)
    print(f"Created LaTeX directory: {latex_dir}")

if not os.path.exists(pdf_dir):
    os.makedirs(pdf_dir)
    print(f"Created PDF directory: {pdf_dir}")

print("Path setup completed")