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
    'user': os.getenv('ORACLE_USER', 'ADMIN'),
    'password': os.getenv('ORACLE_PASSWORD'),
    'host': os.getenv('ORACLE_HOST', 'adb.sa-saopaulo-1.oraclecloud.com'),
    'port': int(os.getenv('ORACLE_PORT', 1521)),
    'service_name': os.getenv('ORACLE_SERVICE_NAME', 'gb8f3e57eee6934_nh66vvfwukxku4dc_high.adb.oraclecloud.com'),
    'encoding': 'UTF-8',
    'service_levels': {
        'high': 'gb8f3e57eee6934_nh66vvfwukxku4dc_high.adb.oraclecloud.com',
        'medium': 'gb8f3e57eee6934_nh66vvfwukxku4dc_medium.adb.oraclecloud.com',
        'low': 'gb8f3e57eee6934_nh66vvfwukxku4dc_low.adb.oraclecloud.com',
        'tp': 'gb8f3e57eee6934_nh66vvfwukxku4dc_tp.adb.oraclecloud.com',
        'tpurgent': 'gb8f3e57eee6934_nh66vvfwukxku4dc_tpurgent.adb.oraclecloud.com'
    }
} 