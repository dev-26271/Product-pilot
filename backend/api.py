import requests
from typing import Dict, Any
from backend.config import N8N_WEBHOOK


def create_project(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sends the project payload to the n8n backend and returns the response.
    """

    try:
        response = requests.post(
            N8N_WEBHOOK,
            json=payload,
            timeout=30
        )

        # Raise an exception for 4xx/5xx responses
        response.raise_for_status()

        return {
            "success": True,
            "data": response.json()
        }

    except requests.exceptions.Timeout:
        return {
            "success": False,
            "error": "The backend took too long to respond."
        }

    except requests.exceptions.ConnectionError:
        return {
            "success": False,
            "error": "Unable to connect to the ProductPilot backend."
        }

    except requests.exceptions.HTTPError as e:
        return {
            "success": False,
            "error": f"HTTP Error: {e}"
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }