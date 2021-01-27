import sqlalchemy as sql
from sqlalchemy import Column, Integer, String, Text, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


Engine = sql.create_engine('sqlite:///appdata.db', echo=True)
Base = declarative_base()
Session = sessionmaker(bind=Engine)


class Card(Base):
    """
    Class maps the cards table in database to an object
    c_id        - ID of the card
    c_name      - name of the card
    c_fields    - name of the fields on a card
    c_layout_f  - front layout of the card
    c_layout_b  - back layout of the card
    """
    __tablename__ = 'cards'
    c_id = Column(Integer, primary_key=True)
    c_name = Column(String(20), nullable=False, unique=True)
    c_fields = Column(String(255), nullable=False)
    c_layout_f = Column(Text(1000))
    c_layout_b = Column(Text(1000))

    __table_args__ = (
        Index("ix_c_name", "c_name"),
    )

    def __repr__(self):
        return f"<Card c_id:{self.c_id} c_name:{self.c_name}>"


class Deck(Base):
    """
    Class maps the decks table in database to an object
    d_id        - ID of teh deck
    d_name      - name of the deck
    c_id        - ID of the card used by deck
    """
    __tablename__ = 'decks'
    d_id = Column(Integer, primary_key=True)
    d_name = Column(String(20), nullable=False, unique=True)
    c_id = Column(Integer, nullable=False)

    __table_args__ = (
        Index("ix_d_name", "d_name"),
    )

    def __repr__(self):
        return f"<Deck d_id:{self.d_id} d_name:{self.d_name}>"


class Note(Base):
    """
    Class maps the notes table in database to an object
    n_id        - ID of the note
    n_data      - filled fields in the note
    n_last_r    - time of the last review of the note
    n_next_r    - time of the next review
    d_id        - ID of the deck used by this note
    """
    __tablename__ = 'notes'
    n_id = Column(Integer, primary_key=True)
    n_data = Column(String(255), nullable=False)
    n_last_r = Column(Integer, nullable=False, default=0)
    n_next_r = Column(Integer, nullable=False, default=0)
    d_id = Column(Integer, nullable=False)

    def __repr__(self):
        return f"<Note n_id:{self.n_id}>"


class Review(Base):
    """
    Class maps the reviews table in database to an object
    r_id        - ID of the review
    r_ease      - review rating
    n_id        - ID of the note to which the review belongs
    """
    __tablename__ = 'reviews'
    r_id = Column(Integer, primary_key=True)
    r_ease = Column(Integer, nullable=False)
    n_id = Column(Integer, nullable=False)

    def __repr__(self):
        return f"<Review r_id:{self.r_id}>"


Base.metadata.create_all(Engine)
