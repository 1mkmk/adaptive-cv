import requests
from bs4 import BeautifulSoup
import logging
import re
from typing import Dict, Any, Optional
import json
import openai
import os

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY", "your-api-key-here")

def extract_from_url(url: str) -> Optional[Dict[str, Any]]:
    """
    Extract job information from a URL
    """
    try:
        logger.info(f"Extracting job information from URL: {url}")
        
        # Request the webpage
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract text content from the page
        page_text = soup.get_text(separator=' ', strip=True)
        
        # Use OpenAI to extract structured data
        return parse_job_description_with_ai(page_text, url)
        
    except Exception as e:
        logger.error(f"Error extracting job from URL {url}: {e}")
        return None

def parse_job_description_with_ai(text: str, url: str = None) -> Dict[str, Any]:
    """
    Use OpenAI to extract structured job information from text
    """
    try:
        # Limit text length to avoid token limits
        max_length = 4000  # Characters
        if len(text) > max_length:
            text = text[:max_length]
        
        prompt = f"""
        Extract key job information from the following job posting text.
        
        Job Posting Text:
        {text}
        
        Format the output as a JSON object with the following fields:
        - title: Job title
        - company: Company name
        - location: Job location
        - description: Full job description
        - requirements: Key requirements
        - responsibilities: Key responsibilities
        
        Return ONLY the JSON output without any explanation, and ensure it's valid JSON:
        """
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that extracts job information from web pages."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=1000
        )
        
        result = response.choices[0].message.content.strip()
        
        # Clean up the result to get valid JSON
        if result.startswith("```json"):
            result = result.replace("```json", "", 1)
        if result.endswith("```"):
            result = result.replace("```", "", 1)
            
        job_data = json.loads(result.strip())
        
        # Add source URL
        if url:
            job_data["source_url"] = url
            
        return job_data
    
    except Exception as e:
        logger.error(f"Error parsing job description with AI: {e}")
        # Return basic structure if AI parsing fails
        return {
            "title": "Unknown Job Title",
            "company": "Unknown Company",
            "location": "Unknown Location",
            "description": text[:500] + "..." if len(text) > 500 else text,
            "source_url": url if url else None
        }