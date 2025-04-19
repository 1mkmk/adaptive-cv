# Testing the CV Generation Feature

This document provides details on how to test the CV generation functionality, including both automated tests and manual verification.

## Automated Tests

We've created several test suites to verify the CV generation workflow:

### 1. LaTeX CV Flow Tests

These tests specifically verify the LaTeX template-based CV generation flow:

```bash
cd /Users/maciejkasik/Desktop/adaptive-cv/frontend
npm test -- src/__tests__/latex-cv-flow.test.ts
```

Test coverage includes:
- Success path for PDF generation
- Direct download fallback when generation times out
- LaTeX template architecture understanding
- End-to-end flow documentation

### 2. Backend Integration Tests

These tests verify the integration between frontend and backend:

```bash
cd /Users/maciejkasik/Desktop/adaptive-cv/frontend
npm test -- src/__tests__/backend-integration.test.ts
```

Test coverage includes:
- API interactions for CV generation
- Error handling and fallback mechanisms
- PDF download URL generation

### 3. CV Service Tests

These tests verify the frontend CV service functionality:

```bash
cd /Users/maciejkasik/Desktop/adaptive-cv/frontend
npm test -- src/__tests__/services/cvService.test.ts
```

Test coverage includes:
- API calls for CV generation
- PDF display and download functions
- Error handling across all service functions

## Manual Testing Instructions

To manually test the CV generation feature:

### 1. Testing PDF Generation

1. Ensure your backend is running with a properly configured LaTeX environment
2. Navigate to the Jobs page
3. Select a job from the list
4. Click "Generate PDF" button
5. Wait for the PDF generation to complete (up to 30 seconds)
6. Verify PDF opens in a new tab or downloads
7. Check that the PDF contains correct profile and job information

### 2. Testing Direct Download Fallback

1. With the backend running, navigate to the Jobs page
2. Select a job from the list
3. Click "Generate PDF" button
4. If generation times out, verify you see an error message with a fallback option
5. Click "Download PDF Directly"
6. Verify the PDF downloads correctly

### 3. Testing LaTeX Template Changes

If you make changes to the LaTeX template:

1. Modify files in `/assets/templates/`
2. Run the backend with the updated templates
3. Generate a CV to verify the changes appear in the output
4. Check the formatting in the PDF is as expected

## Common Issues and Resolutions

### LaTeX Environment Issues

**Symptom**: PDF generation fails with LaTeX compilation errors

**Resolution**:
1. Ensure a LaTeX distribution (MiKTeX or TeX Live) is installed on the server
2. Check `/var/log/app.log` for detailed error messages
3. Look for temporary LaTeX files generated during compilation

### Timeout Issues

**Symptom**: PDF generation times out consistently 

**Resolution**:
1. Increase the timeout in `frontend/src/services/api.ts` (currently 30 seconds)
2. Optimize LaTeX compilation on the backend 
3. Use the direct download option as a reliable fallback

## Testing in Different Environments

### Development

For local development testing:
```bash
# Run backend tests
cd backend
python -m pytest tests/test_api.py::test_generate_cv_pdf -v

# Run frontend tests
cd frontend
npm test -- src/__tests__/latex-cv-flow.test.ts
```

### Production

For production testing:
1. Use the direct URL for PDF generation: `https://your-app.com/api/generate/pdf/{job_id}`
2. Verify PDF generation completes within reasonable time (typically < 30 seconds)
3. Test the direct download URL: `https://your-app.com/api/generate/download/{job_id}`