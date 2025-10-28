import requests
import os
try:
    # dotenv is optional for runtime; if not installed, proceed without it
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

class APIClient:
    def __init__(self, base_url):
        self.base_url = base_url

    def get(self, endpoint, params=None, raw: bool = False):
        url = f"{self.base_url}/{endpoint}"
        response = requests.get(url, params=params)
        response.raise_for_status()
        if raw:
            return response
        try:
            return response.json()
        except ValueError:
            # Not JSON, return text
            return response.text

    def post(self, endpoint, data=None, files=None, raw: bool = False):
        url = f"{self.base_url}/{endpoint}"
        response = requests.post(url, data=data, files=files)
        response.raise_for_status()
        if raw:
            return response
        try:
            return response.json()
        except ValueError:
            return response.text
    
    def put(self, endpoint, data=None, raw: bool = False):
        url = f"{self.base_url}/{endpoint}"
        response = requests.put(url, json=data)
        response.raise_for_status()
        if raw:
            return response
        try:
            return response.json()
        except ValueError:
            return response.text
    
    def delete(self, endpoint):
        url = f"{self.base_url}/{endpoint}"
        response = requests.delete(url)
        response.raise_for_status()
        return response.status_code == 204  
    

api_client = APIClient(os.getenv("DEV_API"))
celery_client = APIClient(os.getenv("CELERY_API"))