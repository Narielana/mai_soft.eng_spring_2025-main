from sqlalchemy import Column, Integer, String, Text

from database.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(Text, nullable=False)
    name = Column(String, index=True)
    surname = Column(String, index=True)
    age = Column(Integer, nullable=True)
