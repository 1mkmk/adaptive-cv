from fastapi import APIRouter, Depends, HTTPException, Body, Response
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Dict
import logging
from datetime import datetime
import base64
import os
from fastapi.responses import FileResponse, StreamingResponse
import io

from ..database import get_db
from ..models.job import Job
from ..services.cv_service import generate_cv as cv_generate_service
from ..services.cv_service import generate_cv_with_template
from ..services.cv_service import get_job
from ..services.latex_cv_generator import PDF_OUTPUT_DIR, LATEX_OUTPUT_DIR, TEMPLATE_DIR, get_available_templates

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PromptRequest(BaseModel):
    prompt: str
    job_id: int = None
    format: str = "markdown"  # Available formats: "markdown", "pdf"
    photo_path: str = None  # Add this new field to track user's profile photo

router = APIRouter(
    tags=["generate"]
)

@router.post("", response_model=Dict[str, str])
def generate_cv(request: PromptRequest, db: Session = Depends(get_db)):
    """Generate a tailored CV based on the job description"""
    try:
        # Log the generation request
        logger.info(f"Generating CV for job_id: {request.job_id if request.job_id else 'No Job ID'} in format: {request.format}")
        
        # Add photo instructions to the prompt if a photo path is provided
        enhanced_prompt = request.prompt
        if request.photo_path and os.path.exists(request.photo_path):
            photo_instruction = f"""
Important: If the LaTeX template contains an image placeholder (using \\includegraphics), 
replace it with the user's profile photo using this path: {request.photo_path}
Example: \\includegraphics[width=0.6\\columnwidth]{{{request.photo_path}}}
"""
            enhanced_prompt = photo_instruction + "\n\n" + enhanced_prompt
        else:
            photo_instruction = """
If the LaTeX template contains an image placeholder (using \\includegraphics),
comment it out since the user has no profile photo.
"""
            enhanced_prompt = photo_instruction + "\n\n" + enhanced_prompt
            
        # Use our CV generation service with specified format and enhanced prompt
        cv_text = cv_generate_service(db, enhanced_prompt, request.job_id, request.format)
        
        # For PDF format, cv_text will be base64-encoded
        if request.format.lower() == "pdf":
            return {
                "result": cv_text,
                "format": "pdf"
            }
        
        # For regular markdown format
        return {"result": cv_text, "format": "markdown"}
    
    except Exception as e:
        logger.error(f"Error in generate_cv endpoint: {e}")
        
        # Zwróć awaryjną odpowiedź zamiast zgłaszania wyjątku
        fallback_cv = f"""# CV Error Recovery

Sorry, we encountered an error while generating your CV, but we've recovered.

## Error Details
{str(e)}

## Next Steps
Please try again or use a simpler job description.

---
*Generated on {datetime.now().strftime('%Y-%m-%d')} by AdaptiveCV*
"""
        
        return {"result": fallback_cv, "format": "markdown"}

