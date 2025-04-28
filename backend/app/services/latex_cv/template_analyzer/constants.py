"""
Constants used by the template analyzer module.
"""

# Common LaTeX commands used in CV templates
CV_COMMANDS = [
    # Personal information
    'name', 'fullname', 'firstname', 'lastname', 'email', 'phone', 'address', 'location',
    'photo', 'profilephoto', 'picture', 'avatar', 'mobile', 'website', 'homepage',
    'github', 'gitlab', 'bitbucket', 'linkedin', 'twitter', 'skype', 'telegram', 
    'profilesummary', 'summary', 'objective', 'about', 'personal', 'bio',
    
    # Education & Work
    'university', 'college', 'school', 'degree', 'major', 'minor', 'gpa',
    'company', 'position', 'jobtitle', 'role', 'employer', 'organization',
    'supervisor', 'mentor', 'period', 'daterange', 'fromdate', 'todate',
    
    # Skills & Languages
    'skill', 'skills', 'technology', 'technologies', 'language', 'languages',
    'proficiency', 'level', 'rating', 'score', 'expertise',
    
    # Other common CV fields
    'project', 'projects', 'publication', 'publications', 'achievement', 'achievements',
    'award', 'awards', 'certification', 'certifications', 'volunteer', 'volunteering',
    'interest', 'interests', 'hobby', 'hobbies', 'reference', 'references'
]

# Common placeholder patterns in LaTeX templates
PLACEHOLDER_PATTERNS = [
    r'Your Name', r'John Doe', r'Jane Doe', r'your email', r'your phone', 
    r'your address', r'your position', r'your company', 
    r'your university', r'your degree', r'your skills'
]