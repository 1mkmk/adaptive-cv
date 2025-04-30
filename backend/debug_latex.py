#!/usr/bin/env python
"""
LaTeX CV Generator Diagnostic Tool

This script performs diagnostics on the LaTeX environment to help troubleshoot CV generation issues.

Usage:
    python debug_latex.py

This will run a series of tests to check the LaTeX environment, compile a simple test document,
and provide detailed information about potential issues.
"""

import os
import sys
import subprocess
import tempfile
import platform
import shutil
import glob
import json
import re
from pathlib import Path

# Determine the project root based on this script's location
BASE_DIR = Path(__file__).parent.parent

def print_section(title):
    """Print a section header for better output formatting"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)

def run_command(cmd, timeout=30):
    """Run a command and return its output with error status"""
    try:
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            timeout=timeout
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out after {timeout} seconds"
    except Exception as e:
        return False, "", f"Error running command: {str(e)}"

def check_latex_installation():
    """Check if LaTeX is properly installed"""
    print_section("LaTeX Installation Check")
    
    # Check for pdflatex
    success, stdout, stderr = run_command(["pdflatex", "--version"])
    
    if success:
        print("✓ pdflatex is installed:")
        print(f"  {stdout.splitlines()[0]}")
    else:
        print("✗ pdflatex is NOT installed or not in PATH")
        print(f"  Error: {stderr}")
        print("\nInstallation instructions:")
        if platform.system() == "Windows":
            print("  - Install MiKTeX: https://miktex.org/download")
            print("  - Or install TeX Live: https://www.tug.org/texlive/windows.html")
        elif platform.system() == "Darwin":  # macOS
            print("  - Install MacTeX: https://www.tug.org/mactex/")
            print("  - Or use Homebrew: brew install --cask mactex")
        else:  # Linux
            print("  - Install TeX Live: sudo apt-get install texlive-full")
            print("  - Or for minimal installation: sudo apt-get install texlive-base")
        return False
    
    return True

def check_latex_packages():
    """Check for commonly needed LaTeX packages"""
    print_section("LaTeX Package Check")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a test .tex file that imports common packages
        test_file = os.path.join(temp_dir, "package_test.tex")
        with open(test_file, "w") as f:
            f.write("\\documentclass{article}\n")
            f.write("\\usepackage{graphicx}\n")  # For images
            f.write("\\usepackage{hyperref}\n")   # For links
            f.write("\\usepackage{geometry}\n")   # For page layout
            f.write("\\usepackage{xcolor}\n")     # For colors
            f.write("\\usepackage{tikz}\n")       # For graphics
            f.write("\\usepackage{fontenc}\n")    # For font encoding
            f.write("\\usepackage{enumitem}\n")   # For lists
            f.write("\\usepackage{titlesec}\n")   # For section formatting
            f.write("\\usepackage{microtype}\n")  # For typography improvements
            f.write("\\begin{document}\nTest Package Compilation\n\\end{document}\n")
        
        print("Testing compilation with common LaTeX packages...")
        orig_dir = os.getcwd()
        os.chdir(temp_dir)
        
        try:
            # Run pdflatex with the test file
            success, stdout, stderr = run_command(
                ["pdflatex", "-interaction=nonstopmode", "package_test.tex"]
            )
            
            # Check if PDF was generated
            if os.path.exists("package_test.pdf"):
                print("✓ All basic LaTeX packages compiled successfully")
                return True
            else:
                print("✗ LaTeX package test failed")
                
                # Parse the log for package errors
                packages_with_errors = []
                if os.path.exists("package_test.log"):
                    with open("package_test.log", "r", encoding="utf-8", errors="ignore") as log:
                        log_content = log.read()
                        
                        # Look for common package error patterns
                        for line in log_content.splitlines():
                            if "Package" in line and "Error" in line:
                                packages_with_errors.append(line.strip())
                            elif "not found" in line and ".sty" in line:
                                packages_with_errors.append(line.strip())
                
                if packages_with_errors:
                    print("  Package errors found:")
                    for err in packages_with_errors:
                        print(f"  - {err}")
                else:
                    print("  Compilation failed, but specific package errors weren't identified.")
                    print("  Check the full log for more details.")
                
                print("\nSuggestion: Try installing full LaTeX distribution:")
                if platform.system() == "Windows":
                    print("  - Use MiKTeX Package Manager to install missing packages")
                    print("  - Or reinstall with a complete TeX Live installation")
                else:
                    print("  - sudo apt-get install texlive-full (Ubuntu/Debian)")
                    print("  - sudo dnf install texlive-scheme-full (Fedora)")
                    print("  - brew install --cask mactex (macOS with Homebrew)")
                
                return False
                
        finally:
            os.chdir(orig_dir)

def test_template_compilation(template_name=None):
    """Test compilation with an actual CV template"""
    print_section("CV Template Compilation Test")
    
    # Define template directory path
    templates_extracted_dir = BASE_DIR / "assets" / "templates" / "templates_extracted"
    
    # If no specific template provided, use a default or find the first available one
    if not template_name:
        # Try to find available templates
        if templates_extracted_dir.exists():
            templates = [d for d in templates_extracted_dir.iterdir() if d.is_dir()]
            if templates:
                template_name = templates[0].name
                print(f"No template specified, using: {template_name}")
            else:
                print("No templates found in the extracted templates directory.")
                return False
        else:
            print(f"Templates directory not found: {templates_extracted_dir}")
            return False
    
    # Determine the template directory
    template_dir = templates_extracted_dir / template_name
    if not template_dir.exists():
        print(f"Template '{template_name}' not found in {templates_extracted_dir}")
        return False
    
    print(f"Testing compilation with template: {template_name}")
    
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        # Copy template files to temp directory
        for item in os.listdir(template_dir):
            src_path = os.path.join(template_dir, item)
            if os.path.isdir(src_path):
                shutil.copytree(src_path, os.path.join(temp_dir, item), dirs_exist_ok=True)
            else:
                shutil.copy2(src_path, temp_dir)
        
        # Find main .tex file
        tex_files = glob.glob(os.path.join(temp_dir, "*.tex"))
        if not tex_files:
            print(f"No .tex files found in template: {template_name}")
            return False
        
        main_tex = tex_files[0]  # Assume first .tex file is main file
        
        # Create a simple test CV
        test_data = {
            "name": "Test Candidate",
            "email": "test@example.com",
            "phone": "+1 234 567 890",
            "address": "Test City, Test Country",
            "profile_summary": "Experienced professional with skills in Python, LaTeX, and testing.",
            "experience": [
                {
                    "title": "Software Engineer",
                    "company": "Test Company",
                    "location": "Test Location",
                    "start_date": "2020",
                    "end_date": "Present",
                    "description": "Implemented and tested software solutions."
                }
            ],
            "education": [
                {
                    "degree": "Bachelor of Science",
                    "institution": "Test University",
                    "location": "Test Location",
                    "start_date": "2015",
                    "end_date": "2019",
                    "description": "Studied Computer Science and Software Engineering."
                }
            ],
            "skills": [
                {"name": "Python", "level": "Expert", "category": "Programming"},
                {"name": "LaTeX", "level": "Intermediate", "category": "Documentation"},
                {"name": "Testing", "level": "Advanced", "category": "Quality Assurance"}
            ]
        }
        
        # Create a simple cv.tex file
        with open(os.path.join(temp_dir, "cv.tex"), "w", encoding="utf-8") as f:
            f.write("% Test CV file\n")
            f.write("\\documentclass{article}\n")
            
            # Include the template if it's a .cls file
            tex_basename = os.path.basename(main_tex)
            if tex_basename.endswith(".cls"):
                f.write(f"\\usepackage{{{os.path.splitext(tex_basename)[0]}}}\n")
            else:
                f.write(f"\\input{{{os.path.splitext(tex_basename)[0]}}}\n")
            
            f.write("\\begin{document}\n")
            f.write(f"\\name{{{test_data['name']}}}\n")
            f.write(f"\\address{{{test_data['address']}}}\n")
            f.write(f"\\email{{{test_data['email']}}}\n")
            f.write(f"\\phone{{{test_data['phone']}}}\n")
            
            # Add profile summary
            f.write(f"\\section*{{Profile}}\n{test_data['profile_summary']}\n\n")
            
            # Add experience
            f.write("\\section*{Experience}\n")
            for job in test_data["experience"]:
                f.write(f"\\subsection*{{{job['title']} at {job['company']}}}\n")
                f.write(f"{job['start_date']} - {job['end_date']} | {job['location']}\n")
                f.write(f"{job['description']}\n\n")
            
            # Add education
            f.write("\\section*{Education}\n")
            for edu in test_data["education"]:
                f.write(f"\\subsection*{{{edu['degree']} at {edu['institution']}}}\n")
                f.write(f"{edu['start_date']} - {edu['end_date']} | {edu['location']}\n")
                f.write(f"{edu['description']}\n\n")
            
            f.write("\\end{document}\n")
        
        # Try to compile
        orig_dir = os.getcwd()
        os.chdir(temp_dir)
        
        try:
            print("Compiling test CV...")
            success, stdout, stderr = run_command(
                ["pdflatex", "-interaction=nonstopmode", "cv.tex"]
            )
            
            if os.path.exists("cv.pdf"):
                print("✓ Successfully compiled test CV")
                pdf_size = os.path.getsize("cv.pdf")
                print(f"  PDF size: {pdf_size} bytes")
                return True
            else:
                print("✗ Failed to compile test CV")
                
                # Check for error log
                if os.path.exists("cv.log"):
                    # Extract key errors from the log
                    with open("cv.log", "r", encoding="utf-8", errors="ignore") as log:
                        log_content = log.read()
                        error_lines = []
                        
                        # Look for common LaTeX error patterns
                        for line in log_content.splitlines():
                            if any(err in line.lower() for err in ["error", "undefined", "missing", "not found"]):
                                error_lines.append(line.strip())
                        
                        if error_lines:
                            print("\nKey errors from LaTeX compilation:")
                            for i, line in enumerate(error_lines[:10]):  # Show first 10 errors
                                print(f"  {i+1}. {line}")
                            
                            if len(error_lines) > 10:
                                print(f"  ... and {len(error_lines) - 10} more errors")
                
                return False
        finally:
            os.chdir(orig_dir)

def check_system_environment():
    """Check system environment variables and paths"""
    print_section("System Environment Check")
    
    # Check PATH environment variable
    path = os.environ.get('PATH', '')
    path_entries = path.split(os.pathsep)
    
    # Look for LaTeX-related directories in PATH
    latex_paths = []
    for entry in path_entries:
        if any(tex_dir in entry.lower() for tex_dir in ['tex', 'latex', 'miktex']):
            latex_paths.append(entry)
    
    if latex_paths:
        print("LaTeX-related directories found in PATH:")
        for p in latex_paths:
            print(f"  - {p}")
    else:
        print("No LaTeX-related directories found in PATH.")
        print("This might be why LaTeX commands are not found.")
    
    # Check TEXINPUTS environment variable
    texinputs = os.environ.get('TEXINPUTS', '')
    if texinputs:
        print("\nTEXINPUTS environment variable:")
        print(f"  {texinputs}")
    else:
        print("\nTEXINPUTS environment variable not set (this is often normal).")
    
    # Check for temporary directory access
    print("\nChecking temporary directory access:")
    temp_dir = tempfile.gettempdir()
    print(f"  Temporary directory: {temp_dir}")
    
    try:
        test_file = os.path.join(temp_dir, 'latex_test.txt')
        with open(test_file, 'w') as f:
            f.write("Test")
        os.remove(test_file)
        print("  ✓ Can write to temporary directory")
    except Exception as e:
        print(f"  ✗ Cannot write to temporary directory: {str(e)}")
    
    return True

def check_latest_compile_errors():
    """Check most recent compilation errors in the generated directories"""
    print_section("Recent Compilation Errors")
    
    # Path to the generated LaTeX directories
    latex_dir = BASE_DIR / "assets" / "generated" / "latex"
    
    if not latex_dir.exists():
        print(f"Generated LaTeX directory not found: {latex_dir}")
        return False
    
    # Get list of directories sorted by modification time (newest first)
    dirs = [d for d in latex_dir.iterdir() if d.is_dir()]
    if not dirs:
        print("No generated LaTeX directories found.")
        return False
    
    dirs.sort(key=lambda d: d.stat().st_mtime, reverse=True)
    latest_dir = dirs[0]
    
    print(f"Checking the most recent LaTeX directory: {latest_dir.name}")
    
    # Look for log and error files
    log_files = [
        latest_dir / "compile_log.txt",
        latest_dir / "compile_error.txt", 
        latest_dir / "exception_error.txt",
        latest_dir / "cv.log"
    ]
    
    found_logs = False
    for log_path in log_files:
        if log_path.exists():
            print(f"\nContents of {log_path.name}:")
            try:
                with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    
                    # For large logs, just show the relevant parts
                    if len(content) > 1000:
                        # Show first lines
                        print(content[:200] + "\n...\n")
                        
                        # Extract and show error lines
                        error_lines = []
                        for line in content.splitlines():
                            if any(err in line.lower() for err in ["error", "undefined", "missing"]):
                                error_lines.append(line)
                        
                        if error_lines:
                            print("Error messages found in log:")
                            for i, line in enumerate(error_lines[:15]):  # Show first 15 errors
                                print(f"  {i+1}. {line}")
                            
                            if len(error_lines) > 15:
                                print(f"  ... and {len(error_lines) - 15} more errors")
                        
                        # Show last few lines
                        print("\n...\n" + content[-500:])
                    else:
                        print(content)
                    found_logs = True
            except Exception as e:
                print(f"  Error reading log file: {str(e)}")
    
    # Check the content of cv.tex
    cv_tex = latest_dir / "cv.tex"
    if cv_tex.exists():
        print("\nChecking cv.tex file:")
        try:
            with open(cv_tex, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read(1000)  # Get first 1000 chars
                print(f"Content of cv.tex (first 1000 chars):\n{content}...")
                
                # Check for common LaTeX syntax issues
                issues = []
                
                # Check for unmatched braces
                opening_braces = content.count('{')
                closing_braces = content.count('}')
                if opening_braces != closing_braces:
                    issues.append(f"Unbalanced braces: {opening_braces} opening vs {closing_braces} closing")
                
                # Check for common command issues
                if "\\begin{document}" not in content:
                    issues.append("Missing \\begin{document}")
                if "\\" in content and "\\documentclass" not in content:
                    issues.append("LaTeX commands found but no \\documentclass")
                
                if issues:
                    print("\nPotential issues detected in cv.tex:")
                    for issue in issues:
                        print(f"  - {issue}")
                else:
                    print("No obvious syntax issues detected in cv.tex")
        except Exception as e:
            print(f"  Error reading cv.tex file: {str(e)}")
    else:
        print("\nNo cv.tex file found")
    
    # List directory contents
    print("\nDirectory contents:")
    for item in latest_dir.iterdir():
        if item.is_file():
            print(f"  - {item.name} ({item.stat().st_size} bytes)")
        else:
            print(f"  - {item.name}/ (directory)")
    
    return found_logs

def generate_diagnostic_report():
    """Generate a comprehensive diagnostic report"""
    report = {
        "system": {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "path_environment": os.environ.get('PATH', '').split(os.pathsep),
        },
        "tests": {}
    }
    
    # Run tests and add results to report
    report["tests"]["latex_installed"] = check_latex_installation()
    report["tests"]["packages_check"] = check_latex_packages()
    report["tests"]["template_test"] = test_template_compilation()
    report["tests"]["system_env"] = check_system_environment()
    report["tests"]["recent_errors"] = check_latest_compile_errors()
    
    # Save report to file
    report_file = os.path.join(BASE_DIR, "latex_diagnostics.json")
    with open(report_file, "w") as f:
        json.dump(report, f, indent=2)
    
    print_section("Diagnostic Summary")
    print(f"Full diagnostic report saved to: {report_file}")
    
    # Determine overall status
    success_count = sum(1 for test, result in report["tests"].items() if result)
    total_tests = len(report["tests"])
    
    print(f"Tests passed: {success_count}/{total_tests}")
    
    if success_count == total_tests:
        print("\n✅ All tests PASSED - LaTeX environment appears to be working correctly!")
        print("If you're still having issues, check the saved diagnostic report.")
    elif success_count >= total_tests - 1:
        print("\n⚠️ Most tests passed, but there are some minor issues.")
        print("Review the test results above to address the remaining problems.")
    else:
        print("\n❌ Multiple tests FAILED - Your LaTeX environment has significant issues.")
        print("Please fix the problems identified in the test results above.")

if __name__ == "__main__":
    print_section("LaTeX CV Generator Diagnostics")
    generate_diagnostic_report()