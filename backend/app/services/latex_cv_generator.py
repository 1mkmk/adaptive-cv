"""
Moduł do generowania CV w formacie LaTeX i konwersji do PDF.
"""
import os
import tempfile
import subprocess
import shutil
import logging
import re
import base64
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import hashlib
import datetime
import json
import cv2
import numpy as np
from sqlalchemy.orm import Session
from PIL import Image
import io

from app.models.candidate import Candidate
from app.models.job import Job

# Konfiguracja logowania
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ścieżki do szablonów i wyników
ASSETS_DIR = Path(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../assets')))
TEMPLATE_DIR = ASSETS_DIR / 'templates'
TEMPLATE_FOLDERS_DIR = TEMPLATE_DIR / 'templates_extracted'  # Directory for extracted template folders
TEMPLATE_ZIPS_DIR = TEMPLATE_DIR / 'templates_zipped'  # Directory for template ZIP files

# Foldery do zapisywania wygenerowanych plików
OUTPUT_DIR = ASSETS_DIR / 'generated'
LATEX_OUTPUT_DIR = OUTPUT_DIR / 'latex'
PDF_OUTPUT_DIR = OUTPUT_DIR / 'pdf'
PHOTOS_DIR = ASSETS_DIR / 'photos'  # Zdjęcia są teraz przechowywane w assets/photos

# Upewnij się, że foldery istnieją
os.makedirs(LATEX_OUTPUT_DIR, exist_ok=True)
os.makedirs(PDF_OUTPUT_DIR, exist_ok=True)
os.makedirs(TEMPLATE_FOLDERS_DIR, exist_ok=True)
os.makedirs(TEMPLATE_ZIPS_DIR, exist_ok=True)
os.makedirs(PHOTOS_DIR, exist_ok=True)

def save_profile_photo_for_latex(photo_data_uri: str, output_dir: str = None) -> Optional[str]:
    """
    Saves the base64 profile photo to a file for LaTeX templates.
    
    Args:
        photo_data_uri: Base64 data URI of the photo
        output_dir: Directory to save the photo (unused, kept for backward compatibility)
        
    Returns:
        Path to the saved photo file, or None if the photo couldn't be saved
    """
    if not photo_data_uri:
        return None
        
    try:
        # Extract the base64 data from the data URI
        # Format: data:image/jpeg;base64,/9j/4AAQSkZJRgABA...
        if ';base64,' not in photo_data_uri:
            logger.warning("Invalid photo data URI format")
            return None
            
        header, base64_data = photo_data_uri.split(';base64,', 1)
        image_data = base64.b64decode(base64_data)
        
        # Ensure the content is valid image data
        try:
            from PIL import Image
            import io
            img = Image.open(io.BytesIO(image_data))
            # Save as PNG to ensure compatibility
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='PNG')
            image_data = img_bytes.getvalue()
        except Exception as img_err:
            logger.error(f"Error validating/converting image data: {img_err}")
            return None
            
        # Always save to PHOTOS_DIR with name 'photo.png'
        photo_path = os.path.join(PHOTOS_DIR, "photo.png")
        
        # Save the image to a file
        with open(photo_path, 'wb') as f:
            f.write(image_data)
        
        logger.info(f"Saved profile photo to {photo_path}")
        return photo_path
    except Exception as e:
        logger.error(f"Error saving profile photo: {e}")
        return None

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
    if os.path.exists(TEMPLATE_FOLDERS_DIR):
        for folder_name in os.listdir(TEMPLATE_FOLDERS_DIR):
            folder_path = os.path.join(TEMPLATE_FOLDERS_DIR, folder_name)
            
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
    if os.path.exists(TEMPLATE_ZIPS_DIR):
        # Scan for all ZIP files in the templates_zipped directory
        for filename in os.listdir(TEMPLATE_ZIPS_DIR):
            if filename.endswith('.zip'):
                zip_path = os.path.join(TEMPLATE_ZIPS_DIR, filename)
                
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
                        preview_file = os.path.join(TEMPLATE_DIR, preview_name)
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
                "path": str(TEMPLATE_DIR),
                "has_cls": True,
                "tex_files": ["resume_faangpath.tex"],
                "main_tex": "resume_faangpath.tex"
            })
        else:
            # Add a placeholder if absolutely no templates found
            templates.append({
                "id": "default",
                "name": "Default Template",
                "path": str(TEMPLATE_DIR),
                "has_cls": False,
                "tex_files": [],
                "main_tex": None,
                "missing": True
            })
    
    return templates

def experience_to_markdown(experience_list: List[Dict[str, Any]]) -> str:
    """Konwertuje listę doświadczeń do formatu Markdown"""
    if not experience_list:
        return "Brak doświadczenia"
    
    result = ""
    for exp in experience_list:
        company = exp.get('company', 'Firma')
        position = exp.get('position', 'Stanowisko')
        start = exp.get('start_date', '')
        end = 'Obecnie' if exp.get('current', False) else exp.get('end_date', '')
        date_range = f"{start} - {end}" if start or end else ""
        description = exp.get('description', '')
        
        result += f"### {position} | {company}\n"
        if date_range:
            result += f"*{date_range}*\n\n"
        if description:
            result += f"{description}\n\n"
    
    return result.strip()

def education_to_markdown(education_list: List[Dict[str, Any]]) -> str:
    """Konwertuje listę edukacji do formatu Markdown"""
    if not education_list:
        return "Brak danych o edukacji"
    
    result = ""
    for edu in education_list:
        degree = edu.get('degree', '')
        field = edu.get('field', '')
        institution = edu.get('institution', '')
        start = edu.get('start_date', '')
        end = 'Obecnie' if edu.get('current', False) else edu.get('end_date', '')
        date_range = f"{start} - {end}" if start or end else ""
        
        title = ""
        if degree and field:
            title = f"{degree} w {field}"
        elif degree:
            title = degree
        elif field:
            title = field
        
        if title and institution:
            result += f"### {title} | {institution}\n"
        elif title:
            result += f"### {title}\n"
        elif institution:
            result += f"### {institution}\n"
        else:
            result += "### Edukacja\n"
            
        if date_range:
            result += f"*{date_range}*\n\n"
        else:
            result += "\n"
    
    return result.strip()

def generate_job_key(job_dict: Dict[str, Any]) -> str:
    """
    Generuje unikalny klucz dla danego ogłoszenia o pracę.
    Używa kombinacji nazwy stanowiska, firmy i skróconego hasha opisu.
    
    Args:
        job_dict: Dane oferty pracy
        
    Returns:
        Unikalny klucz dla ogłoszenia, bezpieczny do użycia w nazwach plików
    """
    # Pobierz podstawowe dane
    title = job_dict.get('title', 'job').lower().replace(' ', '_')
    company = job_dict.get('company', 'company').lower().replace(' ', '_')
    
    # Utwórz hash z opisu stanowiska
    description_hash = hashlib.md5(job_dict.get('description', '').encode()).hexdigest()[:8]
    
    # Dodaj aktualną datę
    date_str = datetime.datetime.now().strftime('%Y%m%d')
    
    # Połącz wszystko w unikalny klucz
    key = f"{title}_{company}_{date_str}_{description_hash}"
    
    # Usuń wszelkie niepożądane znaki z klucza
    key = re.sub(r'[^a-z0-9_-]', '', key)
    
    return key

def extract_skills_for_job(profile_skills: List[str], job_description: str) -> List[str]:
    """
    Ekstrahuje umiejętności z profilu, które są najbardziej dopasowane do opisu pracy.
    
    Args:
        profile_skills: Lista umiejętności z profilu kandydata
        job_description: Opis stanowiska pracy
        
    Returns:
        Lista umiejętności dopasowanych do stanowiska
    """
    # Prosta implementacja - wyciąga wszystkie umiejętności, które pojawiają się w opisie pracy
    job_description_lower = job_description.lower()
    matched_skills = []
    
    for skill in profile_skills:
        if skill.lower() in job_description_lower:
            matched_skills.append(skill)
    
    # Jeśli nie znaleziono dopasowań, zwróć wszystkie umiejętności
    if not matched_skills:
        return profile_skills
        
    return matched_skills

