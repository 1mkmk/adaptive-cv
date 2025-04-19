# Adaptive CV Backend

This project is a FastAPI application that allows users to manage job applications and generate tailored CVs based on job descriptions. It uses SQLite as the database for storing job information.

## Project Structure

```
adaptive-cv-backend
├── app
│   ├── __init__.py
│   ├── main.py
│   ├── database.py
│   ├── models
│   │   ├── __init__.py
│   │   └── job.py
│   ├── schemas
│   │   ├── __init__.py
│   │   └── job.py
│   ├── routers
│   │   ├── __init__.py
│   │   ├── jobs.py
│   │   └── generate.py
│   └── services
│       ├── __init__.py
│       ├── job_service.py
│       └── cv_service.py
├── tests
│   ├── __init__.py
│   └── test_api.py
├── .env.example
├── requirements.txt
├── README.md
└── .gitignore
```

## Setup Instructions

1. **Clone the repository:**
   ```
   git clone <repository-url>
   cd adaptive-cv-backend
   ```

2. **Create a virtual environment:**
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install dependencies:**
   ```
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   Copy `.env.example` to `.env` and update the values as needed.

5. **Run the application:**
   ```
   uvicorn app.main:app --reload
   ```

## Usage

- The API provides endpoints for managing job applications, including creating, reading, updating, and deleting job entries.
- Users can also generate tailored CVs based on job descriptions.
- The system supports multiple LaTeX templates stored in the `/assets/templates/` directory.

### Template Management

- LaTeX CV templates should be stored as ZIP files in the `/assets/templates/` directory.
- During startup, the backend runs a script to extract templates and generate preview images.
- The `/generate/templates` endpoint provides a list of available templates with preview images.
- Each template is identified by a unique ID derived from its filename.

### Adding New Templates

To add a new LaTeX CV template:

1. Package your template files into a ZIP file.
2. Place the ZIP in the `/assets/templates/` directory.
3. Restart the backend, or manually run `python generate_template_previews.py`.
4. The script will automatically extract, compile, and generate a preview for the template.

## Testing

To run the tests, use the following command:
```
pytest
```

## License

This project is licensed under the MIT License. See the LICENSE file for details.