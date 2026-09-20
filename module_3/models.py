from sqlalchemy import String, Float, Integer, Text, Date, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
import datetime

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

# Point to the 'grad_admissions' database where load_data.py stores the data
DATABASE_URL = "postgresql://postgres:Python2026$@localhost:5432/grad_admissions"

engine = create_engine(DATABASE_URL)

# Session factory interacting with the exact same database and table as load_data.py
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)