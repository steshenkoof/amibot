import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bot configuration
BOT_TOKEN = '7861528513:AAGdOVksUiAERz8jcE0QxTbmYQQyAfwdMUY'

# Admin user IDs - только @mansklav
ADMIN_IDS = [5168428653]  # @mansklav

# PostgreSQL Database configuration
POSTGRES_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'port': int(os.getenv('POSTGRES_PORT', 5432)),
    'user': os.getenv('POSTGRES_USER', 'postgres'),
    'password': os.getenv('POSTGRES_PASSWORD', '0665191213'),
    'database': os.getenv('POSTGRES_DATABASE', 'amichaisebase'),
}

# Database URL for direct connection
DATABASE_URL = f"postgresql://{POSTGRES_CONFIG['user']}:{POSTGRES_CONFIG['password']}@{POSTGRES_CONFIG['host']}:{POSTGRES_CONFIG['port']}/{POSTGRES_CONFIG['database']}"

# Work location settings
WORK_LOCATION = {
    'latitude': 50.4501,  # Replace with actual work location
    'longitude': 30.5234,  # Replace with actual work location
    'radius': 100  # meters - allowed distance from work location
}

# Office location settings (example coordinates - Moscow Red Square)
OFFICE_LATITUDE = float(os.getenv('OFFICE_LATITUDE', '55.7539'))
OFFICE_LONGITUDE = float(os.getenv('OFFICE_LONGITUDE', '37.6208'))
OFFICE_RADIUS = int(os.getenv('OFFICE_RADIUS', '100'))  # meters

# Timezone
TIMEZONE = os.getenv('TIMEZONE', 'Europe/Moscow') 