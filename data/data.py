from sqlmodel import Session,SQLModel,create_engine
from config.config import settings
import models
engine=create_engine(settings.database_url,echo=True)

def get_session():
    with Session(engine) as session:
        yield session
        
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
    