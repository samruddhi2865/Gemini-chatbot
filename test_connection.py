"""Step 2: send ONE message to Gemini and print the reply.
Run:  python test_connection.py
"""
import os
from dotenv import load_dotenv
from google import genai

load_dotenv()  # reads the .env file

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise SystemExit("GEMINI_API_KEY is missing. Create a .env file first.")

client = genai.Client(api_key=api_key)
model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")

response = client.models.generate_content(model=model, contents="Say hello in one short sentence!")
print("Gemini says:", response.text)