@router.get("/templates")
def get_templates():
    """Get list of available LaTeX CV templates"""
    try:
        templates = get_available_templates()
        
        # Format response as a list of simplified template info
        template_list = []
        for template in templates:
            # Get base64 preview image if available
            preview_base64 = None
            if "preview" in template and os.path.exists(template["preview"]):
                try:
                    with open(template["preview"], "rb") as f:
                        image_data = f.read()
                        image_type = os.path.splitext(template["preview"])[1][1:]  # Get extension without dot
                        preview_base64 = f"data:image/{image_type};base64,{base64.b64encode(image_data).decode('utf-8')}"
                except Exception as e:
                    logger.error(f"Error reading preview image: {e}")
            else:
                # Try to find a preview image based on template ID
                for img_ext in [".png", ".jpg", ".jpeg"]:
                    fallback_preview = os.path.join(TEMPLATE_DIR, f"{template['id']}_preview{img_ext}")
                    if os.path.exists(fallback_preview):
                        try:
                            with open(fallback_preview, "rb") as f:
                                image_data = f.read()
                                image_type = os.path.splitext(fallback_preview)[1][1:]  # Get extension without dot
                                preview_base64 = f"data:image/{image_type};base64,{base64.b64encode(image_data).decode('utf-8')}"
                                break
                        except Exception as e:
                            logger.error(f"Error reading fallback preview image: {e}")
            
            # Add a friendly description based on the template name
            template_description = "Professional CV template"
            template_name_lower = template["name"].lower()
            
            if "academic" in template_name_lower:
                template_description = "Academic CV for research and teaching positions"
            elif "faangpath" in template_name_lower:
                template_description = "Clean, modern template optimized for tech jobs"
            elif "wenneker" in template_name_lower:
                template_description = "Elegant two-column layout with photo"
            elif "altacv" in template_name_lower:
                template_description = "Modern sidebar design with colored sections"
            elif "deedy" in template_name_lower:
                template_description = "Compact one-page resume for professionals"
            elif "curve" in template_name_lower:
                template_description = "Stylish CV with curved section headers"
            elif "luxsleek" in template_name_lower:
                template_description = "Luxurious design with gold accents"
            elif "marissa" in template_name_lower or "mayer" in template_name_lower:
                template_description = "Based on Marissa Mayer's CV design"
            elif "rendercv" in template_name_lower:
                template_description = "Clean, minimal design with subtle styling"
            elif "hipster" in template_name_lower:
                template_description = "Creative CV with a modern hipster aesthetic"
            
            template_list.append({
                "id": template["id"],
                "name": template["name"],
                "preview": preview_base64,
                "description": template_description
            })
        
        return {
            "templates": template_list
        }
    except Exception as e:
        logger.error(f"Error getting templates: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get templates: {str(e)}")

@router.get("/pdf/{job_id}")
def generate_pdf_cv(
    job_id: int, 
    template_id: str = None, 
    model: str = None,
    custom_context: str = None,
    db: Session = Depends(get_db)
):
    """Generate a PDF CV using LaTeX template for a specific job"""
    try:
        # Log the generation request with new parameters
        logger.info(f"Generating PDF CV for job_id: {job_id} with template: {template_id or 'default'}, model: {model or 'default'}")
        
        # Use template-based generation with additional parameters
        # Pass model and custom_context to the generation service
        result = generate_cv_with_template(
            db, 
            job_id, 
            template_id, 
            model=model, 
            custom_context=custom_context
        )
        
        # Handle case when PDF is not available (fallback to markdown)
        if not result.get("pdf") and result.get("markdown"):
            return {
                "result": result.get("markdown"),
                "format": "markdown",
                "error": result.get("error", "PDF generation failed, fallback to markdown")
            }
        
        # Normal response with PDF
        response = {
            "result": result["pdf"],
            "format": "pdf"
        }
        
        # Add preview if available
        if result.get("preview"):
            response["preview"] = result["preview"]
            logger.info("CV preview was generated and attached to the response")
            
        return response
    
    except Exception as e:
        logger.error(f"Error in generate_pdf_cv endpoint: {e}")
        
        # Get job description for fallback
        job = db.query(Job).filter(Job.id == job_id).first()
        job_description = job.description if job else "No job description available"
        
        # Fallback to markdown
        fallback_cv = cv_generate_service(db, job_description, job_id, "markdown")
        
        return {
            "result": fallback_cv,
            "format": "markdown",
            "error": str(e)
        }

