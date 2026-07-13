import os
from dotenv import load_dotenv

# Load workspace configuration variables from local environmental scopes
load_dotenv()

# Expose GROQ API key supporting standard names and local config naming conventions
GROQ_API_KEY = os.getenv("GROQ_API_KEY") or os.getenv("Groq_API")

