from flask import Blueprint, request, jsonify, render_template, redirect, url_for
import json
import os
import sqlite3
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import uuid

job_bp = Blueprint('job', __name__)

# Initialize in-memory SQLite database
def get_db_connection():
    conn = sqlite3.connect(':memory:', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

# Create jobs table if it doesn't exist
conn = get_db_connection()
conn.execute('''
CREATE TABLE IF NOT EXISTS jobs (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    company TEXT NOT NULL,
    location TEXT,
    description TEXT,
    requirements TEXT,
    source_url TEXT,
    created_at TEXT
)
''')
conn.commit()

# File to store job postings (for persistence)
JOBS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'jobs.json')

# Create data directory if it doesn't exist
os.makedirs(os.path.dirname(JOBS_FILE), exist_ok=True)

# Initialize jobs file if it doesn't exist
if not os.path.exists(JOBS_FILE):
    with open(JOBS_FILE, 'w') as f:
        json.dump([], f)

def load_jobs():
    conn = get_db_connection()
    jobs = conn.execute('SELECT * FROM jobs ORDER BY created_at DESC').fetchall()
    
    if not jobs:  # If memory DB is empty, load from file
        try:
            with open(JOBS_FILE, 'r') as f:
                file_jobs = json.load(f)
                
            # Populate memory DB from file
            if file_jobs:
                for job in file_jobs:
                    conn.execute('''
                    INSERT INTO jobs (id, title, company, location, description, requirements, source_url, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        job['id'],
                        job['title'],
                        job['company'],
                        job.get('location', ''),
                        job.get('description', ''),
                        job.get('requirements', ''),
                        job.get('source_url', ''),
                        job.get('created_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                    ))
                conn.commit()
                
            jobs = conn.execute('SELECT * FROM jobs ORDER BY created_at DESC').fetchall()
        except:
            return []
    
    return [dict(job) for job in jobs]

def save_job_to_db(job_data):
    conn = get_db_connection()
    conn.execute('''
    INSERT INTO jobs (id, title, company, location, description, requirements, source_url, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        job_data['id'],
        job_data['title'],
        job_data['company'],
        job_data.get('location', ''),
        job_data.get('description', ''),
        job_data.get('requirements', ''),
        job_data.get('source_url', ''),
        job_data.get('created_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    ))
    conn.commit()
    
    # Also save to file for persistence
    jobs = load_jobs()
    with open(JOBS_FILE, 'w') as f:
        json.dump(jobs, f)
    
    return job_data

def scrape_job_posting(url):
    """Scrape job information from a URL"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'lxml')
        
        # Generic scraping logic - this will need to be adjusted for specific sites
        title = soup.find('h1') or soup.find('h2')
        title = title.text.strip() if title else "Unknown Position"
        
        # Look for company name
        company_elem = soup.find('meta', property='og:site_name') or \
                      soup.find(string=lambda s: "company" in s.lower() if s else False)
        company = company_elem.get('content') if hasattr(company_elem, 'get') else \
                 company_elem.parent.text if company_elem else "Unknown Company"
        
        # Try to extract location
        location_elem = soup.find(string=lambda s: "location" in s.lower() if s else False)
        location = location_elem.parent.text if location_elem else ""
        
        # Get main content
        content = soup.find('main') or soup.find('article') or soup.find('div', class_='content')
        description = content.text.strip() if content else "No description available"
        
        # Try to extract requirements
        req_section = soup.find(string=lambda s: "requirements" in s.lower() if s else False)
        requirements = req_section.find_next('ul').text if req_section and req_section.find_next('ul') else "No specific requirements listed"
        
        return {
            'title': title,
            'company': company,
            'location': location,
            'description': description,
            'requirements': requirements,
            'source_url': url
        }
    except Exception as e:
        print(f"Error scraping job: {str(e)}")
        return None

@job_bp.route('/')
def all_jobs():
    return render_template('jobs.html', jobs=load_jobs())

@job_bp.route('/history')
def job_history():
    jobs = load_jobs()
    return render_template('job_history.html', jobs=jobs)

@job_bp.route('/create', methods=['GET'])
def create_job_form():
    return render_template('job_form.html')

@job_bp.route('/create', methods=['POST'])
def create_job():
    form_data = request.form
    
    # Check if we're adding via URL or manual form
    if 'job_url' in form_data and form_data.get('job_url').strip():
        # Process URL submission
        url = form_data.get('job_url').strip()
        job_data = scrape_job_posting(url)
        
        if not job_data:
            return "Failed to scrape job data. Please try a different URL or add manually.", 400
            
        # Add missing fields
        job_data['id'] = str(uuid.uuid4())
        job_data['created_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Save to database
        save_job_to_db(job_data)
        return render_template('job_success.html', job=job_data)
    else:
        # Process manual form submission
        new_job = {
            'id': str(uuid.uuid4()),
            'title': form_data.get('title', ''),
            'company': form_data.get('company', ''),
            'location': form_data.get('location', ''),
            'description': form_data.get('description', ''),
            'requirements': form_data.get('requirements', ''),
            'source_url': '',
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        save_job_to_db(new_job)
        return render_template('job_success.html', job=new_job)

@job_bp.route('/<job_id>')
def view_job(job_id):
    conn = get_db_connection()
    job = conn.execute('SELECT * FROM jobs WHERE id = ?', (job_id,)).fetchone()
    
    if not job:
        return "Job not found", 404
    
    return render_template('job_detail.html', job=dict(job))