def prepare_latex_environment(template_id: str = None, profile_photo: str = None) -> Tuple[str, str]:
    """
    Przygotowuje środowisko LaTeX, tworząc tymczasowy katalog i 
    kopiując pliki szablonu LaTeX.
    
    Args:
        template_id: ID wybranego szablonu (nazwa folderu w templates_extracted)
        profile_photo: Base64 data URI of the profile photo
        
    Returns:
        Tuple zawierający ścieżkę do tymczasowego katalogu z szablonem
        oraz nazwę głównego pliku TEX
    """
    # Utwórz tymczasowy katalog
    tmp_dir = tempfile.mkdtemp(prefix="cv_latex_")
    logger.info(f"Utworzono tymczasowy katalog dla LaTeX: {tmp_dir}")
    
    # Zawsze twórz katalog photos w folderze tymczasowym
    tmp_photos_dir = os.path.join(tmp_dir, "photos")
    os.makedirs(tmp_photos_dir, exist_ok=True)
    logger.info(f"Utworzono katalog photos w folderze tymczasowym: {tmp_photos_dir}")
    
    main_tex_file = "resume_faangpath.tex"  # Default main tex file
    photo_path_for_template = None  # Will be sent to the OpenAI chat if a photo is provided
    
    try:
        # Pobierz dostępne szablony
        templates = get_available_templates()
        
        # Wybierz konkretny szablon, jeśli podano
        selected_template = None
        if template_id:
            # Helper function for template ID normalization
            def normalize_id(temp_id):
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
                
            # Try exact match first
            for template in templates:
                if template["id"] == template_id:
                    selected_template = template
                    break
                    
            # If no exact match, try normalized match
            if not selected_template:
                normalized_input_id = normalize_id(template_id)
                for template in templates:
                    if normalize_id(template["id"]) == normalized_input_id:
                        selected_template = template
                        logger.info(f"Found template using normalized ID matching: {template['id']} for input {template_id}")
                        break
        
        # Jeśli nie znaleziono wybranego szablonu lub nie podano ID, użyj pierwszego dostępnego
        if not selected_template and templates:
            selected_template = templates[0]
            logger.info(f"Używam domyślnego szablonu: {selected_template['name']}")
        
        # Jeśli mamy wybrany szablon, przygotuj go
        if selected_template:
            # Sprawdź, czy szablon jest typu ZIP czy już rozpakowany
            if "zip_file" in selected_template:
                # Szablon jest w pliku ZIP, rozpakuj go
                zip_file = selected_template["zip_file"]
                zip_path = os.path.join(TEMPLATE_DIR, zip_file)
                
                if os.path.exists(zip_path):
                    logger.info(f"Rozpakowuję szablon ZIP: {zip_path}")
                    
                    try:
                        # Spróbuj rozpakować za pomocą unzip
                        subprocess.run(['unzip', '-q', '-o', zip_path, '-d', tmp_dir], check=True)
                        logger.info(f"Rozpakowano szablon LaTeX do: {tmp_dir}")
                    except Exception as unzip_error:
                        logger.warning(f"Błąd podczas rozpakowywania przez unzip: {unzip_error}")
                        
                        # Alternatywna metoda rozpakowania za pomocą zipfile
                        try:
                            import zipfile
                            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                                zip_ref.extractall(tmp_dir)
                            logger.info(f"Rozpakowano szablon LaTeX za pomocą zipfile do: {tmp_dir}")
                        except Exception as zipfile_error:
                            logger.error(f"Błąd podczas rozpakowywania za pomocą zipfile: {zipfile_error}")
                            raise
                    
                    # Szukaj plików .tex w rozpakowanym katalogu (także w podkatalogach)
                    tex_files = []
                    
                    for root, dirs, files in os.walk(tmp_dir):
                        for file in files:
                            if file.endswith('.tex'):
                                rel_path = os.path.relpath(os.path.join(root, file), tmp_dir)
                                tex_files.append(rel_path)
                    
                    # Wybierz główny plik .tex
                    if tex_files:
                        # Priorytetyzuj pliki, które zawierają słowa kluczowe
                        priority_files = [f for f in tex_files if any(keyword in f.lower() 
                                          for keyword in ['main', 'resume', 'cv', 'template'])]
                        
                        if priority_files:
                            main_tex_file = priority_files[0]
                        else:
                            main_tex_file = tex_files[0]
                        
                        logger.info(f"Wykryto główny plik TEX: {main_tex_file}")
                    else:
                        logger.warning("Nie znaleziono plików .tex w rozpakowanym archiwum ZIP")
            else:
                # Szablon jest już rozpakowany, skopiuj go
                template_path = selected_template["path"]
                main_tex_file = selected_template.get("main_tex", "resume_faangpath.tex")
                
                logger.info(f"Kopiowanie plików z szablonu: {selected_template['name']} ({template_path})")
                
                # Funkcja do rekursywnego kopiowania katalogów
                def copy_folder_recursively(src, dst):
                    if not os.path.exists(dst):
                        os.makedirs(dst)
                    for item in os.listdir(src):
                        s = os.path.join(src, item)
                        d = os.path.join(dst, item)
                        if os.path.isdir(s):
                            copy_folder_recursively(s, d)
                        else:
                            if not item.startswith('.'):
                                shutil.copy2(s, d)
                
                # Kopiuj cały folder szablonu wraz z podfolderami
                copy_folder_recursively(template_path, tmp_dir)
                logger.info(f"Skopiowano cały folder szablonu wraz z podfolderami do: {tmp_dir}")
            
            # Handle profile photo if provided
            if profile_photo:
                # Save the photo for LaTeX
                photo_path = save_profile_photo_for_latex(profile_photo, str(PHOTOS_DIR))
                
                if photo_path:
                    # We'll only create a single photo file in each location to avoid confusion
                    # The template seems to look for photo.jpg, so we'll use that
                    
                    # Convert the PNG to JPG for LaTeX compatibility
                    try:
                        from PIL import Image
                        import io
                        
                        # Load the PNG
                        with open(photo_path, 'rb') as f:
                            img = Image.open(io.BytesIO(f.read()))
                            
                            # Convert to JPG and save to temp locations
                            
                            # 1. Root directory
                            jpg_path = os.path.join(tmp_dir, "photo.jpg")
                            img.convert('RGB').save(jpg_path, "JPEG", quality=95)
                            logger.info(f"Saved JPG photo to: {jpg_path}")
                            
                            # 2. Photos subdirectory
                            jpg_path_photos = os.path.join(tmp_photos_dir, "photo.jpg")
                            img.convert('RGB').save(jpg_path_photos, "JPEG", quality=95)
                            logger.info(f"Saved JPG photo to: {jpg_path_photos}")
                    except Exception as e:
                        logger.error(f"Error converting photo to JPG: {e}")
                        # Fall back to copying the PNG
                        target_photo_path = os.path.join(tmp_dir, "photo.png")
                        photos_target_path = os.path.join(tmp_photos_dir, "photo.png")
                        shutil.copy(photo_path, target_photo_path)
                        shutil.copy(photo_path, photos_target_path)
                    
                    logger.info(f"Copied profile photo to template directory")
                    
                    # Store the correct relative path for OpenAI to use in the LaTeX file
                    photo_path_for_template = "./photos/photo.jpg"
            
        else:
            # Brak szablonów - użyj awaryjnie pojedynczych plików, jeśli są dostępne
            resume_cls = os.path.join(TEMPLATE_DIR, 'resume.cls')
            resume_tex = os.path.join(TEMPLATE_DIR, 'resume_faangpath.tex')
            
            if os.path.exists(resume_cls) and os.path.exists(resume_tex):
                logger.info("Znaleziono indywidualne pliki szablonu, kopiowanie...")
                
                # Funkcja kopiowania rekursywnego
                def copy_folder_recursively(src, dst):
                    if not os.path.exists(dst):
                        os.makedirs(dst)
                    for item in os.listdir(src):
                        s = os.path.join(src, item)
                        d = os.path.join(dst, item)
                        if os.path.isdir(s):
                            copy_folder_recursively(s, d)
                        else:
                            if not item.startswith('.'):
                                shutil.copy2(s, d)
                
                # Kopiuj wszystkie pliki z katalogu szablonu
                copy_folder_recursively(TEMPLATE_DIR, tmp_dir)
                logger.info(f"Skopiowano całą zawartość folderu szablonu do: {tmp_dir}")
            else:
                logger.error("Nie znaleziono żadnych szablonów ani plików szablonowych")
                raise FileNotFoundError("Nie znaleziono żadnych szablonów CV")
        
        # Sprawdź zawartość katalogu tmp_dir po kopiowaniu
        files_in_tmp = os.listdir(tmp_dir)
        if not files_in_tmp:
            logger.error("Katalog tymczasowy jest pusty po próbie kopiowania. Brak plików szablonu.")
            raise FileNotFoundError("Nie znaleziono plików szablonu LaTeX")
        
        # Wyświetl szczegółową strukturę katalogów i plików
        def log_directory_structure(path, indent=0):
            """Logs the directory structure recursively with indentation for clarity"""
            files = os.listdir(path)
            for f in files:
                full_path = os.path.join(path, f)
                if f.startswith('.'):
                    continue  # Skip hidden files
                if os.path.isdir(full_path):
                    logger.info(f"{'  ' * indent}[D] {f}/")
                    log_directory_structure(full_path, indent + 1)
                else:
                    file_size = os.path.getsize(full_path)
                    logger.info(f"{'  ' * indent}[F] {f} ({file_size} bytes)")
        
        logger.info(f"Struktura katalogu tymczasowego {tmp_dir}:")
        log_directory_structure(tmp_dir)
        
        logger.info(f"Główne pliki w katalogu tymczasowym: {files_in_tmp}")
        
        # Add photo relative path as metadata to be read by generate_latex_cv
        if photo_path_for_template:
            with open(os.path.join(tmp_dir, '.photo_path'), 'w') as f:
                # Save the relative path ./photos/photo.png
                f.write("./photos/photo.png")
            logger.info(f"Saved photo relative path to metadata: ./photos/photo.png")
        
        return tmp_dir, main_tex_file
    
    except Exception as e:
        # W przypadku błędu, usuń tymczasowy katalog
        shutil.rmtree(tmp_dir, ignore_errors=True)
        logger.error(f"Błąd podczas przygotowywania środowiska LaTeX: {e}")
        raise

