import sys
import os
import logging

# Create logs directory if it doesn't exist
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
os.makedirs(log_dir, exist_ok=True)

# Configure logging to file
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename=os.path.join(log_dir, 'app.log'),
    filemode='a'
)

# Also log to stderr for Apache
console = logging.StreamHandler(sys.stderr)
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)

logger = logging.getLogger(__name__)

# Add the project directory to Python path
project_home = os.path.dirname(os.path.abspath(__file__))
if project_home not in sys.path:
    sys.path.insert(0, project_home)

logger.info(f"Python version: {sys.version}")
logger.info(f"Python path: {sys.path}")
logger.info(f"Working directory: {os.getcwd()}")

try:
    from app import app
    application = app  # Expose as both 'app' and 'application'
    logger.info("Successfully imported Flask application")
except Exception as e:
    logger.error(f"Error importing Flask application: {str(e)}")
    raise

# Ensure the upload folder exists
try:
    os.makedirs(os.path.join(project_home, 'uploads'), exist_ok=True)
    logging.info("Uploads directory verified/created")
except Exception as e:
    logging.error(f"Error creating uploads directory: {str(e)}")

if __name__ == "__main__":
    application.run()
