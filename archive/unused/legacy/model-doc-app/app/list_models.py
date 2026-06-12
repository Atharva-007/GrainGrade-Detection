import os
from google import genai
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).resolve().parent / ".env")
api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

print("Listing models...")
for m in client.models.list():
    print(f"Name: {m.name}, Actions: {m.supported_actions}")
