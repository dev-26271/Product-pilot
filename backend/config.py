import os
from dotenv import load_dotenv

# Load workspace configuration variables from local environmental scopes
load_dotenv()

N8N_WEBHOOK = os.getenv("N8N_WEBHOOK", "https://dev-22.app.n8n.cloud/webhook-test/ebcc15da-a895-46ae-9a37-1746bd3a1fd8")

# Expose GROQ API key supporting standard names and local config naming conventions
GROQ_API_KEY = os.getenv("GROQ_API_KEY") or os.getenv("Groq_API")