@router.get("/download/{job_id}")
def download_cv(
    job_id: int, 
    template_id: str = None, 
    model: str = None,
    custom_context: str = None,
    db: Session = Depends(get_db)
):
    """
    Download a generated PDF CV for a specific job.
    Returns a file for download instead of JSON data.
    
    First checks if a file already exists in the PDF_OUTPUT_DIR folder.
    If not, generates the CV and saves it in the appropriate folder.
    Now supports model selection and custom context for generation.
    """
    try:
        # Get job information
        job = get_job(db, job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f"Job with ID: {job_id} not found")
        
        # Check if we already have a saved PDF file for this job and template
        # Only use cached version if no model or custom context is specified
        if job.cv_key and not model and not custom_context:
            pdf_path = os.path.join(PDF_OUTPUT_DIR, f"cv_{job.cv_key}.pdf")
            
            if os.path.exists(pdf_path):
                logger.info(f"Found existing PDF file: {pdf_path}")
                
                # Generate filename for the user with position-company format
                filename = f"CV_{job.title.strip()}-{job.company.strip()}_{datetime.now().strftime('%Y%m%d')}.pdf"
                # Replace invalid characters with underscores
                filename = filename.replace(" ", "_").replace("/", "_").replace("\\", "_").replace(":", "_")
                
                # Return existing file
                return FileResponse(
                    pdf_path,
                    media_type="application/pdf",
                    filename=filename
                )
        
        # If we don't have a saved file or custom parameters were specified, generate CV
        logger.info(f"Generating new CV for job_id: {job_id} with model: {model or 'default'}")
        
        # Generate filename based on job information with position-company format
        filename = f"CV_{job.title.strip()}-{job.company.strip()}_{datetime.now().strftime('%Y%m%d')}.pdf"
        # Replace invalid characters in filename
        filename = filename.replace(" ", "_").replace("/", "_").replace("\\", "_").replace(":", "_")
        
        # Generate CV and save in appropriate folders
        result = generate_cv_with_template(
            db, 
            job_id, 
            template_id, 
            model=model, 
            custom_context=custom_context
        )
        
        if not result.get("pdf"):
            raise HTTPException(status_code=404, detail="Could not generate CV in PDF format")
        
        # Check if we have a PDF file path in the result
        if result.get("pdf_path") and os.path.exists(result["pdf_path"]):
            # Return file from disk
            return FileResponse(
                result["pdf_path"],
                media_type="application/pdf",
                filename=filename
            )
        else:
            # As a last resort, use base64 if we don't have a file
            pdf_data = base64.b64decode(result["pdf"])
            
            # Create StreamingResponse for PDF data
            return StreamingResponse(
                io.BytesIO(pdf_data),
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f"attachment; filename={filename}"
                }
            )
            
    except HTTPException:
        # Przekazuj dalej wyjątki HTTPException
        raise
    except Exception as e:
        logger.error(f"Błąd podczas pobierania CV: {e}")
        raise HTTPException(status_code=500, detail=f"Nie można pobrać CV: {str(e)}")

