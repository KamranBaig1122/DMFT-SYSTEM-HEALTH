import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('config.env')

a_email = os.getenv('ADMIN_EMAIL', 'admin@dmft.com')
a_pass = os.getenv('ADMIN_PASSWORD', 'admin123')
