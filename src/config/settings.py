import os
from dotenv import load_dotenv

load_dotenv(override=True)

NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")
NVIDIA_MODEL = os.getenv("NVIDIA_MODEL")