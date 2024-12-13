# Libraries
import os

# Modules
from sqlmodel import SQLModel, create_engine
from datetime import datetime
from db.models import DimDate, DimStation, DimProduct, DimMoment, FactData
from utils.logger_config import setup_logger
from dotenv import load_dotenv

# Loading env vars
load_dotenv()
database_url = os.getenv("DATABASE_URL")

# Logger configuration for this script
log_path = "logs/database_creation.log"
logger = setup_logger("database_creation", log_path)


# Engine configuration
engine = create_engine(database_url, echo=True)


# Function to database
def create_database():
    SQLModel.metadata.create_all(engine)


# Creating database
try:
    create_database()
    logger.info("Database created successfully")
except Exception as e:
    logger.error(f"Error during database creation: {e}")
