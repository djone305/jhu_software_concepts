from sqlalchemy import String, Float, Integer, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

# ==========================================
# Database Connection Configuration
# ==========================================
# Update this connection string with your actual PostgreSQL credentials and database name.
# Format: postgresql+psycopg2://username:password@host:port/database_name
DATABASE_URL = "postgresql+psycopg2://postgres:your_password@localhost:5432/your_database_name"

# Create the SQLAlchemy engine
engine = create_engine(DATABASE_URL, echo=False)

# Create a configured "Session" class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ==========================================
# Declarative Base
# ==========================================
class Base(DeclarativeBase):
    pass

# ==========================================
# Applicant Model Definition
# ==========================================
class Applicant(Base):
    __tablename__ = "applicants"

    # Primary Key
    p_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Application Metadata & Details
    term: Mapped[str | None] = mapped_column(String, nullable=True)
    us_or_international: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str | None] = mapped_column(String, nullable=True)
    degree: Mapped[str | None] = mapped_column(String, nullable=True)
    
    # Academic Metrics
    gpa: Mapped[float | None] = mapped_column(Float, nullable=True)
    gre: Mapped[float | None] = mapped_column(Float, nullable=True)       # GRE Quantitative
    gre_v: Mapped[float | None] = mapped_column(Float, nullable=True)     # GRE Verbal
    gre_aw: Mapped[float | None] = mapped_column(Float, nullable=True)    # GRE Analytical Writing
    
    # Program and Institution Details
    program: Mapped[str | None] = mapped_column(Text, nullable=True)
    llm_generated_university: Mapped[str | None] = mapped_column(Text, nullable=True)
    llm_generated_program: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<Applicant(p_id={self.p_id}, term='{self.term}', status='{self.status}')>"