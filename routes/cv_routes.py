import os
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from werkzeug.utils import secure_filename
from llm.openai import OpenAIClient

cv_bp = Blueprint('cv', __name__)

# Initialize OpenAI client
openai_client = OpenAIClient()

# Define upload folder for profile photos
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # Create upload folder if it doesn't exist

@cv_bp.route('/')
def home():
    return render_template('index.html')

@cv_bp.route('/generate', methods=['POST'])
def generate_cv():
    data = request.json
    user_input = data.get('prompt', '')
    
    prompt = f"""
    Based on the following information, create a professional CV:
    
    {user_input}
    
    Format the CV with appropriate sections for Professional Summary, Experience, 
    Skills, and Education.
    """
    
    try:
        result = openai_client.generate_response(prompt)
        return jsonify({"result": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@cv_bp.route('/save-profile', methods=['POST'])
def save_profile():
    try:
        # Handle profile photo upload
        if 'photo' in request.files and request.files['photo'].filename:
            file = request.files['photo']
            filename = secure_filename(file.filename)
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(file_path)
            # Store file path relative to static folder
            photo_path = f'/uploads/{filename}'
        else:
            photo_path = None
            
        # Process form data
        profile_data = {
            'personal': {
                'full_name': request.form.get('full_name', ''),
                'email': request.form.get('email', ''),
                'phone': request.form.get('phone', ''),
                'address': request.form.get('address', ''),
                'photo': photo_path
            },
            'education': [],
            'skills': request.form.get('skills', ''),
            'languages': [],
            'certifications': []
        }
        
        # Process education entries
        edu_institutions = request.form.getlist('edu_institution[]')
        edu_degrees = request.form.getlist('edu_degree[]')
        edu_years = request.form.getlist('edu_years[]')
        
        for i in range(len(edu_institutions)):
            if edu_institutions[i]:
                profile_data['education'].append({
                    'institution': edu_institutions[i],
                    'degree': edu_degrees[i] if i < len(edu_degrees) else '',
                    'years': edu_years[i] if i < len(edu_years) else ''
                })
        
        # Process language entries
        languages = request.form.getlist('language[]')
        proficiencies = request.form.getlist('proficiency[]')
        
        for i in range(len(languages)):
            if languages[i]:
                profile_data['languages'].append({
                    'language': languages[i],
                    'proficiency': proficiencies[i] if i < len(proficiencies) else 'Intermediate'
                })
        
        # Process certification entries
        cert_names = request.form.getlist('cert_name[]') 
        cert_issuers = request.form.getlist('cert_issuer[]')
        cert_years = request.form.getlist('cert_year[]')
        
        for i in range(len(cert_names)):
            if cert_names[i]:
                profile_data['certifications'].append({
                    'name': cert_names[i],
                    'issuer': cert_issuers[i] if i < len(cert_issuers) else '',
                    'year': cert_years[i] if i < len(cert_years) else ''
                })
        
        # Save profile data to file
        profile_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'profile.json')
        with open(profile_file, 'w') as f:
            json.dump(profile_data, f, indent=2)
        
        # If all goes well, redirect back to homepage
        flash('Profile saved successfully!') if 'flash' in globals() else None
        return redirect(url_for('cv.home'))
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500