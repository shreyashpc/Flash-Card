# database models/table definitions
from .database import db


class Users(db.Model):
    __tablename__ = 'users'
    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)


class Decks(db.Model):
    __tablename__ = 'decks'
    deck_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    deck_name = db.Column(db.String(50), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)


class Cards(db.Model):
    __tablename__ = 'cards'
    card_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    deck_id = db.Column(db.Integer, db.ForeignKey("decks.deck_id"), nullable=False)
    question = db.Column(db.String(50), unique=True, nullable=False)
    answer = db.Column(db.String(50), nullable=False)
    revision = db.Column(db.Integer)

