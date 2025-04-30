"""
Document processor for extracting text from CV files.
"""
import io
import os
import logging
import tempfile
import subprocess
import importlib
import sys
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

logger = logging.getLogger(__name__)

# Import PDF libraries carefully
try:
    import PyPDF2
except ImportError:
    logger.warning("PyPDF2 not installed. PDF extraction might be limited.")
    PyPDF2 = None

try:
    import fitz  # PyMuPDF
except ImportError:
    logger.warning("PyMuPDF (fitz) not installed. PDF extraction might be limited.")
    fitz = None

try:
    import pytesseract
    from pdf2image import convert_from_path
    TESSERACT_AVAILABLE = True
except ImportError:
    logger.warning("pytesseract and/or pdf2image not installed. OCR will not be available.")
    TESSERACT_AVAILABLE = False

try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    logger.warning("OpenCV not installed. Advanced image processing will not be available.")
    OPENCV_AVAILABLE = False

class DocumentProcessor:
    """Class for handling document parsing and text extraction"""
    
    @staticmethod
    async def extract_text_from_file(file_contents: bytes, filename: str) -> Tuple[str, bool]:
        """
        Extract text from a document file
        
        Args:
            file_contents: Binary contents of the file
            filename: Original filename with extension
            
        Returns:
            Tuple of (extracted text, is_placeholder)
        """
        file_ext = os.path.splitext(filename.lower())[1] if filename else ""
        is_placeholder = False
        cv_text = ""
        
        if file_ext == '.pdf':
            cv_text, is_placeholder = await DocumentProcessor.extract_text_from_pdf(file_contents, filename)
        elif file_ext in ['.doc', '.docx']:
            # Word document format not supported yet
            raise ValueError("Word document parsing not yet supported. Please convert to PDF or plain text.")
        else:
            # Assume it's a text file
            logger.info("Parsing as text file")
            cv_text = file_contents.decode('utf-8', errors='ignore')
        
        # If we couldn't extract any text, return an error
        if not cv_text or cv_text.strip() == "":
            raise ValueError("Could not extract text from the provided file.")
            
        logger.info(f"Extracted {len(cv_text)} characters of text from CV")
        return cv_text, is_placeholder

    @staticmethod
    async def extract_text_from_pdf(file_contents: bytes, filename: str) -> Tuple[str, bool]:
        """
        Extract text from a PDF file using multiple methods if necessary
        
        Args:
            file_contents: Binary contents of the PDF file
            filename: Original filename with extension
            
        Returns:
            Tuple of (extracted text, is_placeholder)
        """
        cv_text = ""
        is_placeholder = False
        
        # Try PyPDF2 first
        if PyPDF2:
            try:
                logger.info("Parsing PDF file using PyPDF2")
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_contents))
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    cv_text += page.extract_text() + "\n"
            except Exception as pdf_err:
                logger.error(f"PyPDF2 extraction error: {pdf_err}")
                cv_text = ""
        
        # If PyPDF2 fails, try PyMuPDF
        if not cv_text or cv_text.strip() == "":
            if fitz:
                try:
                    logger.info("PyPDF2 extraction returned empty result. Trying PyMuPDF...")
                    
                    # Save to temporary file for PyMuPDF
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_pdf:
                        temp_pdf.write(file_contents)
                        temp_pdf_path = temp_pdf.name
                    
                    # Open the PDF with PyMuPDF
                    doc = fitz.open(temp_pdf_path)
                    pymupdf_text = ""
                    
                    # Extract text from each page
                    for page_num in range(len(doc)):
                        page = doc[page_num]
                        pymupdf_text += page.get_text() + "\n"
                    
                    # Clean up temp file
                    os.unlink(temp_pdf_path)
                    
                    if pymupdf_text.strip():
                        logger.info(f"Successfully extracted {len(pymupdf_text)} characters using PyMuPDF")
                        cv_text = pymupdf_text
                    else:
                        logger.warning("PyMuPDF extraction returned empty result")
                except Exception as fitz_err:
                    logger.error(f"PyMuPDF extraction error: {fitz_err}")
        
        # If both PyPDF2 and PyMuPDF fail, try OCR
        if not cv_text or cv_text.strip() == "":
            cv_text, is_placeholder = await DocumentProcessor.try_ocr_extraction(file_contents, filename)
            if not cv_text:
                # Create a placeholder CV if all extraction methods fail
                logger.info("Creating a placeholder CV with minimal structure")
                is_placeholder = True
                cv_text = f"""This is a placeholder CV created because the original PDF could not be parsed.
                
Please review and fill in your information:

{{
    "name": "{Path(filename).stem.replace('_', ' ')}",
    "email": "youremail@example.com",
    "phone": "+48 000 000 000",
    "summary": "This is a placeholder CV created because the original PDF could not be parsed. Please edit all fields.",
    "location": "Wrocław, Poland",
    "skills": ["Technical Skills", "Professional Skills", "Software Development"],
    "experience": [{{
        "company": "Company Name",
        "position": "Position Title",
        "start_date": "2020-01",
        "end_date": "",
        "current": true,
        "description": "Please add job description here."
    }}],
    "education": [{{
        "institution": "University Name",
        "degree": "Degree",
        "field": "Field of Study",
        "start_date": "2015-09",
        "end_date": "2019-06",
        "current": false
    }}]
}}
"""
        
        return cv_text, is_placeholder

    @staticmethod
    async def try_ocr_extraction(file_contents: bytes, filename: str) -> Tuple[str, bool]:
        """
        Try to extract text from PDF using OCR techniques
        
        Args:
            file_contents: Binary contents of the PDF file
            filename: Original filename with extension
            
        Returns:
            Tuple of (extracted text, is_placeholder)
        """
        cv_text = ""
        is_placeholder = False
        
        # Try OCR if pytesseract is available
        if TESSERACT_AVAILABLE:
            try:
                # Save PDF to a temporary file for OCR processing
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_pdf:
                    temp_pdf.write(file_contents)
                    temp_pdf_path = temp_pdf.name
                
                logger.info(f"Using pytesseract OCR on PDF: {temp_pdf_path}")
                # Convert PDF to images
                images = convert_from_path(temp_pdf_path)
                
                # Extract text from each image using OCR
                ocr_text = ""
                for i, image in enumerate(images):
                    logger.info(f"Processing page {i+1} with OCR")
                    page_text = pytesseract.image_to_string(image)
                    ocr_text += page_text + "\n"
                    # Print first part of OCR results to log for debugging
                    logger.info(f"OCR text from page {i+1} (first 200 chars): {page_text[:200]}")
                
                if ocr_text.strip():
                    logger.info(f"Successfully extracted {len(ocr_text)} characters using OCR")
                    cv_text = ocr_text
                else:
                    logger.warning("OCR extraction returned empty result")
                
                # Clean up temp PDF file
                os.unlink(temp_pdf_path)
                
            except Exception as ocr_error:
                logger.error(f"OCR processing error: {ocr_error}")
                
                # Try to auto-install packages as a fallback
                try:
                    # Attempt to install missing packages
                    logger.info("Trying to install pytesseract and pdf2image...")
                    subprocess.run(['pip', 'install', 'pytesseract', 'pdf2image'], check=True)
                    
                    # Retry OCR after installation
                    importlib.invalidate_caches()
                    await DocumentProcessor.try_ocr_with_installed_packages(file_contents)
                except Exception as install_error:
                    logger.error(f"Failed to auto-install OCR packages: {install_error}")
        
        # Try pdftotext command if OCR failed
        if not cv_text or cv_text.strip() == "":
            cv_text = await DocumentProcessor.try_pdftotext_command(file_contents)
        
        # Try image-based approach if all else failed
        if not cv_text or cv_text.strip() == "":
            cv_text = await DocumentProcessor.try_image_based_extraction(file_contents, filename)
            # This is a synthetic CV, so mark as placeholder
            if cv_text:
                is_placeholder = True
        
        return cv_text, is_placeholder

    @staticmethod
    async def try_ocr_with_installed_packages(file_contents: bytes) -> str:
        """Try OCR after packages have been installed"""
        try:
            # Reimport necessary modules
            if 'pytesseract' in sys.modules:
                del sys.modules['pytesseract']
            if 'pdf2image' in sys.modules:
                del sys.modules['pdf2image']
            
            import pytesseract
            from pdf2image import convert_from_path
            
            # Configure custom Tesseract path if available
            custom_path = os.environ.get('TESSERACT_PATH')
            if custom_path and os.path.exists(custom_path):
                logger.info(f"Using custom Tesseract path: {custom_path}")
                pytesseract.pytesseract.tesseract_cmd = custom_path
            # Try a few common paths
            elif os.path.exists('/usr/local/bin/tesseract'):
                pytesseract.pytesseract.tesseract_cmd = '/usr/local/bin/tesseract'
            elif os.path.exists('/usr/bin/tesseract'):
                pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'
            elif os.path.exists('/opt/homebrew/bin/tesseract'):
                pytesseract.pytesseract.tesseract_cmd = '/opt/homebrew/bin/tesseract'
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_pdf:
                temp_pdf.write(file_contents)
                temp_pdf_path = temp_pdf.name
            
            # Convert PDF to images
            images = convert_from_path(temp_pdf_path)
            
            # Extract text from each image using OCR
            ocr_text = ""
            for i, image in enumerate(images):
                logger.info(f"Processing page {i+1} with OCR after installation")
                page_text = pytesseract.image_to_string(image)
                ocr_text += page_text + "\n"
            
            # Clean up temp file
            os.unlink(temp_pdf_path)
            
            if ocr_text.strip():
                logger.info(f"Successfully extracted {len(ocr_text)} characters using OCR after installation")
                return ocr_text
            
        except Exception as retry_error:
            logger.error(f"OCR retry failed after installation: {retry_error}")
        
        return ""

    @staticmethod
    async def try_pdftotext_command(file_contents: bytes) -> str:
        """Try using the pdftotext command-line tool"""
        try:
            logger.info("Attempting text extraction with pdftotext system command")
            
            # Create temp files
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_pdf:
                temp_pdf.write(file_contents)
                temp_pdf_path = temp_pdf.name
            
            txt_output = tempfile.NamedTemporaryFile(delete=False, suffix='.txt').name
            
            # Run pdftotext command
            subprocess.run(['pdftotext', temp_pdf_path, txt_output], check=True)
            
            # Read extracted text
            with open(txt_output, 'r', encoding='utf-8', errors='ignore') as f:
                cv_text = f.read()
            
            # Clean up temp files
            os.unlink(temp_pdf_path)
            os.unlink(txt_output)
            
            if cv_text.strip():
                logger.info(f"Successfully extracted {len(cv_text)} characters using pdftotext")
                return cv_text
            
            logger.warning("pdftotext extraction returned empty result")
            
        except Exception as pdftotext_error:
            logger.error(f"pdftotext extraction error: {pdftotext_error}")
        
        return ""

    @staticmethod
    async def try_image_based_extraction(file_contents: bytes, filename: str) -> str:
        """Try to extract information from PDF by analyzing it as images"""
        if not fitz or not OPENCV_AVAILABLE:
            return ""
        
        try:
            logger.info("Text extraction failed. Attempting to treat PDF as images for analysis...")
            
            # Save PDF to temp file for processing
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_pdf:
                temp_pdf.write(file_contents)
                temp_pdf_path = temp_pdf.name
            
            # Open the PDF
            doc = fitz.open(temp_pdf_path)
            image_descriptions = []
            temp_img_files = []
            
            # Process each page as an image
            for page_num in range(len(doc)):
                logger.info(f"Processing PDF page {page_num+1} as image")
                page = doc[page_num]
                
                # Render page to an image (PNG)
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x zoom for better quality
                img_path = f"{temp_pdf_path}_page_{page_num}.png"
                pix.save(img_path)
                temp_img_files.append(img_path)
                
                # Create a raw description of what's in the image using OpenCV
                img = cv2.imread(img_path)
                if img is not None:
                    # Simple image analysis to detect text-like content
                    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)
                    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                    
                    # Check if the image has enough contours that could be text
                    description = f"Page {page_num+1}: "
                    if len(contours) > 50:
                        description += f"Contains text-like content with {len(contours)} potential characters/elements."
                        # Try to detect sections based on font size/weight differences
                        # This is a basic simulation - we're not actually detecting headings, just approximating
                        description += " Likely contains sections for personal info, experience, skills, and education."
                    else:
                        description += f"Contains {len(contours)} elements, possibly graphics or sparse text."
                    
                    image_descriptions.append(description)
            
            # Clean up the temp PDF and images
            os.unlink(temp_pdf_path)
            for img_path in temp_img_files:
                os.unlink(img_path)
            
            if image_descriptions:
                # Create a synthetic CV text that explains what's in the PDF
                cv_text = "CV CONTENT ANALYSIS (EXTRACTED FROM IMAGES):\n\n"
                cv_text += "\n".join(image_descriptions)
                cv_text += "\n\nNote: This CV appears to be a scanned document or protected PDF. Only limited information could be extracted."
                
                logger.info(f"Created synthetic description of PDF content with {len(cv_text)} characters")
                return cv_text
            
        except Exception as img_err:
            logger.error(f"Image-based PDF analysis failed: {img_err}")
        
        return ""