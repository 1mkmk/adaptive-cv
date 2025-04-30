"""
LaTeX compilation utilities for CV generation.
"""

import os
import subprocess
import tempfile
import logging
import time
import traceback
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)

class LaTeXCompiler:
    """Handles the compilation of LaTeX documents to PDF"""
    
    @staticmethod
    def check_latex_installation():
        """Check if LaTeX is installed and return version info"""
        try:
            version_check = subprocess.run(["pdflatex", "--version"], 
                                         capture_output=True, text=True, timeout=5)
            if version_check.returncode == 0:
                version = version_check.stdout.splitlines()[0].strip()
                # Also check for common LaTeX packages that might be needed
                LaTeXCompiler.check_latex_packages()
                return True, version
            return False, None
        except Exception as e:
            logger.error(f"Error checking LaTeX installation: {e}")
            return False, None
            
    @staticmethod
    def check_latex_packages():
        """Check if commonly needed LaTeX packages are installed"""
        try:
            # Use kpsewhich to check for some common .sty files
            common_packages = ["hyperref.sty", "fontawesome.sty", "xcolor.sty", "geometry.sty"]
            missing_packages = []
            
            for package in common_packages:
                try:
                    result = subprocess.run(["kpsewhich", package], 
                                           capture_output=True, text=True, timeout=2)
                    if result.returncode != 0 or not result.stdout.strip():
                        missing_packages.append(package.replace('.sty', ''))
                except Exception:
                    missing_packages.append(package.replace('.sty', ''))
            
            if missing_packages:
                logger.warning(f"Some LaTeX packages may be missing: {', '.join(missing_packages)}")
                logger.warning("This might cause compilation errors for certain templates.")
            else:
                logger.info("All common LaTeX packages appear to be available.")
        except Exception as e:
            logger.error(f"Error checking LaTeX packages: {e}")
    
    @staticmethod
    def compile_latex(template_dir, latex_file, output_pdf=None, max_attempts=3):
        """
        Compile a LaTeX file to PDF
        
        Args:
            template_dir: Directory containing all template files
            latex_file: Path to the main LaTeX file to compile
            output_pdf: Optional path to save the compiled PDF
            max_attempts: Maximum number of compilation attempts
            
        Returns:
            tuple: (success flag, pdf_path or error message)
        """
        if not os.path.exists(latex_file):
            return False, f"LaTeX file not found: {latex_file}"
            
        # Get the base name of the LaTeX file for output naming
        latex_basename = os.path.basename(latex_file)
        latex_filename = os.path.splitext(latex_basename)[0]
        
        # Get the directory of the latex file
        latex_dir = os.path.dirname(latex_file)
        
        # Expected PDF output name
        pdf_output = os.path.join(latex_dir, f"{latex_filename}.pdf")
        
        # Change to the template directory to ensure all includes work
        original_dir = os.getcwd()
        os.chdir(template_dir)
        
        success = False
        error_output = ""
        
        try:
            # Run pdflatex multiple times to resolve references
            for attempt in range(max_attempts):
                logger.info(f"LaTeX compilation attempt {attempt+1} for {latex_basename}")
                
                # Run pdflatex with various options to handle errors and output
                process = subprocess.run(
                    [
                        "pdflatex",
                        "-interaction=nonstopmode",  # Don't stop on error
                        "-halt-on-error",            # But do exit with error code
                        "-file-line-error",          # Show file and line for errors
                        latex_file
                    ],
                    cwd=template_dir,
                    capture_output=True,
                    text=True,
                    timeout=60  # Timeout to prevent hanging
                )
                
                # Check if compilation succeeded
                if process.returncode == 0:
                    if os.path.exists(pdf_output):
                        success = True
                        break
                else:
                    # Log the error details
                    error_output = process.stderr + process.stdout
                    logger.error(f"LaTeX compilation failed on attempt {attempt+1}")
                    
                    # Print some context around errors
                    error_lines = [line for line in error_output.splitlines() 
                                  if "error" in line.lower() or "fatal" in line.lower()]
                    for line in error_lines[:5]:  # Limit to first 5 error lines
                        logger.error(f"LaTeX error: {line.strip()}")
                
                # Short pause before next attempt
                time.sleep(1)
            
            # If successful and an output path was provided, copy the PDF there
            if success and output_pdf:
                shutil.copy2(pdf_output, output_pdf)
                return True, output_pdf
            elif success:
                return True, pdf_output
            else:
                # If we get here, compilation failed after all attempts
                return False, error_output
                
        except subprocess.TimeoutExpired:
            return False, "LaTeX compilation timed out"
        except Exception as e:
            logger.error(f"Error during LaTeX compilation: {str(e)}")
            logger.error(traceback.format_exc())
            return False, str(e)
        finally:
            # Always change back to the original directory
            os.chdir(original_dir)