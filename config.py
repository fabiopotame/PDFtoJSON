import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Application settings
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 8085))
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
CORS_HEADERS = 'Content-Type' 

# Oracle Autonomous Database configuration TCP
ORACLE_CONFIG = {
    'user': os.getenv('ORACLE_USER'),
    'password': os.getenv('ORACLE_PASSWORD'),
    'host': os.getenv('ORACLE_HOST'),
    'port': int(os.getenv('ORACLE_PORT')),
    'service_name': os.getenv('ORACLE_SERVICE_NAME')
} 