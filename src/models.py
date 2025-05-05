from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.orm import declarative_base, sessionmaker
import os
import re
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('models') # Get logger instance named 'models'

# Determine database URL based on environment
database_url = os.environ.get('DATABASE_URL')

if database_url:
    # If DATABASE_URL is set, assume it's for PostgreSQL and ensure correct prefix
    logger.info("Found DATABASE_URL environment variable.")

    # Mask the password for printing
    masked_url = re.sub(r':(?:[^@/]+)@', r':[PASSWORD]@', database_url)
    logger.info(f"Connecting using URL: {masked_url}")

    # If DATABASE_URL is set, assume it's for PostgreSQL and ensure correct prefix
    if database_url.startswith("postgres://"):
        # SQLAlchemy 1.4+ requires 'postgresql://' scheme
        database_url = database_url.replace("postgres://", "postgresql://", 1)
        logger.info("Adjusted URL prefix for SQLAlchemy.")
    if not database_url.startswith("postgresql://"):
        logger.warning("DATABASE_URL does not start with postgresql:// scheme. Using it as is.")
else:
    # Default to local SQLite database if DATABASE_URL is not set
    logger.info("DATABASE_URL not set, using local SQLite: sqlite:///words.db")
    database_url = 'sqlite:///words.db'

# Create engine using the determined URL
logger.info("Initializing database engine...")
engine = create_engine(database_url)
Session = sessionmaker(bind=engine)
Base = declarative_base() 

class ForeignWord(Base):
    __tablename__ = 'foreign_words'
    id = Column(Integer, primary_key=True)
    word = Column(String(255), nullable=False)
    meaning = Column(Text)
    context = Column(Text)
    word_type = Column(String(255))
    language = Column(String(50), nullable=False)
    example = Column(Text)

Base.metadata.create_all(engine)
