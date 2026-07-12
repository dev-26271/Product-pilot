import requests
from typing import Dict, Any
from backend.config import N8N_WEBHOOK

def create_project(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Sends payload to n8n webhook and returns the response JSON."""
    try:
        response = requests.post(N8N_WEBHOOK, json=payload, timeout=30)
        if response.status_code == 200:
            return {
                "success": True,
                "data": response.json()
            }
        else:
            return {
                "success": False,
                "error": f"Backend connection failed with status code: {response.status_code}"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
