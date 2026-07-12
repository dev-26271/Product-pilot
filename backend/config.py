import os
from dotenv import load_dotenv

# Load workspace configuration variables from local environmental scopes
load_dotenv()

N8N_WEBHOOK = os.getenv("N8N_WEBHOOK")
GROQ_API_KEY = os.getenv("Groq_API")
