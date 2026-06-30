from sqlalchemy import Column, Integer, String, Text
from database import Base


class Blog(Base):
    __tablename__ = "blogs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    content = Column(Text)


# FIX: auth.py references a "User" model (db.query(User)...) but it was
# never defined anywhere. Added it here alongside Blog so both tables
# get created by model.Base.metadata.create_all() in main.py.
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