@router.get("/download/latex/{job_id}")
def download_latex(job_id: int, template_id: str = None, db: Session = Depends(get_db)):
    """
    Download the generated LaTeX file for a specific job.
    Supports specifying a template ID.
    """
    try:
        # Get job information
        job = get_job(db, job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f"Job with ID: {job_id} not found")
        
        # Check if we have a saved LaTeX file
        latex_path = None
        
        # Check if we need to use a specific template
        if template_id:
            logger.info(f"Generating LaTeX file with template: {template_id} for job_id: {job_id}")
            # Generate CV with specified template
            result = generate_cv_with_template(db, job_id, template_id=template_id)
            
            if not result.get("latex_path"):
                raise HTTPException(status_code=404, detail="Could not generate LaTeX file with specified template")
                
            latex_path = result["latex_path"]
        elif job.cv_key:
            # Use existing key if available
            latex_path = os.path.join(LATEX_OUTPUT_DIR, f"cv_{job.cv_key}.tex")
            
            # If the file doesn't exist but we have the key, try looking in subdirectories
            if not os.path.exists(latex_path):
                # Check for files in subdirectories
                job_subdir = os.path.join(LATEX_OUTPUT_DIR, f"{job.cv_key}")
                if os.path.exists(job_subdir) and os.path.isdir(job_subdir):
                    # Look for .tex files in this directory
                    for filename in os.listdir(job_subdir):
                        if filename.endswith(".tex") and not filename.startswith("debug"):
                            latex_path = os.path.join(job_subdir, filename)
                            break
                
                # If still not found, look for cv_15.tex in files subdirectory
                if not os.path.exists(latex_path):
                    files_subdir = os.path.join(LATEX_OUTPUT_DIR, f"{job.cv_key}/files")
                    if os.path.exists(files_subdir) and os.path.isdir(files_subdir):
                        potential_file = os.path.join(files_subdir, "cv_15.tex")
                        if os.path.exists(potential_file):
                            latex_path = potential_file
            
            # If we still don't have a LaTeX file, generate a new one
            if not os.path.exists(latex_path):
                logger.info(f"LaTeX file not found despite having key, generating new CV for job_id: {job_id}")
                result = generate_cv_with_template(db, job_id)
                
                if not result.get("latex_path"):
                    raise HTTPException(status_code=404, detail="Could not generate LaTeX file")
                    
                latex_path = result["latex_path"]
        else:
            # If we don't have a key, we need to generate CV first
            logger.info(f"No CV key, generating new CV for job_id: {job_id}")
            result = generate_cv_with_template(db, job_id)
            
            if not result.get("latex_path"):
                raise HTTPException(status_code=404, detail="Could not generate LaTeX file")
                
            latex_path = result["latex_path"]
        
        # Check if the file exists
        if not os.path.exists(latex_path):
            raise HTTPException(status_code=404, detail=f"LaTeX file not found at {latex_path}")
        
        # Generate filename for the user with position-company format
        filename = f"CV_LaTeX_{job.title.strip()}-{job.company.strip()}_{datetime.now().strftime('%Y%m%d')}.tex"
        # Replace invalid characters with underscores
        filename = filename.replace(" ", "_").replace("/", "_").replace("\\", "_").replace(":", "_")
        
        # Return LaTeX file
        return FileResponse(
            latex_path,
            media_type="application/x-latex",
            filename=filename
        )
            
    except HTTPException:
        # Pass through HTTPExceptions
        raise
    except Exception as e:
        logger.error(f"Error downloading LaTeX file: {e}")
        raise HTTPException(status_code=500, detail=f"Could not download LaTeX file: {str(e)}")

@router.get("/preview/{job_id}")
def preview_cv(job_id: int, db: Session = Depends(get_db)):
    """
    Pobierz podgląd wygenerowanego CV dla konkretnej oferty pracy.
    Zwraca obraz podglądu w formacie PNG do wyświetlenia w przeglądarce.
    """
    try:
        # Pobierz informacje o ofercie pracy
        job = get_job(db, job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f"Nie znaleziono oferty pracy o ID: {job_id}")
        
        # Sprawdź, czy mamy już zapisany podgląd dla tego CV
        if job.cv_key:
            preview_path = os.path.join(PDF_OUTPUT_DIR, f"cv_{job.cv_key}_preview.png")
            
            if os.path.exists(preview_path):
                logger.info(f"Znaleziono istniejący podgląd: {preview_path}")
                return FileResponse(
                    preview_path,
                    media_type="image/png"
                )
                
        # Generuj CV (lub użyj zapisanego, jeśli istnieje)
        result = generate_cv_with_template(db, job_id)
        
        if not result.get("preview"):
            # Jeśli nie ma podglądu, spróbuj wygenerować go jeszcze raz
            logger.warning(f"Brak podglądu CV dla job_id: {job_id}, próba regeneracji")
            result = generate_cv_with_template(db, job_id)
            
            if not result.get("preview"):
                raise HTTPException(status_code=404, detail="Nie można wygenerować podglądu CV")
        
        # Jeśli mamy ścieżkę do pliku podglądu, użyj jej
        if result.get("preview_path") and os.path.exists(result["preview_path"]):
            return FileResponse(
                result["preview_path"],
                media_type="image/png"
            )
        
        # Jako ostateczność, użyj base64 jeśli nie mamy pliku
        preview_data = base64.b64decode(result["preview"])
        
        # Utwórz StreamingResponse dla danych obrazu
        return StreamingResponse(
            io.BytesIO(preview_data),
            media_type="image/png"
        )
        
    except HTTPException:
        # Przekazuj dalej wyjątki HTTPException
        raise
    except Exception as e:
        logger.error(f"Błąd podczas pobierania podglądu CV: {e}")
        raise HTTPException(status_code=500, detail=f"Nie można pobrać podglądu CV: {str(e)}")