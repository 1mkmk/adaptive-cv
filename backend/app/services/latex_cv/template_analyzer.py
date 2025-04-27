"""
Template analyzer for LaTeX CV generator.

This module is responsible for analyzing LaTeX templates, detecting fields
that need to be replaced, and filling templates with user data.
"""

import os
import re
import shutil
import logging
import glob
import json
import copy
from pathlib import Path
from typing import Dict, Any, List, Set, Tuple, Optional

from .fill_template import escape_latex, prepare_address_format, safe_template_value

logger = logging.getLogger(__name__)

class TemplateAnalyzer:
    """Analyzes LaTeX templates and fills them with user data"""

    # Common LaTeX commands used in CV templates
    CV_COMMANDS = [
        # Personal information
        'name', 'fullname', 'firstname', 'lastname', 'email', 'phone', 'address', 'location',
        'photo', 'profilephoto', 'picture', 'avatar', 'mobile', 'website', 'homepage',
        'github', 'gitlab', 'bitbucket', 'linkedin', 'twitter', 'skype', 'telegram', 
        'profilesummary', 'summary', 'objective', 'about', 'personal', 'bio',
        
        # Education & Work
        'university', 'college', 'school', 'degree', 'major', 'minor', 'gpa',
        'company', 'position', 'jobtitle', 'role', 'employer', 'organization',
        'supervisor', 'mentor', 'period', 'daterange', 'fromdate', 'todate',
        
        # Skills & Languages
        'skill', 'skills', 'technology', 'technologies', 'language', 'languages',
        'proficiency', 'level', 'rating', 'score', 'expertise',
        
        # Other common CV fields
        'project', 'projects', 'publication', 'publications', 'achievement', 'achievements',
        'award', 'awards', 'certification', 'certifications', 'volunteer', 'volunteering',
        'interest', 'interests', 'hobby', 'hobbies', 'reference', 'references'
    ]

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
        main_file, document_structure = self._identify_main_file(tex_files)
        if main_file:
            logger.info(f"Identified main file: {main_file}")
            result["main_files"].append(os.path.relpath(main_file, template_dir))
            result["structure"] = document_structure
        
        # Find other related template files
        for file_path in tex_files:
            if file_path != main_file:
                # Check if the file is included in the main file
                included = self._check_if_included(main_file, file_path)
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
            fields = self._analyze_file_for_fields(file_path)
            if fields:
                result["detected_fields"][rel_path] = fields
        
        # If we have job description and template data, use OpenAI to generate comprehensive debug.json
        if job_description and template_data and template_name:
            try:
                ai_analysis = self._generate_ai_template_analysis(
                    result, job_description, template_data, template_name
                )
                if ai_analysis:
                    # Merge AI analysis with our basic template info
                    result.update(ai_analysis)
            except Exception as e:
                logger.error(f"Error generating AI template analysis: {str(e)}")
        
        return result

    def _identify_main_file(self, tex_files: List[str]) -> Tuple[Optional[str], str]:
        """
        Find the main LaTeX file from a list of .tex files
        
        Args:
            tex_files: List of .tex file paths
            
        Returns:
            Tuple with (main file path, document structure type)
        """
        # Sort by likelihood of being the main file
        candidates = []
        
        for file_path in tex_files:
            # Check if file contains document environment
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
                # Check for document environment
                has_document = '\\begin{document}' in content and '\\end{document}' in content
                
                # Check for common main file names
                file_name = os.path.basename(file_path).lower()
                name_score = 0
                for name in ['main', 'cv', 'resume', 'template', 'index']:
                    if name in file_name:
                        name_score += 1
                
                # Determine document structure
                structure = "unknown"
                if has_document:
                    if "\\documentclass{article}" in content:
                        structure = "article"
                    elif "\\documentclass{resume}" in content:
                        structure = "resume"
                    elif "\\documentclass{cv}" in content:
                        structure = "cv"
                    elif "\\documentclass" in content:
                        # Extract the class name
                        class_match = re.search(r'\\documentclass(?:\[.*?\])?\{(.*?)\}', content)
                        if class_match:
                            structure = class_match.group(1)
                    else:
                        structure = "custom"
                
                candidates.append((file_path, has_document, name_score, structure))
        
        # Filter and sort candidates
        doc_candidates = [c for c in candidates if c[1]]  # Has document environment
        
        if doc_candidates:
            # Sort by name score (higher is better)
            doc_candidates.sort(key=lambda x: x[2], reverse=True)
            return doc_candidates[0][0], doc_candidates[0][3]
        
        # If no document environment found, try to find the most promising file
        if candidates:
            candidates.sort(key=lambda x: x[2], reverse=True)
            return candidates[0][0], "incomplete"
        
        return None, "unknown"

    def _check_if_included(self, main_file: str, file_path: str) -> bool:
        """
        Check if a file is included or imported by the main file
        
        Args:
            main_file: Path to main .tex file
            file_path: Path to file to check
            
        Returns:
            Boolean indicating if the file is included
        """
        if not main_file or not os.path.exists(main_file):
            return False
        
        rel_path = os.path.relpath(file_path, os.path.dirname(main_file))
        file_name = os.path.basename(file_path)
        file_name_no_ext = os.path.splitext(file_name)[0]
        
        # Read main file content
        with open(main_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Check for various include/input patterns
        include_patterns = [
            fr'\\include\s*{{\s*{re.escape(file_name_no_ext)}\s*}}',
            fr'\\input\s*{{\s*{re.escape(file_name_no_ext)}\s*}}',
            fr'\\input\s*{{\s*{re.escape(file_name)}\s*}}',
            fr'\\import\s*{{\s*[^{{}}]*\s*}}\s*{{\s*{re.escape(file_name)}\s*}}',
            fr'\\subimport\s*{{\s*[^{{}}]*\s*}}\s*{{\s*{re.escape(file_name)}\s*}}'
        ]
        
        for pattern in include_patterns:
            if re.search(pattern, content):
                return True
        
        return False

    def _analyze_file_for_fields(self, file_path: str) -> Dict[str, Any]:
        """
        Analyze a LaTeX file to find fields/commands that might need replacement
        
        Args:
            file_path: Path to .tex file
            
        Returns:
            Dictionary with field information
        """
        if not os.path.exists(file_path):
            return {}
        
        fields = {
            "commands": [],
            "environments": [],
            "custom_commands": [],
            "placeholders": []
        }
        
        # Read file content
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Find LaTeX commands from our CV_COMMANDS list
        for cmd in self.CV_COMMANDS:
            pattern = fr'\\{cmd}\s*{{\s*([^}}]*)\s*}}'
            matches = re.findall(pattern, content)
            if matches:
                for match in matches:
                    fields["commands"].append({
                        "command": cmd,
                        "value": match.strip()
                    })
        
        # Find environments related to CV sections
        env_pattern = r'\\begin\{(\w+)[^}]*\}(.*?)\\end\{\1\}'
        for match in re.finditer(env_pattern, content, re.DOTALL):
            env_name = match.group(1)
            env_content = match.group(2)
            
            # Only include relevant CV environments
            cv_env_names = ['education', 'experience', 'skills', 'projects', 'publications', 'awards']
            if any(name in env_name.lower() for name in cv_env_names):
                fields["environments"].append({
                    "name": env_name,
                    "sample_content": env_content[:100] + ('...' if len(env_content) > 100 else '')
                })
        
        # Find custom command definitions
        custom_cmd_pattern = r'\\newcommand\s*{\\(\w+)}\s*\[?.*?\]?\s*{([^}]*)}'
        for match in re.finditer(custom_cmd_pattern, content):
            cmd_name = match.group(1)
            cmd_def = match.group(2)
            fields["custom_commands"].append({
                "name": cmd_name,
                "definition": cmd_def[:100] + ('...' if len(cmd_def) > 100 else '')
            })
        
        # Look for common placeholder patterns 
        placeholder_patterns = [
            r'Your Name', r'John Doe', r'Jane Doe', r'your email', r'your phone', 
            r'your address', r'your position', r'your company', 
            r'your university', r'your degree', r'your skills'
        ]
        
        placeholders = set()
        for pattern in placeholder_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                placeholders.add(match)
        
        fields["placeholders"] = list(placeholders)
        
        return fields

    def _generate_ai_template_analysis(self, template_info: Dict[str, Any], 
                                   job_description: str, template_data: Dict[str, Any], 
                                   template_name: str) -> Dict[str, Any]:
        """
        Generate comprehensive template analysis using OpenAI
        
        Args:
            template_info: Basic template structure information
            job_description: Job description text
            template_data: Candidate profile data
            template_name: Template name
            
        Returns:
            Dictionary with comprehensive template analysis and job matching
        """
        import openai
        import os
        
        # Set OpenAI API key
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            logger.warning("OpenAI API key not available, skipping AI template analysis")
            return {}
            
        openai.api_key = openai_api_key
        
        # Define prompts for creating the analysis
        system_prompt = """You are an AI assistant specialized in analyzing LaTeX templates, job descriptions, and candidate profiles for CV generation. 
        Your task is to analyze a LaTeX template, a job description, and a candidate profile, producing a comprehensive analysis that contains:
        
        1. Complete template analysis including all available fields, structure, customization options, and LaTeX commands
        2. Detailed job requirements extracted from the job description
        3. Analysis of how well the candidate's profile matches the job requirements
        4. Identification of the candidate's strengths and weaknesses relative to the job
        5. Suggestions for improving the profile to better match the job
        6. Template-specific recommendations for highlighting key qualifications
        
        Your output should be a single, well-structured JSON object with all this information.
        """
        
        user_prompt = f"""
        Create a comprehensive analysis for a CV generation system with the following inputs:
        
        TEMPLATE INFO:
        {json.dumps(template_info, indent=2)}
        
        JOB DESCRIPTION:
        {job_description[:2000] if job_description else "No job description provided."}
        
        CANDIDATE PROFILE DATA:
        {json.dumps(template_data, indent=2)}
        
        TEMPLATE NAME: {template_name}
        
        FORMAT YOUR RESPONSE AS A SINGLE, WELL-STRUCTURED JSON OBJECT with these main sections:
        1. "template_analysis": An AI-generated analysis of template strengths, weaknesses, and optimal uses
        2. "customization_options": Key ways this template can be customized
        3. "section_mapping": How template sections map to candidate data fields
        4. "job_match": Comprehensive analysis of how the candidate profile matches the job requirements, including:
           - extracted_requirements (detailed breakdown of job requirements)
           - profile_enhancement (analysis of matches, gaps, and improvement suggestions)
           - template_specific_recommendations (how to use this specific template to highlight key qualifications)
        
        Return ONLY a valid JSON object without any additional text or explanation.
        """
        
        try:
            # Call OpenAI API
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            generated_content = response.choices[0].message.content.strip()
            
            # Extract JSON from the response
            json_match = re.search(r'\{.*\}', generated_content, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                try:
                    ai_analysis = json.loads(json_str)
                    return ai_analysis
                except json.JSONDecodeError:
                    logger.warning("Failed to decode JSON from AI template analysis response")
                    return {}
            else:
                logger.warning("No JSON found in AI template analysis response")
                return {}
                
        except Exception as e:
            logger.warning(f"Error generating AI template analysis: {str(e)}")
            return {}

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
            filled_files = self._ai_fill_template(template_dir, output_dir, template_data, template_info, job_description)
            
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
                
                if self._fill_file(input_path, output_path, template_data):
                    modified_files.append(rel_path)
            
            # Look for any other detected fields in other files
            for rel_path, fields in template_info.get("detected_fields", {}).items():
                if rel_path not in template_info.get("main_files", []) and fields:
                    input_path = os.path.join(template_dir, rel_path)
                    output_path = os.path.join(output_dir, rel_path)
                    
                    if self._fill_file(input_path, output_path, template_data):
                        modified_files.append(rel_path)
            
            # Create a result report
            result = {
                "template_info": template_info,
                "output_dir": output_dir,
                "modified_files": modified_files,
                "main_file": template_info.get("main_files", [""])[0] if template_info.get("main_files") else ""
            }
            
            return result

    def _ai_fill_template(self, template_dir: str, output_dir: str, template_data: Dict[str, Any], 
                        template_info: Dict[str, Any], job_description: str) -> List[str]:
        """
        Use OpenAI to fill the entire template based on comprehensive analysis
        
        Args:
            template_dir: Path to source template directory
            output_dir: Path to output directory
            template_data: User data to fill the template with
            template_info: Template analysis information including AI analysis
            job_description: Job description text
            
        Returns:
            List of modified files
        """
        import openai
        import os
        
        modified_files = []
        
        # Set OpenAI API key
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            logger.warning("OpenAI API key not available, skipping AI template filling")
            return modified_files
            
        openai.api_key = openai_api_key
        
        # Read all main template files
        template_files_content = {}
        for rel_path in template_info.get("main_files", []):
            file_path = os.path.join(template_dir, rel_path)
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    template_files_content[rel_path] = f.read()
            except Exception as e:
                logger.warning(f"Error reading template file {file_path}: {str(e)}")
        
        if not template_files_content:
            logger.warning("No template files found for AI filling")
            return modified_files
        
        # Define prompts for AI filling
        system_prompt = """You are an AI assistant specialized in generating LaTeX CV documents. Your task is to fill a LaTeX template with candidate data, optimizing it for a specific job description. 
        
        Follow these rules:
        1. Maintain the overall LaTeX structure and commands of the original template
        2. Replace placeholder content with real candidate data
        3. Ensure proper LaTeX syntax including escaping special characters
        4. Highlight skills and experiences that match the job requirements
        5. Format content professionally and consistently
        6. Only modify the actual content, not the template structure itself
        
        Your output should be valid LaTeX files that will compile without errors.
        """
        
        # Process each main file
        for rel_path, template_content in template_files_content.items():
            output_path = os.path.join(output_dir, rel_path)
            
            # Create the prompt for this specific file
            user_prompt = f"""
            Fill the following LaTeX template with the candidate's data, optimized for the job description.
            
            JOB DESCRIPTION:
            {job_description[:1500] if job_description else "No job description provided."}
            
            CANDIDATE PROFILE DATA:
            {json.dumps(template_data, indent=2)}
            
            TEMPLATE ANALYSIS:
            {json.dumps(template_info.get("template_analysis", {}), indent=2)}
            {json.dumps(template_info.get("section_mapping", {}), indent=2)}
            
            ORIGINAL TEMPLATE CONTENT:
            ```latex
            {template_content}
            ```
            
            INSTRUCTIONS:
            1. Fill in the template with the candidate's data
            2. Highlight skills and experiences relevant to the job
            3. Maintain correct LaTeX syntax
            4. Ensure special characters are properly escaped
            5. Remove any placeholder content or sample data
            6. Format the content professionally
            
            Return ONLY the filled LaTeX content without any additional explanations or markdown formatting. Just the plain LaTeX content that I can directly write to a file.
            """
            
            try:
                # Call OpenAI API
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.3,
                    max_tokens=2500
                )
                
                filled_content = response.choices[0].message.content.strip()
                
                # Remove any markdown code block markers if present
                filled_content = re.sub(r'^```latex\s*', '', filled_content)
                filled_content = re.sub(r'\s*```$', '', filled_content)
                
                # Ensure the output directory exists
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                
                # Write the filled content to the output file
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(filled_content)
                
                logger.info(f"AI filled template file: {output_path}")
                modified_files.append(rel_path)
                
            except Exception as e:
                logger.error(f"Error in AI template filling for {rel_path}: {str(e)}")
        
        return modified_files

    def _fill_file(self, input_path: str, output_path: str, template_data: Dict[str, Any]) -> bool:
        """
        Fill a single LaTeX file with user data (traditional method, fallback when AI is not available)
        
        Args:
            input_path: Path to input LaTeX file
            output_path: Path to output LaTeX file
            template_data: User data to fill the template with
            
        Returns:
            Boolean indicating if any changes were made
        """
        if not os.path.exists(input_path):
            return False
        
        # Read input file
        with open(input_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        original_content = content
        modified = False
        
        # Process common CV commands
        for field, value in template_data.items():
            # Skip empty or non-string values for simple replacement
            if not value or not isinstance(value, str):
                continue
            
            # Try multiple variants of the field name
            field_variants = [field]
            if field == 'name':
                field_variants.extend(['fullname', 'firstname'])
            elif field == 'email':
                field_variants.append('mail')
            elif field == 'phone':
                field_variants.extend(['telephone', 'mobile', 'cell'])
            elif field == 'address':
                field_variants.extend(['location', 'city', 'country'])
            elif field == 'profile_summary':
                field_variants.extend(['summary', 'objective', 'about', 'personal', 'bio'])
                
            # Special case for address formatting - handle differently
            if field == 'address' and 'email' in template_data:
                # Handle special formatting for address and email/linkedin
                address_lines = prepare_address_format(
                    value, 
                    template_data.get('email'), 
                    template_data.get('linkedin')
                )
                
                # Look for any address commands
                address_patterns = [fr'\\address\s*{{\s*[^}}]*\s*}}' for _ in range(len(address_lines))]
                
                # Find all address command instances
                address_matches = []
                for pattern in address_patterns:
                    matches = list(re.finditer(pattern, content))
                    address_matches.extend(matches)
                
                # Sort by position in the content
                address_matches.sort(key=lambda m: m.start())
                
                # Replace with formatted address values
                for i, match in enumerate(address_matches[:len(address_lines)]):
                    safe_value = safe_template_value(address_lines[i])
                    replacement = f'\\address{{{safe_value}}}'
                    span = match.span()
                    content = content[:span[0]] + replacement + content[span[1]:]
                    modified = True
                
                continue  # Skip normal processing for address
            
            # Regular replacement for other fields
            for variant in field_variants:
                pattern = fr'\\{variant}\s*{{\s*[^}}]*\s*}}'
                if re.search(pattern, content):
                    # Use safe template value to handle escaping properly
                    safe_value = safe_template_value(value)
                    replacement = f'\\{variant}{{{safe_value}}}'
                    content = re.sub(pattern, replacement, content)
                    modified = True
                    logger.debug(f"Replaced \\{variant}{{...}} with '{safe_value}' in {os.path.basename(input_path)}")
        
        # Handle complex sections if needed (education, experience, etc.)
        for section in ['experience', 'education', 'skills', 'languages', 'certifications', 'projects']:
            if section in template_data and isinstance(template_data[section], list) and template_data[section]:
                content = self._process_section(content, section, template_data[section])
                modified = True
        
        # Only write if content was modified
        if modified:
            # Ensure the output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Write output file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
            logger.info(f"Filled template file: {output_path}")
            
            return True
        
        return False

    def _process_section(self, content: str, section_name: str, section_data: List[Dict[str, Any]]) -> str:
        """
        Process a complex section of the CV (experience, education, etc.)
        
        This is a placeholder implementation. In a real-world scenario, this would
        need to understand the specific structure of each template and section.
        
        Args:
            content: LaTeX file content
            section_name: Name of the section (experience, education, etc.)
            section_data: List of dictionaries with section data
            
        Returns:
            Modified LaTeX content
        """
        # For now, we'll just leave this as a placeholder. In a real implementation,
        # we would need to analyze the template's structure for each section and generate
        # the appropriate LaTeX code based on the data.
        
        # This would require template-specific logic, as different templates structure
        # these sections differently.
        
        logger.info(f"Processing {section_name} section with {len(section_data)} items")
        
        return content

    def generate_debug_report(self, template_info: Dict[str, Any], output_path: str) -> str:
        """
        Generate a debug report for a template analysis
        
        Args:
            template_info: Template analysis information
            output_path: Path to save the report
            
        Returns:
            Path to the generated report
        """
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Replace debug.tex with debug.json
        json_output_path = output_path.replace(".tex", ".json")
        
        # Create JSON debug report
        debug_data = {
            "template": {
                "path": template_info.get('path'),
                "structure": template_info.get('structure', 'unknown'),
                "main_files": template_info.get("main_files", []),
                "support_files": template_info.get("support_files", [])
            },
            "detected_fields": {}
        }
        
        # Add detected fields
        for file, fields in template_info.get("detected_fields", {}).items():
            debug_data["detected_fields"][file] = {
                "commands": fields.get("commands", []),
                "environments": fields.get("environments", []),
                "custom_commands": fields.get("custom_commands", []),
                "placeholders": fields.get("placeholders", [])
            }
        
        # Write JSON data
        with open(json_output_path, 'w', encoding='utf-8') as f:
            json.dump(debug_data, f, indent=2, ensure_ascii=False)
        
        # For backward compatibility, also create minimal debug.tex
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("% Template Analysis Debug Report - See debug.json for full details\n\n")
            f.write(f"% Template path: {template_info.get('path')}\n")
            f.write(f"% Debug data stored in: {os.path.basename(json_output_path)}\n")
        
        return json_output_path