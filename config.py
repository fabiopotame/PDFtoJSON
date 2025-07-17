import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Application settings
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 8085))
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
CORS_HEADERS = 'Content-Type'

# Oracle Autonomous Database configuration using wallet
ORACLE_WALLET_DIR = os.path.join(os.getcwd(), 'oracle')
ORACLE_CONFIG = {
    'user': os.getenv('ORACLE_USER', 'ADMIN'),
    'password': os.getenv('ORACLE_PASSWORD'),
    'dsn': os.getenv('ORACLE_DSN', 'nh66vvfwukxku4dc_high'),  # Using HIGH connection by default
    'wallet_dir': ORACLE_WALLET_DIR,
    'wallet_password': os.getenv('ORACLE_WALLET_PASSWORD'),
    'encoding': 'UTF-8',
    'service_levels': {
        'high': 'nh66vvfwukxku4dc_high',
        'medium': 'nh66vvfwukxku4dc_medium',
        'low': 'nh66vvfwukxku4dc_low',
        'tp': 'nh66vvfwukxku4dc_tp',
        'tpurgent': 'nh66vvfwukxku4dc_tpurgent'
    }
} 