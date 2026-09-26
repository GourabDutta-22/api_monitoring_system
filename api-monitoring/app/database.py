import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

import models
from models import Base

load_dotenv()

# Database connection
# Keep your actual password locally; don't share it publicly.
DATABASE_URL = os.getenv("DATABASE_URL")

# SQLAlchemy Engine
engine = create_engine(DATABASE_URL)

# Test database connection
with engine.connect() as connection:
    result = connection.execute(text("SELECT 1"))
    print("Database connected:", result.fetchone())

# Create tables registered in SQLAlchemy metadata
Base.metadata.create_all(engine)

# Session factory
SessionLocal = sessionmaker(bind=engine)