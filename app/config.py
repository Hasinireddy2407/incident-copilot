"""Central configuration. Every other module reads settings from here."""
import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_BASE_URL = "https://api.groq.com/openai/v1"
MODEL = "openai/gpt-oss-120b"

HINDSIGHT_URL = os.getenv("HINDSIGHT_URL", "http://localhost:8888")
HINDSIGHT_API_KEY = os.getenv("HINDSIGHT_API_KEY") or None   # Cloud only
BANK_ID = os.getenv("BANK_ID", "oncall-team")
