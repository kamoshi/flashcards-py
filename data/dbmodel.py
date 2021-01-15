import sqlalchemy as sql
from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


Engine = sql.create_engine('sqlite:///appdata.db', echo=True)
Base = declarative_base()
Session = sessionmaker(bind=Engine)


class Card(Base):
    __tablename__ = 'cards'
    c_id = Column(Integer, primary_key=True)
    c_name = Column(String(20), nullable=False, unique=True)
    c_fields = Column(String(255), nullable=False)
    c_layout_f = Column(Text(1000))
    c_layout_b = Column(Text(1000))

    def __repr__(self):
        return f"<Card c_id:{self.c_id} c_name:{self.c_name}>"


class Deck(Base):
    __tablename__ = 'decks'
    d_id = Column(Integer, primary_key=True)
    d_name = Column(String(20), nullable=False, unique=True)
    c_id = Column(Integer, nullable=False)

    def __repr__(self):
        return f"<Deck d_id:{self.d_id} d_name:{self.d_name}>"


class Note(Base):
    __tablename__ = 'notes'
    n_id = Column(Integer, primary_key=True)
    n_data = Column(String(255), nullable=False)
    n_last_r = Column(Integer, nullable=False, default=0)
    n_next_r = Column(Integer, nullable=False, default=0)
    d_id = Column(Integer, nullable=False)

    def __repr__(self):
        return f"<Note n_id:{self.n_id}>"


class Review(Base):
    __tablename__ = 'reviews'
    r_id = Column(Integer, primary_key=True)
    r_ease = Column(Integer, nullable=False)
    n_id = Column(Integer, nullable=False)

    def __repr__(self):
        return f"<Review r_id:{self.r_id}>"


Base.metadata.create_all(Engine)
