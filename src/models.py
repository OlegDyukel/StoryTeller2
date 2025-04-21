from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.orm import declarative_base, sessionmaker

engine = create_engine('sqlite:///words.db')
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
