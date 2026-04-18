import jwt
import time
import os
from dotenv import load_dotenv

load_dotenv()

SECRET = os.getenv("SECRET_KEY")

if not SECRET:
    raise ValueError("SECRET_KEY not found")

payload = {
    "service": "api",
    "exp": time.time() + 300
}

token = jwt.encode(payload, SECRET, algorithm="HS256")

print(token)