"""
Template utilities for the LaTeX CV generator.
"""

import os
import logging
from typing import List, Dict
from .config import (
    TEMPLATES_EXTRACTED_DIR,
    TEMPLATES_ZIPPED_DIR,
    TEMPLATE_DIR
)

logger = logging.getLogger(__name__)

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