from flask import Flask, render_template, request, jsonify
from llm.openai import OpenAIClient
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Import and register blueprints
from routes.cv_routes import cv_bp
from routes.job_routes import job_bp

app.register_blueprint(cv_bp)
app.register_blueprint(job_bp, url_prefix='/jobs')

if __name__ == "__main__":
    # For development use debug=True, for production use debug=False
    app.run(debug=True, host='0.0.0.0', port=5000)