# wp_api_client.py
import requests
import json
import os
from dotenv import load_dotenv

# Load .env file if it exists (local development)
if os.path.exists('.env'):
    load_dotenv()

class WordPressAPI:
    def __init__(self):
        # Try environment variables first (CI/CD)
        # Then fall back to .env file (local development)
        self.base_url = os.getenv('WP_API_URL')
        self.username = os.getenv('WP_USERNAME')
        self.password = os.getenv('WP_APP_PASSWORD')
        
        if not all([self.base_url, self.username, self.password]):
            raise ValueError(
                "Missing required environment variables. "
                "Please check your .env file or environment settings."
            )
        
        self.auth = (self.username, self.password)
    
    def test_connection(self):
        """Test API connection"""
        try:
            response = requests.get(f"{self.base_url}/users/me", auth=self.auth)
            if response.status_code == 200:
                user_data = response.json()
                print(f"✅ Connected as: {user_data.get('name', 'Unknown')}")
                return True
            else:
                print(f"❌ Connection failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return False

# Usage
if __name__ == "__main__":
    try:
        wp = WordPressAPI()
        wp.test_connection()
    except ValueError as e:
        print(f"Configuration error: {e}")
        print("Please copy .env.example to .env and fill in your credentials.")
