# Adaptive CV

![Adaptive CV Logo](/assets/adaptivecv-logo.jpg)

Adaptive CV is an application that helps you create customized resumes for job applications. It uses AI to tailor your CV based on job descriptions, matching your skills and experience to what employers are looking for.

## Features

- **Profile Management**: Create and maintain your comprehensive CV profile
- **Job Tracking**: Save job listings you're interested in
- **AI-Powered CV Generation**: Generate tailored CVs that match job requirements
- **Multiple CV Templates**: Choose from different professional LaTeX templates
- **Multi-Language Support**: Available in English, Polish, German, French, and Spanish
- **Multi-User System**: Create personal accounts with Google authentication
- **LaTeX Editing**: Download and edit the LaTeX source code for full customization
- **Deployment Options**: Run locally or deploy to cloud servers

## Getting Started

### Prerequisites

- Python 3.8+
- Node.js 16+
- LaTeX distribution (for PDF generation)
- OpenAI API key (for CV generation)
- Google OAuth credentials (for authentication in cloud environment)

### Setup and Installation

#### Quick Start

Use the provided start script to run both frontend and backend:

```bash
./start_app.sh
```

Or for Windows:

```bash
start_app.bat
```

#### Manual Setup

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
   - Set `ENV=local` for local development

4. Create the guest user (for local development):
   ```bash
   python create_guest_user.py
   ```

5. Start the server:
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

The application will be available at http://localhost:3000

### Cloud Deployment

For cloud deployment, we provide an Ansible playbook:

1. Navigate to the ansible directory:
   ```bash
   cd ansible
   ```

2. Create a `.env` file with your server details:
   ```
   SERVER_IP=your_server_ip
   SERVER_USER=your_ssh_user
   DOMAIN_NAME=your-domain.com
   ADMIN_EMAIL=admin@example.com
   GOOGLE_CLIENT_ID=your_google_client_id
   GOOGLE_CLIENT_SECRET=your_google_client_secret
   OPENAI_API_KEY=your_openai_key
   ```

3. Run the deployment script:
   ```bash
   ./deploy.sh
   ```

## How to Use

1. **Sign In or Use Guest Mode**: Sign in with your Google account or use guest mode
2. **Choose Your Language**: Select your preferred language from the dropdown
3. **Create Your Profile**: Fill out your personal information, work experience, education, and skills
4. **Add Jobs**: Add job listings you're interested in by pasting the job description
5. **Generate CV**: Click "Generate CV" for any job to create a tailored resume
6. **Choose Template**: Select from multiple professional LaTeX templates
7. **Download or Edit**: Download your CV as PDF or edit the LaTeX source

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
    - `/auth` - Authentication system
- `/frontend` - React frontend application
  - `/src` - Source code
    - `/components` - Reusable UI components
    - `/pages` - Application pages
    - `/services` - API services
    - `/i18n` - Internationalization files
    - `/context` - React contexts (Auth, etc.)
- `/ansible` - Deployment configuration for cloud servers
- `/config` - Environment-specific configurations
- `/assets` - Static assets and templates

## Multi-Environment Support

- **Local**: Uses SQLite database, auto-login as guest user
- **Cloud**: Uses PostgreSQL database, Google OAuth authentication

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built with FastAPI, SQLAlchemy, React, and TypeScript
- UI components from ShadcnUI
- CV generation powered by OpenAI
- Authentication via Google OAuth
- LaTeX templates from various sources
- Deployment with Docker and Ansible