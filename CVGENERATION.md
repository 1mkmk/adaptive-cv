# CV Generation with LaTeX Templates

This document explains how CV generation works in the AdaptiveCV application. The process combines data from user profiles with job descriptions to create tailored CVs using LaTeX templates.

## Architecture Overview

The CV generation system has the following components:

1. **Frontend**: Provides the user interface for selecting jobs and generating CVs
2. **Backend**: Handles LaTeX template processing and PDF generation 
3. **Assets**: Contains LaTeX templates stored in `/assets/templates/`

## CV Generation Flow

### 1. User Initiates CV Generation

When a user clicks "Generate PDF" in the Jobs page:

- Frontend calls `generatePdfCV(jobId)` from `cvService.ts`
- This makes an API request to `/generate/pdf/{job_id}`

### 2. Backend LaTeX Processing

The backend processing follows these steps:

1. **Prepare Environment**:
   - Creates a temporary directory
   - Extracts the LaTeX template from `assets/templates/FAANGPath Simple Template.zip`

2. **Generate LaTeX File**:
   - Retrieves candidate profile and job data from the database
   - Extracts skills relevant to the job description
   - Formats experience and education data
   - Modifies the LaTeX template by replacing placeholders with actual data
   - Saves the generated LaTeX file

3. **Compile to PDF**:
   - Compiles the LaTeX file to PDF using pdflatex/MiKTeX
   - Runs multiple passes to handle references correctly
   - Generates a preview image of the first page (using ImageMagick, pdf2image, or OpenCV)

4. **Return Results**:
   - Encodes the PDF and preview as base64 strings
   - Returns a dictionary with both encoded files
   - Stores the PDF in the job record in the database

### 3. Frontend Display and Download

After receiving the response:

- For successful generation:
  - Frontend receives base64 encoded PDF
  - Displays PDF in browser and/or initiates download

- For timeout/failure:
  - Shows error message
  - Provides direct download link to `/generate/download/{job_id}`

### 4. Direct Download Fallback

If PDF generation times out or fails:

- User can click "Download PDF Directly"
- Frontend opens `/generate/download/{job_id}` URL
- Backend serves the PDF file directly via StreamingResponse

## Key Files

- **Frontend**:
  - `/frontend/src/pages/Jobs.tsx`: Main UI for job selection and CV generation
  - `/frontend/src/services/cvService.ts`: Service for CV generation API calls
  - `/frontend/src/services/api.ts`: API fetching with timeout handling

- **Backend**:
  - `/backend/app/routers/generate.py`: API endpoints for CV generation
  - `/backend/app/services/cv_service.py`: CV generation service
  - `/backend/app/services/latex_cv_generator.py`: LaTeX template processing

- **Assets**:
  - `/assets/templates/FAANGPath Simple Template.zip`: LaTeX template
  - `/assets/templates/resume.cls`: LaTeX class file
  - `/assets/templates/resume_faangpath.tex`: LaTeX template file

## Testing

Tests for the CV generation flow:

- `/frontend/src/__tests__/latex-cv-flow.test.ts`: Tests for LaTeX generation flow
- `/frontend/src/__tests__/backend-integration.test.ts`: Backend integration tests
- `/frontend/src/__tests__/services/cvService.test.ts`: CV service tests

## Troubleshooting

Common issues:

1. **PDF Generation Timeout**:
   - The default timeout for PDF generation is 30 seconds
   - If generation exceeds this time, use the direct download option

2. **LaTeX Compilation Errors**:
   - Check error logs in `/backend/latex_debugging/` (created on failure)
   - Make sure MiKTeX or TeX Live is installed on the backend server

3. **Preview Generation Issues**:
   - The system tries multiple methods (ImageMagick, pdf2image, OpenCV)
   - Lack of preview doesn't affect PDF generation