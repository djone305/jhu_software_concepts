import os
import datetime
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import String, Float, Integer, Text, Date, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

# Locate and load the .env file in the current directory
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

# Retrieve connection credentials from environment
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_NAME = os.environ.get("DB_NAME", "grad_admissions")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASSWORD = os.environ.get("DB_PASSWORD")

if not DB_PASSWORD:
    raise ValueError(
        f"Missing database password! Verify that {env_path} exists and defines DB_PASSWORD."
    )

# Dynamically construct the SQLAlchemy Database URL
DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Setup Engine and Session Factory
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


class Applicant(Base):
    __tablename__ = "applicants"

    p_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    program: Mapped[str | None] = mapped_column(Text, nullable=True)
    comments: Mapped[str | None] = mapped_column(Text, nullable=True)
    date_added: Mapped[datetime.date | None] = mapped_column(Date, nullable=True)
    url: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str | None] = mapped_column(String, nullable=True)
    term: Mapped[str | None] = mapped_column(String, nullable=True)
    us_or_international: Mapped[str | None] = mapped_column(String, nullable=True)
    gpa: Mapped[float | None] = mapped_column(Float, nullable=True)
    gre: Mapped[float | None] = mapped_column(Float, nullable=True)
    gre_v: Mapped[float | None] = mapped_column(Float, nullable=True)
    gre_aw: Mapped[float | None] = mapped_column(Float, nullable=True)
    degree: Mapped[str | None] = mapped_column(String, nullable=True)
    llm_generated_program: Mapped[str | None] = mapped_column(Text, nullable=True)
    llm_generated_university: Mapped[str | None] = mapped_column(Text, nullable=True)