import os

HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', '8085'))
MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB
CORS_HEADERS = 'Content-Type' 