# Adaptive CV

![Adaptive CV Logo](/assets/adaptivecv-logo.jpg)

Adaptive CV is an application that helps you create customized resumes for job applications. It uses AI to tailor your CV based on job descriptions, matching your skills and experience to what employers are looking for.

## Features

- **Profile Management**: Create and maintain your comprehensive CV profile
- **Job Tracking**: Save job listings you're interested in
- **AI-Powered CV Generation**: Generate tailored CVs that match job requirements
- **Multiple CV Templates**: Choose from different CV formats (coming soon)

## Getting Started

### Prerequisites

- Python 3.8+
- Node.js 16+
- OpenAI API key (for CV generation)

### Setup and Installation

#### Backend (FastAPI)

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure your environment variables:
   - Copy `.env.example` to `.env` (if not present)
   - Add your OpenAI API key to the `.env` file

4. Start the server:
   ```bash
   uvicorn app.main:app --reload
   ```

The API will be available at http://localhost:8000

#### Frontend (React)

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```

The application will be available at http://localhost:5173

## How to Use

1. **Create Your Profile**: Fill out your personal information, work experience, education, and skills
2. **Add Jobs**: Add job listings you're interested in by pasting the URL or job description
3. **Generate CV**: Click "Generate CV" for any job to create a tailored resume
4. **Review and Export**: Review the generated CV and download it (export feature coming soon)

## API Documentation

Once the backend is running, you can access the API documentation at:
- http://localhost:8000/docs (Swagger UI)
- http://localhost:8000/redoc (ReDoc)

## Project Structure

- `/backend` - FastAPI backend server
  - `/app` - Main application code
    - `/models` - Database models
    - `/routers` - API route handlers
    - `/schemas` - Pydantic schemas for validation
    - `/services` - Business logic services
- `/frontend` - React frontend application
  - `/src` - Source code
    - `/components` - Reusable UI components
    - `/pages` - Application pages
    - `/services` - API services

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built with FastAPI, SQLAlchemy, React, and TypeScript
- UI components from ShadcnUI
- CV generation powered by OpenAI