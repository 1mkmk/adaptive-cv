"""
Script to add the ai_summary column to the jobs table.
"""
import os
import sys
import logging
from sqlalchemy import text

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

try:
    # Import database components
    from app.database import engine
    
    logger.info("Adding ai_summary column to jobs table")
    
    # Execute ALTER TABLE command
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE jobs ADD COLUMN ai_summary TEXT"))
            conn.commit()
            logger.info("Successfully added ai_summary column to jobs table")
        except Exception as e:
            logger.error(f"Error adding column: {e}")
            logger.info("Column may already exist or there was another issue")
    
except Exception as e:
    logger.error(f"Error in migration script: {e}")

logger.info("Migration complete")