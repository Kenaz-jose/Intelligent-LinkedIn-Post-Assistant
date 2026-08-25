import os
from dotenv import load_dotenv
load_dotenv(override=True)

print("Tracing Enabled:", os.getenv("LANGCHAIN_TRACING_V2"))
print("API Key loaded:", bool(os.getenv("LANGCHAIN_API_KEY")))

from langsmith import Client
client = Client()
# This will test your connection and list your projects
projects = list(client.list_projects())
print("Connected successfully! Projects found:", [p.name for p in projects])