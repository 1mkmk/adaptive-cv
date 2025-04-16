import requests
import os
import json

class OpenAIClient:
    """
    A client for interacting with the OpenAI ChatGPT API.
    """
    
    def __init__(self, api_key=None):
        """
        Initialize the ChatGPT client.
        
        Args:
            api_key (str, optional): OpenAI API key. If not provided, will try to get from environment.
        """
        # Get API key from parameter or environment variable
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("API key is required. Provide it as a parameter or set OPENAI_API_KEY environment variable.")
        
        # Set up default headers
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
    def generate_response(self, prompt, model="gpt-3.5-turbo", temperature=0.7, max_tokens=None):
        """
        Send a prompt to the ChatGPT API and get a response.
        
        Args:
            prompt (str): The prompt to send to the API
            model (str): The model to use (default: "gpt-3.5-turbo")
            temperature (float): Controls randomness (0-1)
            max_tokens (int, optional): Maximum response length
            
        Returns:
            str: The response from the API
        """
        # Prepare the API request payload
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature
        }
        
        # Add optional parameters if provided
        if max_tokens:
            payload["max_tokens"] = max_tokens
            
        try:
            # Make the API request
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=self.headers,
                data=json.dumps(payload)
            )
            
            # Handle the response
            response.raise_for_status()  # Raise an exception for HTTP errors
            return response.json()["choices"][0]["message"]["content"]
            
        except requests.exceptions.HTTPError as e:
            return f"HTTP Error: {e}"
        except requests.exceptions.ConnectionError:
            return "Connection Error: Failed to connect to the API"
        except requests.exceptions.Timeout:
            return "Timeout Error: Request timed out"
        except requests.exceptions.RequestException as e:
            return f"Request Error: {e}"
        except (KeyError, IndexError) as e:
            return f"Response Parsing Error: {e}"

# Example usage
if __name__ == "__main__":
    try:
        # Create a client
        client = OpenAIClient()
        
        # Example prompt
        prompt = "Generate a professional summary for a software developer's CV"
        
        # Get response
        print("Sending request to ChatGPT API...")
        response = client.generate_response(prompt)
        
        print("\nAPI Response:")
        print(response)
        
    except ValueError as e:
        print(f"Error: {e}")