# Funkcja do zabezpieczania specjalnych znaków LaTeX
def escape_latex(text):
    """Zabezpiecza znaki specjalne w LaTeX."""
    if not text:
        return ""
    # Zamień znaki specjalne LaTeX
    replacements = {
        '%': '\\%',
        '&': '\\&',
        '$': '\\$',
        '#': '\\#',
        '_': '\\_',
        '{': '\\{',
        '}': '\\}',
        '~': '\\textasciitilde{}',
        '^': '\\textasciicircum{}',
        '\\': '\\textbackslash{}',
    }
    # Nie zamieniaj sekwencji, które już są escape'owane
    for char, replacement in replacements.items():
        if char == '\\':
            continue  # Specjalne traktowanie dla backslasha
        # Zamień tylko niezabezpieczone wystąpienia
        pattern = f"(?<!\\\\){re.escape(char)}"
        text = re.sub(pattern, replacement, text)
    return text

def generate_latex_cv(candidate: Dict[str, Any], job: Dict[str, Any], output_dir: str, main_tex_file: str = "resume_faangpath.tex", model: str = None, custom_context: str = None) -> str:
    """
    Generuje plik LaTeX CV na podstawie danych kandydata i oferty pracy, używając OpenAI API.
    
    Args:
        candidate: Dane kandydata
        job: Dane oferty pracy
        output_dir: Katalog, do którego zostanie zapisany plik LaTeX
        main_tex_file: Nazwa głównego pliku TeX (domyślnie resume_faangpath.tex)
        
    Returns:
        Ścieżka do wygenerowanego pliku LaTeX
    """
    import openai
    
    # Ścieżki do plików szablonu
    resume_cls_path = os.path.join(output_dir, 'resume.cls')
    template_tex_path = os.path.join(output_dir, main_tex_file)
    output_tex_path = os.path.join(output_dir, 'output.tex')
    
    # Sprawdź czy główny plik szablonu istnieje
    if not os.path.exists(template_tex_path):
        raise FileNotFoundError(f"Nie znaleziono głównego pliku szablonu {main_tex_file} w {output_dir}")
    
    # Wczytaj szablon LaTeX
    with open(template_tex_path, 'r', encoding='utf-8', errors='ignore') as f:
        template = f.read()
    
    # Prepare data for OpenAI with more details and formatting
    # Format skills with categories if available
    skills_formatted = ""
    skills_list = candidate.get('skills', [])
    
    if not skills_list:
        skills_formatted = "No skills provided in candidate profile"
        logger.warning("No skills available in candidate profile for CV generation")
    else:
        try:
            # Check if skills are simple strings or complex objects with categories
            if len(skills_list) > 0:
                if isinstance(skills_list[0], str):
                    # Simple list of skills
                    skills_formatted = ", ".join(skills_list)
                elif isinstance(skills_list[0], dict) and 'name' in skills_list[0]:
                    # Skills with categories
                    skills_by_category = {}
                    for skill in skills_list:
                        category = skill.get('category', 'Other')
                        if category not in skills_by_category:
                            skills_by_category[category] = []
                        skills_by_category[category].append(skill.get('name'))
                    
                    # Format by category
                    for category, category_skills in skills_by_category.items():
                        skills_formatted += f"- {category}: {', '.join(category_skills)}\n"
                else:
                    # Fallback for any other format
                    skills_formatted = ", ".join([str(s) for s in skills_list])
            else:
                skills_formatted = "No skills provided in candidate profile"
                logger.warning("Empty skills array in candidate profile")
        except Exception as e:
            logger.error(f"Error formatting skills: {e}")
            # Provide a safe fallback
            skills_formatted = "Skills format error. Please update your profile with valid skills."
    
    # Format experience with more details and structure
    experience = ""
    experience_list = candidate.get('experience', [])
    if not experience_list:
        experience = "No professional experience provided in candidate profile"
        logger.warning("No experience available in candidate profile for CV generation")
    else:
        for idx, exp in enumerate(experience_list):
            # Add separator for multiple entries
            if idx > 0:
                experience += "---\n"
                
            # Format core details
            position = exp.get('position', 'Unknown Position')
            company = exp.get('company', 'Unknown Company')
            start_date = exp.get('start_date', '')
            current = exp.get('current', False)
            end_date = 'Present' if current else exp.get('end_date', '')
            description = exp.get('description', '')
            
            experience += f"- Position: {position}\n"
            experience += f"  Company: {company}\n"
            experience += f"  Dates: {start_date} to {end_date}\n"
            
            # Add location if available
            if exp.get('location'):
                experience += f"  Location: {exp.get('location')}\n"
                
            # Add responsibilities with bullet points if they exist
            if isinstance(description, list):
                experience += "  Responsibilities:\n"
                for resp in description:
                    experience += f"    * {resp}\n"
            else:
                experience += f"  Description: {description}\n"
                
            # Add achievements if they exist
            if exp.get('achievements') and isinstance(exp.get('achievements'), list):
                experience += "  Key Achievements:\n"
                for achievement in exp.get('achievements'):
                    experience += f"    * {achievement}\n"
                    
            # Add technologies/skills used if they exist
            if exp.get('technologies') and isinstance(exp.get('technologies'), list):
                experience += f"  Technologies: {', '.join(exp.get('technologies'))}\n"
                
            experience += "\n"
    
    # Format education with more details
    education = ""
    education_list = candidate.get('education', [])
    if not education_list:
        education = "No education background provided in candidate profile"
        logger.warning("No education available in candidate profile for CV generation")
    else:
        for idx, edu in enumerate(education_list):
            # Add separator for multiple entries
            if idx > 0:
                education += "---\n"
                
            # Format core details
            degree = edu.get('degree', 'Unknown Degree')
            field = edu.get('field', 'Unknown Field')
            institution = edu.get('institution', 'Unknown Institution')
            start_date = edu.get('start_date', '')
            current = edu.get('current', False)
            end_date = 'Present' if current else edu.get('end_date', '')
            
            education += f"- Degree: {degree} in {field}\n"
            education += f"  Institution: {institution}\n"
            education += f"  Dates: {start_date} to {end_date}\n"
            
            # Add GPA if available
            if edu.get('gpa'):
                education += f"  GPA: {edu.get('gpa')}\n"
                
            # Add courses if available
            if edu.get('courses') and isinstance(edu.get('courses'), list):
                education += f"  Relevant Courses: {', '.join(edu.get('courses'))}\n"
                
            # Add thesis if available
            if edu.get('thesis'):
                education += f"  Thesis: {edu.get('thesis')}\n"
                
            education += "\n"
            
    # Also prepare summary if available
    summary = candidate.get('summary', '')
    if summary:
        summary = f"Professional Summary:\n{summary}"
    else:
        logger.warning("No professional summary available in candidate profile for CV generation")
    
    # Check if the template includes a photo - assume most templates will use photo.jpg
    has_photo = False
    photo_patterns = [
        "\\includegraphics[width=0.6\\columnwidth]{photo.jpg}",
        "\\includegraphics{photo.jpg}",
        "\\includegraphics[width="
    ]
    
    for pattern in photo_patterns:
        if pattern in template:
            has_photo = True
            logger.info(f"Template contains photo placeholder: {pattern}")
            break
    
    # Check if we have a profile photo path saved during template preparation
    photo_path = None
    photo_info = ""
    photo_metadata_path = os.path.join(output_dir, '.photo_path')
    if os.path.exists(photo_metadata_path):
        with open(photo_metadata_path, 'r') as f:
            photo_path = f.read().strip()
        if photo_path:
            photo_info = f"A profile photo is provided and must be included in the CV.\n\n*** EXTREMELY IMPORTANT: YOU MUST UNCOMMENT ANY COMMENTED PHOTO CODE AND CHANGE THE PATH ***\n\n1. Find any commented code related to photos (look for lines with % before \\includegraphics)\n2. REMOVE the % comment marker\n3. Replace ANY existing path with EXACTLY: '{photo_path}'\n4. Final result should look like: \\includegraphics[width=0.6\\columnwidth]{{{photo_path}}}\n\nFAILURE TO UNCOMMENT AND REPLACE THE PATH WILL RESULT IN NO PHOTO APPEARING IN THE CV.\nThis is one of the most important parts of the template modification!"
            logger.info(f"Including photo information in prompt with relative path: {photo_path}")
    
    # Prompt for OpenAI to generate CV in LaTeX format
    prompt = f"""You are a LaTeX expert who specializes in creating professional CV documents tailored to specific job postings.

I need you to create a CV that specifically addresses the requirements in the job posting. Use the candidate's information to highlight their most relevant experience and skills for this specific position.

CANDIDATE INFORMATION:
- Name: {candidate.get('name', 'Candidate Name')}
- Email: {candidate.get('email', 'email@example.com')}
- Phone: {candidate.get('phone', 'Phone Number')}
- Location: {candidate.get('location', 'Location')}
- LinkedIn: {candidate.get('linkedin', '')}
- Website: {candidate.get('website', '')}
{f"- Photo: {photo_info}" if photo_info else ""}

CANDIDATE PROFESSIONAL SUMMARY:
{summary}

JOB DETAILS:
- Title: {job.get('title', 'Job Title')}
- Company: {job.get('company', 'Company Name')}
- Location: {job.get('location', '')}
- Source URL: {job.get('source_url', '')}

FULL JOB DESCRIPTION:
{job.get('description', '')}

CANDIDATE SKILLS:
{skills_formatted}

CANDIDATE EXPERIENCE:
{experience}

CANDIDATE EDUCATION:
{education}

ADDITIONAL INFORMATION:
- The candidate's profile must be accurately represented in the CV
- Do not invent or fabricate information that is not in the candidate's profile
- Focus on matching existing skills and experience to the job requirements
- If the candidate's profile is missing critical information for the job, note this as "Skills gap: [missing skill]" in the CV

INSTRUCTIONS:
1. Carefully analyze the job description to identify ALL key requirements, skills, and qualifications
2. Ensure that EVERY requirement mentioned in the job posting is addressed in the CV
3. For technical skills and qualifications mentioned in the posting, add them to the candidate's profile even if not explicitly listed in their original skills
4. DO NOT embellish years of experience or specific time-related qualifications
5. Embellish achievements and quantify them with plausible numbers (20-30% improvements, etc.)
6. Add relevant-sounding projects or responsibilities that demonstrate the required skills
7. Use plenty of industry-specific terminology from the job description to create a strong impression
8. Present the candidate's existing experience in a way that connects directly to the job requirements
9. Structure the experience section to emphasize aspects that match the job requirements
10. Create a compelling career objective that addresses ALL key requirements from the job posting
11. Fill out the LaTeX template below with content that ensures EVERY requirement in the job posting is covered

Here's the LaTeX template. Please fill it with the candidate's data while maintaining proper LaTeX syntax and escaping any special LaTeX characters. Ensure the result is valid LaTeX code that can be compiled:

```latex
{template}
```

DO NOT add any explanations or notes. Just return the filled-out LaTeX template.
"""

    try:
        # Check if OpenAI API Key is set - with better error messages
        openai_key = os.getenv("OPENAI_API_KEY")
        if not openai_key:
            logger.error("OpenAI API key is missing or empty. Please set the OPENAI_API_KEY environment variable.")
            raise ValueError("OpenAI API key not set (empty or missing)")
        if openai_key == "your-api-key-here":
            logger.error("OpenAI API key is set to the default placeholder value. Please set a valid API key.")
            raise ValueError("OpenAI API key not set (using placeholder value)")
            
        logger.info("OpenAI API key is properly configured")
        
        # Apply custom context if provided
        if custom_context:
            prompt += f"\n\nAdditional Context for CV Generation:\n{custom_context}"
            logger.info(f"Added custom context to the prompt: {custom_context[:50]}...")
        
        # Determine which model to use
        selected_model = model if model else "gpt-3.5-turbo"
        logger.info(f"Using model: {selected_model} for CV generation")
        
        # Log important information before making API call
        logger.info(f"Preparing to call OpenAI API with model {selected_model}")
        logger.info(f"Candidate skills count: {len(str(skills_formatted).split(','))}")
        logger.info(f"Candidate experience entries: {len(experience.split('---'))}")
        logger.info(f"Candidate education entries: {len(education.split('---'))}")
        logger.info(f"Job description length: {len(job.get('description', ''))}")
        
        # Call OpenAI API to fill template - with better error handling
        logger.info("Sending request to OpenAI API...")
        try:
            import time
            start_time = time.time()
            
            response = openai.ChatCompletion.create(
                model=selected_model,
                messages=[
                    {"role": "system", "content": "You are a LaTeX expert who specializes in creating CV documents that ensure candidates meet ALL requirements from job postings. Your primary goal is to analyze job descriptions in detail and ensure that EVERY single requirement is addressed in the CV. You add skills and qualifications mentioned in the job posting to the candidate's profile, but you DO NOT embellish years of experience or time-specific qualifications. You restructure the candidate's existing experience to emphasize relevant aspects and add projects that demonstrate required skills. Your goal is to make the CV pass automated screening systems by ensuring all requirements are covered while maintaining accuracy about experience timeline.\n\nPHOTO HANDLING INSTRUCTIONS: When the user provides a photo path, you MUST UNCOMMENT any commented photo code in the template (remove the % symbol) and change the path to exactly what is specified. For example, convert '%\\includegraphics[width=0.6\\columnwidth]{photo.jpg}' to '\\includegraphics[width=0.6\\columnwidth]{./photos/photo.png}'. This is CRITICAL for the photo to appear in the final CV."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=4000 if "gpt-4" in selected_model else 2000,  # Higher token limit for GPT-4
                request_timeout=120 if "gpt-4" in selected_model else 60   # Longer timeout for safety
            )
            
            elapsed_time = time.time() - start_time
            logger.info(f"OpenAI API call completed successfully in {elapsed_time:.2f} seconds")
            
        except openai.error.Timeout as timeout_err:
            logger.error(f"OpenAI API request timed out: {timeout_err}")
            raise ValueError(f"OpenAI API request timed out after {timeout_err.timeout} seconds")
            
        except openai.error.APIError as api_err:
            logger.error(f"OpenAI API returned an API Error: {api_err}")
            raise ValueError(f"OpenAI API Error: {str(api_err)}")
            
        except openai.error.AuthenticationError as auth_err:
            logger.error(f"OpenAI API authentication error: {auth_err}")
            raise ValueError(f"OpenAI API authentication failed: {str(auth_err)}")
            
        except openai.error.RateLimitError as rate_err:
            logger.error(f"OpenAI API rate limit exceeded: {rate_err}")
            raise ValueError(f"OpenAI API rate limit exceeded: {str(rate_err)}")
            
        except Exception as err:
            logger.error(f"Unexpected error when calling OpenAI API: {err}")
            raise ValueError(f"Failed to call OpenAI API: {str(err)}")
        
        # Pobierz wygenerowany tekst
        filled_template = response.choices[0].message.content.strip()
        
        # Usuń ewentualne znaczniki kodu Markdown
        if filled_template.startswith("```latex"):
            filled_template = filled_template.split("```latex", 1)[1]
        if filled_template.endswith("```"):
            filled_template = filled_template.rsplit("```", 1)[0]
            
        filled_template = filled_template.strip()
        
        # Automatic fix for photo inclusion if OpenAI didn't uncomment it properly
        if photo_path:
            # Look for commented includegraphics lines
            import re
            commented_photo_pattern = r'%\s*\\includegraphics(\[[^\]]*\])?\{[^}]*\}'
            if re.search(commented_photo_pattern, filled_template):
                logger.warning("Found commented photo includegraphics in template - fixing automatically")
                # Replace commented photo lines with the correct path
                filled_template = re.sub(
                    commented_photo_pattern,
                    f'\\\\includegraphics\\1{{{photo_path}}}',
                    filled_template
                )
                logger.info(f"Automatically fixed photo path in LaTeX template to {photo_path}")
                
            # Also look for photo.jpg in includegraphics and replace it
            photo_jpg_pattern = r'\\includegraphics(\[[^\]]*\])?\{photo\.jpg\}'
            if re.search(photo_jpg_pattern, filled_template):
                logger.info("Found photo.jpg path in template - updating to use the correct path")
                filled_template = re.sub(
                    photo_jpg_pattern,
                    f'\\includegraphics\\1{{{photo_path}}}',
                    filled_template
                )
                logger.info(f"Replaced photo.jpg with {photo_path} in LaTeX template")
        
        # Zapisz wygenerowany plik LaTeX - ale do głównego pliku TEX szablonu, nie do oddzielnego pliku output.tex
        # Nadpisujemy główny plik TEX szablonu w tymczasowym folderze
        with open(template_tex_path, 'w') as f:
            f.write(filled_template)
        
        logger.info(f"Wygenerowano i zapisano dane do głównego pliku szablonu LaTeX: {template_tex_path}")
        
        # Plik .cls jest już w folderze wyjściowym, nie musimy go kopiować
        
        return template_tex_path
        
    except ValueError as value_error:
        # Handle specific errors raised within this function
        logger.error(f"OpenAI API error: {value_error}")
        logger.error(f"Using fallback template generation due to OpenAI API error: {value_error}")
        
        # Save error details to file for debugging
        error_path = os.path.join(output_dir, "openai_error.log")
        with open(error_path, "w") as error_file:
            error_file.write(f"Error when calling OpenAI API: {str(value_error)}\n\n")
            error_file.write(f"Template path: {template_tex_path}\n")
            error_file.write(f"Model: {model}\n")
            error_file.write(f"Custom context: {custom_context}\n\n")
            error_file.write(f"Candidate skills: {skills_formatted[:500]}...\n\n")
            error_file.write(f"Candidate experience: {experience[:500]}...\n\n")
            error_file.write(f"Candidate education: {education[:500]}...\n\n")
        
        # Fallback to simple template replacement
        logger.info("Using fallback template generation mechanism...")
        
        # Podstawowe zastąpienia w szablonie
        template = template.replace('Firstname Lastname', candidate.get('name', 'Candidate Name'))
        
        # Kontakt i lokalizacja
        contact_info = f"{candidate.get('phone', 'Phone')} \\\\ {candidate.get('location', 'Location')}"
        template = template.replace('+1(123) 456-7890 \\\\ San Francisco, CA', contact_info)
        
        # Email i linki
        email = candidate.get('email', 'email@example.com')
        links_info = f"\\href{{mailto:{email}}}{{{email}}} \\\\ "
        if candidate.get('linkedin'):
            linkedin = candidate.get('linkedin', '')
            links_info += f"\\href{{https://{linkedin}}}{{{linkedin}}} \\\\ "
        if candidate.get('website'):
            website = candidate.get('website', '')
            links_info += f"\\href{{{website}}}{{{website}}} "
        
        template = template.replace("\\href{mailto:contact@faangpath.com}{contact@faangpath.com} \\\\ \\href{https://linkedin.com/company/faangpath}{linkedin.com/company/faangpath} \\\\ \\href{www.faangpath.com}{www.faangpath.com}}", links_info)
        
        # Cel zawodowy - bardziej dopasowany do konkretnego stanowiska
        job_title = job.get('title', 'Software Engineer')
        company_name = job.get('company', 'a technology company')
        job_description = job.get('description', '')
        
        # Wyciągnij kluczowe słowa z opisu stanowiska (maksymalnie 3)
        key_terms = []
        potential_keywords = ["experience", "skills", "development", "management", "design", "engineering", 
                         "analysis", "research", "communication", "leadership", "technical"]
        for keyword in potential_keywords:
            if keyword.lower() in job_description.lower() and len(key_terms) < 3:
                key_terms.append(keyword)
        
        # Jeśli nie znaleziono słów kluczowych, użyj domyślnych
        if not key_terms:
            key_terms = ["professional experience"]
        
        key_terms_text = ", ".join(key_terms)
        objective = f"Experienced professional with expertise in {key_terms_text} seeking a {job_title} position at {company_name}."
        template = template.replace("Software Engineer with 2+ years of experience in XXX, seeking full-time XXX roles.", objective)
        
        # Próba dopasowania umiejętności kandydata do opisu stanowiska
        skills_list = candidate.get('skills', [])
        matched_skills = []
        
        for skill in skills_list:
            if skill.lower() in job_description.lower():
                matched_skills.append(skill)
                
        # Jeśli znaleziono dopasowane umiejętności, dodaj je do CV
        if matched_skills:
            # Znajdź sekcję z umiejętnościami w szablonie
            skills_section = "\\section{Skills}\n"
            if skills_section in template:
                skills_content = "\\begin{itemize}\n"
                for skill in matched_skills[:5]:  # Ogranicz do 5 najważniejszych umiejętności
                    skills_content += f"\\item {skill}\n"
                skills_content += "\\end{itemize}\n"
                
                # Zastąp placeholder lub dodaj po sekcji Skills
                template = template.replace(skills_section + "XXX", skills_section + skills_content)
        
        # Zapisz wygenerowany plik LaTeX - nadpisując główny plik szablonu
        with open(template_tex_path, 'w') as f:
            f.write(template)
        
        # Plik .cls jest już w folderze wyjściowym, nie musimy go kopiować
        
        return template_tex_path

def compile_latex_to_pdf(tex_path: str) -> Tuple[str, str]:
    """
    Kompiluje plik LaTeX do PDF i generuje podgląd z wykorzystaniem OpenCV i MiKTeX.
    
    Jeśli pdflatex nie jest dostępny lub nie zadziała, generuje pusty PDF z odpowiednim komunikatem.
    
    Args:
        tex_path: Ścieżka do pliku LaTeX
        
    Returns:
        Tuple zawierający ścieżkę do wygenerowanego pliku PDF oraz ścieżkę do podglądu
    """
    try:
        # Pobierz katalog, w którym znajduje się plik LaTeX
        latex_dir = os.path.dirname(tex_path)
        tex_filename = os.path.basename(tex_path)
        
        # Sprawdź strukturę katalogu przed kompilacją
        logger.info(f"Struktura katalogu przed kompilacją LaTeX:")
        for root, dirs, files in os.walk(latex_dir):
            rel_path = os.path.relpath(root, latex_dir)
            if rel_path == ".":
                rel_path = ""
            else:
                rel_path = rel_path + "/"
            logger.info(f"  Directory: {rel_path}")
            for file in files:
                logger.info(f"    - {rel_path}{file}")
        
        # Upewnij się, że katalog photos istnieje
        photos_dir = os.path.join(latex_dir, "photos")
        if not os.path.exists(photos_dir):
            os.makedirs(photos_dir, exist_ok=True)
            logger.info(f"Utworzono katalog photos w: {photos_dir}")
        
        # Konwertuj i umieść zdjęcie w odpowiednich lokalizacjach
        photo_original = os.path.join(PHOTOS_DIR, "photo.png")
        
        if os.path.exists(photo_original):
            # Konwertuj PNG do JPG dla lepszej kompatybilności z LaTeX
            try:
                from PIL import Image
                
                # Wczytaj obraz PNG
                img = Image.open(photo_original)
                
                # Zapisz kopię jako JPG w katalogu głównym
                photo_jpg_root = os.path.join(latex_dir, "photo.jpg")
                img.convert('RGB').save(photo_jpg_root, "JPEG", quality=95)
                logger.info(f"Konwertowano i zapisano zdjęcie jako JPG w katalogu głównym: {photo_jpg_root}")
                
                # Zapisz kopię jako JPG w katalogu photos
                photo_jpg_subdir = os.path.join(photos_dir, "photo.jpg")
                img.convert('RGB').save(photo_jpg_subdir, "JPEG", quality=95)
                logger.info(f"Konwertowano i zapisano zdjęcie jako JPG w katalogu photos: {photo_jpg_subdir}")
                
                # Dla większej kompatybilności, zapisz również kopie PNG
                photo_png_root = os.path.join(latex_dir, "photo.png")
                shutil.copy(photo_original, photo_png_root)
                
                photo_png_subdir = os.path.join(photos_dir, "photo.png")
                shutil.copy(photo_original, photo_png_subdir)
                
            except Exception as img_err:
                logger.error(f"Błąd konwersji obrazu: {img_err}")
                # W przypadku błędu, skopiuj oryginalne PNG
                photo_png_root = os.path.join(latex_dir, "photo.png")
                photo_png_subdir = os.path.join(photos_dir, "photo.png")
                
                shutil.copy(photo_original, photo_png_root)
                shutil.copy(photo_original, photo_png_subdir)
                logger.info(f"Skopiowano oryginalne zdjęcie PNG do katalogów")
        
        # Lepsza obsługa błędów - uzyskujemy pełen output z pdflatex
        logger.info(f"Uruchamianie pdflatex w katalogu: {latex_dir} dla pliku: {tex_filename}")
        
        # Wykryj, czy korzystamy z MiKTeX lub TeX Live
        try:
            # Sprawdź wersję pdflatex, aby określić, z jakiego systemu korzystamy
            version_process = subprocess.run(
                ['pdflatex', '--version'], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8'
            )
            if "MiKTeX" in version_process.stdout:
                logger.info("Wykryto MiKTeX jako system TeX")
                is_miktex = True
            else:
                logger.info("Wykryto inny system TeX (prawdopodobnie TeX Live)")
                is_miktex = False
        except Exception as version_error:
            logger.warning(f"Nie można określić wersji pdflatex: {version_error}")
            is_miktex = False
        
        # Uruchom pdflatex z odpowiednimi opcjami dla MiKTeX lub TeX Live
        # WAŻNE: Używamy tylko nazwy pliku (bez ścieżki), aby pdflatex szukał plików w katalogu bieżącym
        if is_miktex:
            process = subprocess.run(
                ['pdflatex', '-interaction=nonstopmode', '-halt-on-error', '-synctex=1', 
                 '-enable-installer', tex_filename], 
                cwd=latex_dir, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8'
            )
        else:
            process = subprocess.run(
                ['pdflatex', '-interaction=nonstopmode', '-halt-on-error', tex_filename], 
                cwd=latex_dir, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8'
            )
        
        # Sprawdź, czy kompilacja zakończyła się sukcesem
        if process.returncode != 0:
            logger.error(f"Pierwszy przebieg pdflatex nie powiódł się. Kod błędu: {process.returncode}")
            logger.error(f"Wyjście standardowe: {process.stdout}")
            logger.error(f"Wyjście błędów: {process.stderr}")
            
            # Sprawdź logi LaTeX, aby znaleźć błąd
            log_path = os.path.splitext(tex_path)[0] + '.log'
            if os.path.exists(log_path):
                with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                    log_content = f.read()
                    # Zapisz pełny log do łatwiejszego debugowania
                    debug_log_path = os.path.splitext(tex_path)[0] + '_debug.log'
                    with open(debug_log_path, 'w', encoding='utf-8') as debug_f:
                        debug_f.write(log_content)
                    logger.info(f"Zapisano pełny log kompilacji do: {debug_log_path}")
                    
                    # Szukanie typowych błędów w logu
                    error_lines = []
                    for line in log_content.split('\n'):
                        if '!' in line and not line.startswith('!'):  # Linie błędów często zawierają !
                            error_lines.append(line.strip())
                        elif line.strip().startswith('l.'):  # Linie z numerem linii błędu
                            error_lines.append(line.strip())
                    
                    if error_lines:
                        logger.error(f"Znaleziono błędy w logu LaTeX:")
                        for err in error_lines[:5]:  # Pokaż maksymalnie 5 linii błędów
                            logger.error(f"  - {err}")
                    else:
                        logger.error("Nie znaleziono dokładnego błędu w logu LaTeX")
            
            # Próba wyciągnięcia najważniejszych informacji o błędzie
            error_info = "Nieznany błąd"
            if "! LaTeX Error:" in process.stdout:
                error_parts = process.stdout.split("! LaTeX Error:")
                if len(error_parts) > 1:
                    error_info = error_parts[1].split('\n')[0].strip()
            
            # Zapisz problematyczny plik TeX do łatwiejszego debugowania
            debug_tex_path = os.path.splitext(tex_path)[0] + '_debug.tex'
            try:
                shutil.copy(tex_path, debug_tex_path)
                logger.info(f"Zapisano problematyczny plik TeX do: {debug_tex_path}")
                
                # Sprawdź czy istnieje zdjęcie w PHOTOS_DIR i skopiuj je do katalogu tymczasowego
                source_photo = os.path.join(PHOTOS_DIR, "photo.png")
                if os.path.exists(source_photo):
                    # Upewnij się, że katalog photos istnieje w katalogu tymczasowym
                    latex_dir = os.path.dirname(tex_path)
                    tmp_photos_dir = os.path.join(latex_dir, "photos")
                    os.makedirs(tmp_photos_dir, exist_ok=True)
                    
                    # Skopiuj zdjęcie
                    target_photo = os.path.join(tmp_photos_dir, "photo.png")
                    shutil.copy(source_photo, target_photo)
                    logger.info(f"Skopiowano zdjęcie z {source_photo} do {target_photo} podczas debugowania")
            except Exception as copy_err:
                logger.error(f"Nie można zapisać kopii pliku TeX lub zdjęcia do debugowania: {copy_err}")
            
            raise RuntimeError(f"Błąd kompilacji LaTeX: {error_info}")
        
        # Drugi przebieg dla referencji - używamy tej samej nazwy pliku co w pierwszym przebiegu
        logger.info("Uruchamianie drugiego przebiegu pdflatex dla referencji")
        if is_miktex:
            second_process = subprocess.run(
                ['pdflatex', '-interaction=nonstopmode', '-synctex=1', 
                 '-enable-installer', tex_filename], 
                cwd=latex_dir, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8'
            )
        else:
            second_process = subprocess.run(
                ['pdflatex', '-interaction=nonstopmode', tex_filename], 
                cwd=latex_dir, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8'
            )
        
        # Sprawdź, czy drugi przebieg zakończył się sukcesem
        if second_process.returncode != 0:
            logger.warning(f"Drugi przebieg pdflatex nie powiódł się. Kod błędu: {second_process.returncode}")
            # Tutaj możemy kontynuować, ponieważ pierwszy przebieg już wygenerował PDF
        
        # Ścieżka do wygenerowanego PDF
        pdf_path = os.path.splitext(tex_path)[0] + '.pdf'
        
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"Nie znaleziono wygenerowanego pliku PDF: {pdf_path}")
        
        # Generuj podgląd pierwszej strony PDF
        preview_path = os.path.splitext(tex_path)[0] + '_preview.png'
        logger.info(f"Generowanie podglądu PDF: {preview_path}")
        
        # Strategia wielowarstwowa - próbujemy różnych metod do uzyskania podglądu
        preview_generated = False
        
        # Metoda 1: ImageMagick convert
        if not preview_generated:
            try:
                logger.info("Próba generowania podglądu za pomocą ImageMagick convert...")
                subprocess.run(
                    ['convert', '-density', '150', '-quality', '90', 
                     f"{pdf_path}[0]", # Tylko pierwsza strona
                     preview_path],
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                if os.path.exists(preview_path):
                    logger.info(f"Wygenerowano podgląd PDF za pomocą ImageMagick w pliku: {preview_path}")
                    preview_generated = True
            except Exception as convert_error:
                logger.warning(f"Nie można wygenerować podglądu za pomocą ImageMagick: {convert_error}")
                # Kontynuuj do następnej metody
        
        # Metoda 2: pdf2image (poppler)
        if not preview_generated:
            try:
                logger.info("Próba generowania podglądu za pomocą pdf2image...")
                try:
                    from pdf2image import convert_from_path
                    images = convert_from_path(pdf_path, dpi=150, first_page=1, last_page=1)
                    if images:
                        first_page = images[0]
                        first_page.save(preview_path, 'PNG')
                        logger.info(f"Wygenerowano podgląd PDF za pomocą pdf2image: {preview_path}")
                        preview_generated = True
                    else:
                        logger.warning("pdf2image nie zwrócił żadnych obrazów")
                except ImportError:
                    logger.warning("Biblioteka pdf2image nie jest zainstalowana")
                except Exception as pdf2image_error:
                    logger.warning(f"Błąd podczas generowania podglądu z pdf2image: {pdf2image_error}")
            except Exception as pdf2image_outer_error:
                logger.warning(f"Zewnętrzny błąd pdf2image: {pdf2image_outer_error}")
                # Kontynuuj do następnej metody
        
        # Metoda 3: OpenCV (bezpośrednio)
        if not preview_generated:
            try:
                logger.info("Próba generowania podglądu za pomocą OpenCV...")
                
                # Najpierw spróbujmy skonwertować PDF na obrazek za pomocą zewnętrznego narzędzia
                tmp_img = os.path.splitext(tex_path)[0] + '_tmp.png'
                try:
                    subprocess.run(
                        ['pdftoppm', '-png', '-singlefile', '-r', '150', pdf_path, os.path.splitext(tex_path)[0] + '_tmp'],
                        check=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE
                    )
                    if os.path.exists(tmp_img):
                        # Teraz użyj OpenCV do przetworzenia obrazka
                        img = cv2.imread(tmp_img)
                        if img is not None:
                            # Możemy dodać tutaj dodatkowe przetwarzanie obrazu za pomocą OpenCV
                            # np. zmienić rozmiar, poprawić kontrast, itp.
                            
                            # Zapisz przetworzone zdjęcie
                            cv2.imwrite(preview_path, img)
                            logger.info(f"Wygenerowano podgląd PDF za pomocą OpenCV: {preview_path}")
                            preview_generated = True
                            
                            # Usuń tymczasowy plik
                            os.remove(tmp_img)
                except Exception as pdftoppm_error:
                    logger.warning(f"Nie można użyć pdftoppm do konwersji: {pdftoppm_error}")
            except Exception as opencv_error:
                logger.warning(f"Nie można wygenerować podglądu za pomocą OpenCV: {opencv_error}")
                # Ostatnia metoda zawiodła
        
        # Fallback - w przypadku braku podglądu
        if not preview_generated:
            logger.warning("Wszystkie metody generowania podglądu PDF zawiodły. Brak podglądu.")
            preview_path = None
        
        logger.info(f"PDF wygenerowany pomyślnie w: {pdf_path}")
        return pdf_path, preview_path
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Błąd podczas kompilacji LaTeX: {e}")
        # Sprawdź logi LaTeX, aby znaleźć błąd
        log_path = os.path.splitext(tex_path)[0] + '.log'
        if os.path.exists(log_path):
            with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                log_content = f.read()
                # Zapisz pełny log do łatwiejszego debugowania
                debug_log_path = os.path.splitext(tex_path)[0] + '_error.log'
                with open(debug_log_path, 'w', encoding='utf-8') as debug_f:
                    debug_f.write(log_content)
                logger.info(f"Zapisano pełny log kompilacji do: {debug_log_path}")
                logger.error(f"Podsumowanie loga LaTeX: {log_content[:500]}...") # Tylko pierwsze 500 znaków loga
                
        # Zapisz problematyczny plik TeX do łatwiejszego debugowania
        debug_tex_path = os.path.splitext(tex_path)[0] + '_error.tex'
        try:
            shutil.copy(tex_path, debug_tex_path)
            logger.info(f"Zapisano problematyczny plik TeX do: {debug_tex_path}")
        except Exception as copy_err:
            logger.error(f"Nie można zapisać kopii pliku TeX do debugowania: {copy_err}")
            
        raise RuntimeError(f"Błąd kompilacji LaTeX: {str(e)}")

def generate_cv_from_template(
    db: Session, 
    job_id: int, 
    template_id: str = None, 
    model: str = None, 
    custom_context: str = None
) -> Dict[str, str]:
    """
    Generates a CV in PDF format based on candidate data and job description.
    Additionally saves LaTeX and PDF files in appropriate folders.
    Now supports model selection and custom context for generation.
    
    Args:
        db: Database session
        job_id: Job offer ID
        template_id: Template ID to use (optional)
        model: Language model to use for generation (optional)
        custom_context: Additional context for CV generation (optional)
        
    Returns:
        Dictionary containing the generated CV in PDF format (as Base64) and a preview (also as Base64),
        as well as paths to the saved LaTeX and PDF files
    """
    from app.models.candidate import Candidate
    from app.models.job import Job
    import base64
    
    # Pobierz dane kandydata i oferty pracy
    candidate = db.query(Candidate).first()
    job = db.query(Job).filter(Job.id == job_id).first()
    
    if not candidate:
        raise ValueError("Nie znaleziono profilu kandydata")
    
    if not job:
        raise ValueError(f"Nie znaleziono oferty pracy o ID: {job_id}")
    
    # Prepare candidate data as dictionary - with improved error handling
    candidate_dict = {
        'name': candidate.name,
        'email': candidate.email,
        'phone': candidate.phone,
        'summary': candidate.summary,
        'location': candidate.location,
        'linkedin': candidate.linkedin,
        'website': candidate.website,
    }
    
    # Safely parse JSON fields with proper error handling
    try:
        if candidate.skills and candidate.skills.strip():
            candidate_dict['skills'] = json.loads(candidate.skills)
        else:
            candidate_dict['skills'] = []
            logger.warning("No skills found in candidate profile")
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing skills JSON: {e}")
        logger.error(f"Raw skills data: {repr(candidate.skills)}")
        candidate_dict['skills'] = []
    
    try:
        if candidate.experience and candidate.experience.strip():
            candidate_dict['experience'] = json.loads(candidate.experience)
        else:
            candidate_dict['experience'] = []
            logger.warning("No experience found in candidate profile")
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing experience JSON: {e}")
        logger.error(f"Raw experience data: {repr(candidate.experience)}")
        candidate_dict['experience'] = []
    
    try:
        if candidate.education and candidate.education.strip():
            candidate_dict['education'] = json.loads(candidate.education)
        else:
            candidate_dict['education'] = []
            logger.warning("No education found in candidate profile")
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing education JSON: {e}")
        logger.error(f"Raw education data: {repr(candidate.education)}")
        candidate_dict['education'] = []
        
    # Log the parsed candidate data with detailed information
    logger.info(f"Parsed candidate profile with: {len(candidate_dict['skills'])} skills, " +
                f"{len(candidate_dict['experience'])} experience entries, " +
                f"{len(candidate_dict['education'])} education entries")
                
    # Add detailed debug info in case of issues
    if not candidate_dict['skills']:
        logger.warning(f"Original skills data: {candidate.skills}")
    if not candidate_dict['experience']:
        logger.warning(f"Original experience data: {candidate.experience}")
    if not candidate_dict['education']:
        logger.warning(f"Original education data: {candidate.education}")
        
    # Add some debug info about the overall profile completeness
    missing_fields = []
    if not candidate.name:
        missing_fields.append("name")
    if not candidate.email:
        missing_fields.append("email")
    if not candidate.phone:
        missing_fields.append("phone")
    if not candidate.summary:
        missing_fields.append("summary")
    if not candidate.skills or candidate.skills == "[]":
        missing_fields.append("skills")
    if not candidate.experience or candidate.experience == "[]":
        missing_fields.append("experience")
    if not candidate.education or candidate.education == "[]":
        missing_fields.append("education")
        
    if missing_fields:
        logger.warning(f"Incomplete candidate profile. Missing fields: {', '.join(missing_fields)}")
    else:
        logger.info("Candidate profile appears to be complete with all essential fields")
    
    # Przygotuj dane oferty pracy w formacie słownika
    job_dict = {
        'id': job.id,
        'title': job.title,
        'company': job.company,
        'location': job.location,
        'description': job.description,
        'source_url': job.source_url
    }
    
    # Tymczasowy katalog dla LaTeX
    latex_dir = None
    
    try:
        # Wygeneruj unikalny klucz dla tego ogłoszenia
        job_key = generate_job_key(job_dict)
        logger.info(f"Wygenerowano klucz dla CV: {job_key}")
        
        # Tworzenie folderów dla tego konkretnego CV
        job_latex_dir = os.path.join(LATEX_OUTPUT_DIR, job_key)
        job_pdf_dir = os.path.join(PDF_OUTPUT_DIR, job_key)
        
        # Upewnij się, że foldery istnieją
        os.makedirs(job_latex_dir, exist_ok=True)
        os.makedirs(job_pdf_dir, exist_ok=True)
        
        # Utwórz ścieżki do plików wyjściowych
        latex_output_path = os.path.join(job_latex_dir, f"cv.tex")
        pdf_output_path = os.path.join(job_pdf_dir, f"cv.pdf")
        
        try:
            logger.info(f"Rozpoczynam generowanie CV dla job_id: {job_id} z szablonem: {template_id or 'default'}")
            # Przygotuj środowisko LaTeX - pass the profile photo
            logger.info("Przygotowuję środowisko LaTeX...")
            # Get photo from candidate data
            profile_photo = candidate.photo if hasattr(candidate, 'photo') else None
            latex_dir, main_tex_file = prepare_latex_environment(template_id, profile_photo)
            logger.info(f"Środowisko LaTeX przygotowane w: {latex_dir}, główny plik: {main_tex_file}")
            
            # Generuj plik LaTeX - ścieżka to główny plik szablonu w katalogu tymczasowym
            main_tex_path = os.path.join(latex_dir, main_tex_file)
            logger.info(f"Generating LaTeX file with candidate data and job details (using model: {model})...")
            tex_path = generate_latex_cv(candidate_dict, job_dict, latex_dir, main_tex_file, model, custom_context)
            logger.info(f"Generated LaTeX file: {tex_path}")
            
            # Sprawdź czy plik LaTeX został wygenerowany
            if not os.path.exists(tex_path):
                raise FileNotFoundError(f"Plik LaTeX nie został wygenerowany: {tex_path}")
                
            # Upewnij się, że zwracana ścieżka to faktycznie plik z szablonem, a nie output.tex
            if os.path.basename(tex_path) == "output.tex" and os.path.exists(main_tex_path):
                logger.info(f"Zamieniam output.tex na główny plik szablonu: {main_tex_path}")
                tex_path = main_tex_path
            
            # Zapisz kopię pliku LaTeX dla debugowania w folderze zadania
            debug_tex_path = os.path.join(job_latex_dir, "debug.tex")
            shutil.copy(tex_path, debug_tex_path)
            logger.info(f"Zapisano kopię LaTeX do debugowania: {debug_tex_path}")
            
            # Zapisz kopię struktury katalogów LaTeX dla debugowania
            debug_dir = os.path.join(job_latex_dir, "files")
            os.makedirs(debug_dir, exist_ok=True)
            
            # Kopiuj cały katalog tymczasowy do debug_dir
            def copy_folder_recursively(src, dst):
                if not os.path.exists(dst):
                    os.makedirs(dst)
                for item in os.listdir(src):
                    s = os.path.join(src, item)
                    d = os.path.join(dst, item)
                    if os.path.isdir(s):
                        copy_folder_recursively(s, d)
                    else:
                        if not item.startswith('.'):
                            shutil.copy2(s, d)
                            
            # Kopiuj całą strukturę katalogów - źródłem jest katalog tymczasowy latex_dir
            copy_folder_recursively(latex_dir, debug_dir)
            logger.info(f"Zapisano kopię pełnej struktury katalogów LaTeX do: {debug_dir}")
            
            # Kompiluj do PDF - teraz zwraca tuple (pdf_path, preview_path)
            logger.info("Kompilowanie LaTeX do PDF...")
            pdf_path, preview_path = compile_latex_to_pdf(tex_path)
            logger.info(f"Wygenerowano PDF: {pdf_path}")
            
        except Exception as latex_error:
            logger.error(f"Szczegółowy błąd LaTeX: {str(latex_error)}")
            logger.error(f"Błąd w procesie LaTeX: {latex_error}")
            
            # Jeśli wystąpił błąd w procesie LaTeX, wygeneruj podstawowe CV w Markdown
            # Zamiast używać funkcji generate_cv, która może wymagać działającej sesji,
            # wygenerujemy prostego markdowna ręcznie
            
            markdown_cv = f"""# CV dla {job_dict.get('title', 'pozycji')} w {job_dict.get('company', 'firmie')}
            
## Dane Osobowe
- Imię i nazwisko: {candidate_dict.get('name', 'Kandydat')}
- Email: {candidate_dict.get('email', 'email@example.com')}
- Telefon: {candidate_dict.get('phone', 'Nr telefonu')}
- Lokalizacja: {candidate_dict.get('location', 'Lokalizacja')}

## Podsumowanie
{candidate_dict.get('summary', 'Brak podsumowania')}

## Umiejętności
{', '.join(candidate_dict.get('skills', []))}

## Doświadczenie
{experience_to_markdown(candidate_dict.get('experience', []))}

## Edukacja
{education_to_markdown(candidate_dict.get('education', []))}

---
*Wygenerowano automatycznie dla ogłoszenia o pracę*
            """
            
            # Zapisz markdown jako plik tekstowy w folderze zadania
            fallback_latex_path = os.path.join(job_latex_dir, "fallback.tex")
            with open(fallback_latex_path, 'w') as f:
                f.write(f"% LaTeX compilation failed - fallback to plaintext\n\n{markdown_cv}")
            
            # Zwróć słownik z informacją o błędzie
            return {
                "pdf": None,
                "markdown": markdown_cv,
                "error": str(latex_error),
                "latex_path": fallback_latex_path,
                "job_key": job_key
            }
        
        # Zapisz kopię pliku LaTeX w docelowym folderze
        shutil.copy(tex_path, latex_output_path)
        logger.info(f"Zapisano plik LaTeX: {latex_output_path}")
        
        # Ponieważ zdjęcie jest już zapisane w PHOTOS_DIR, nie musimy go kopiować ponownie
        
        # Zapisz kopię pliku PDF w docelowym folderze
        shutil.copy(pdf_path, pdf_output_path)
        logger.info(f"Zapisano plik PDF: {pdf_output_path}")
        
        # Wczytaj wygenerowany plik PDF
        with open(pdf_path, 'rb') as f:
            pdf_content = f.read()
        
        # Zakoduj zawartość PDF jako Base64
        pdf_base64 = base64.b64encode(pdf_content).decode('utf-8')
        
        # Przygotuj słownik z wynikami
        result = {
            "pdf": pdf_base64,
            "preview": None,
            "latex_path": latex_output_path,
            "pdf_path": pdf_output_path,
            "job_key": job_key
        }
        
        # Jeśli mamy podgląd, dodaj go również do wyniku
        if preview_path and os.path.exists(preview_path):
            try:
                with open(preview_path, 'rb') as f:
                    preview_content = f.read()
                preview_base64 = base64.b64encode(preview_content).decode('utf-8')
                result["preview"] = preview_base64
                
                # Zapisz również podgląd w folderze zadania
                preview_output_path = os.path.join(job_pdf_dir, "preview.png")
                shutil.copy(preview_path, preview_output_path)
                logger.info(f"Zapisano podgląd CV: {preview_output_path}")
                result["preview_path"] = preview_output_path
                
                logger.info(f"Dodano podgląd CV (rozmiar: {len(preview_content)} bajtów)")
            except Exception as preview_error:
                logger.warning(f"Błąd podczas odczytu podglądu: {preview_error}")
        
        # Zapisz wygenerowane CV do oferty pracy
        job.cv = pdf_base64
        job.cv_key = job_key  # Zapisz klucz w bazie danych (wymaga dodania kolumny cv_key)
        db.commit()
        
        return result
    
    except Exception as e:
        logger.error(f"Błąd podczas generowania CV: {e}")
        raise
    
    finally:
        # Usuń tymczasowy katalog
        if latex_dir and os.path.exists(latex_dir):
            shutil.rmtree(latex_dir, ignore_errors=True)
            logger.info(f"Usunięto tymczasowy katalog LaTeX: {latex_dir}")