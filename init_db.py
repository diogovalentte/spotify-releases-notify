from src.db import create_db
from src.utils import get_logger

if __name__ == "__main__":
    logger = get_logger()
    logger.info("Creating database if not exist...")
    create_db()
    logger.info("Database created!")
