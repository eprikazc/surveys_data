from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import sessionmaker, relationship

from config import config

engine = create_engine(config['DB']['connection_string'])

Base = declarative_base()
Base.metadata.bind = engine
Session = sessionmaker(bind=engine)


class Survey(Base):
    __tablename__ = 'zenloop_survey'
    id = Column(Integer, primary_key=True)
    public_hash_id = Column(String, unique=True)
    title = Column(String)
    status = Column(String)
    nps = Column(Integer)
    brand = Column(String)
    # TODO: add JSON field for raw response?


class Answer(Base):
    __tablename__ = 'zenloop_answer'
    id = Column(Integer, primary_key=True)
    survey_id = Column(Integer, ForeignKey('zenloop_survey.id'))
    recipient_id = Column(String)
    score = Column(Integer)
    comment = Column(String)
    inserted_at = Column(DateTime)
    inserted_at_str = Column(String)

    survey = relationship('Survey')
    # TODO: add JSON field for raw response?


if __name__ == '__main__':
    Base.metadata.create_all()
