from flask import request
from flask_restful import Resource
from flask_restful import fields, marshal_with
from flask_restful import reqparse
from application.database import db
from application.models import Decks, Users, Cards
from flask_security.utils import encrypt_password
from application.validation import BusinessValidationError

# -----------------Parsers----------------------

create_user_parser = reqparse.RequestParser()
create_user_parser.add_argument('username')
create_user_parser.add_argument('password')

create_deck_parser = reqparse.RequestParser()
create_deck_parser.add_argument('deck_name')
create_deck_parser.add_argument('user_id')
#
get_deck_parser = reqparse.RequestParser()
get_deck_parser.add_argument('user_id')
#
put_deck_parser = reqparse.RequestParser()
put_deck_parser.add_argument('deck_id')
put_deck_parser.add_argument('deck_name')
#
create_card_parser = reqparse.RequestParser()
create_card_parser.add_argument('question', action='append')
create_card_parser.add_argument('answer', action='append')
create_card_parser.add_argument('deck_id')
#
get_card_parser = reqparse.RequestParser()
get_card_parser.add_argument('deck_id')
#
put_card_parser = reqparse.RequestParser()
put_card_parser.add_argument('card_id')
put_card_parser.add_argument('question')
put_card_parser.add_argument('answer')

# -------Output Fields-----------------

deck_output_fields = {
    "deck_id": fields.Integer,
    "deck_name": fields.String
}

card_output_fields = {
    "card_id": fields.Integer,
    "deck_id": fields.Integer,
    "question": fields.String,
    "answer": fields.String,
    "revision": fields.Integer
}



# ----------------- User -----------------


class UserAPI(Resource):
    def get(self):
        pass

    def post(self):
        args = create_user_parser.parse_args()
        username = args.get("username", None)
        password = args.get("password", None)
        if username is None:
            raise BusinessValidationError(status_code=400, error_code="U1001", error_message="Username is required")
        if password is None:
            raise BusinessValidationError(status_code=400, error_code="U1002", error_message="Password is required")

        user = db.session.query(Users).filter(Users.username == username).first()
        # print(user)
        if user:
            raise BusinessValidationError(status_code=400, error_code="U1003",error_message="Duplicate user")

        new_user = Users(username=username, password=encrypt_password(password))
        db.session.add(new_user)
        db.session.commit()
        return "New User Created"

# -------------------- Deck API -------------------------

class DeckAPI(Resource):
    @marshal_with(deck_output_fields)
    def get(self):
        args = get_deck_parser.parse_args()
        user_id = args.get("user_id", None)
        deck = db.session.query(Decks).filter(Decks.user_id == user_id).all()
        return deck

    def put(self):
        args = put_deck_parser.parse_args()
        deck_id = args.get('deck_id', None)
        new_name = args.get('deck_name', None)
        if deck_id is None:
            raise BusinessValidationError(status_code=400, error_code="D1001", error_message="Deck Id is required")
        deck = db.session.query(Decks).filter(Decks.deck_id == deck_id).first()
        deck.deck_name = new_name
        db.session.add(deck)
        db.session.commit()
        return "", 200

    def post(self):
        args = create_deck_parser.parse_args()
        deck_name = args.get("deck_name", None)
        user_id = args.get("user_id", None)
        if deck_name is None:
            raise BusinessValidationError(status_code=400, error_code="D1002", error_message="Deck name is required")
        if user_id is None:
            raise BusinessValidationError(status_code=400, error_code="D1003", error_message="User id is required")
        new_deck = Decks(deck_name=deck_name, user_id=user_id)
        db.session.add(new_deck)
        db.session.commit()
        return "", 201

    def delete(self, deck_id):
        deck = db.session.query(Decks).filter(Decks.deck_id == deck_id).delete(synchronize_session=False)
        db.session.commit()
        return "", 204


# ---------------Card API-------------


class CardAPI(Resource):
    @marshal_with(card_output_fields)
    def get(self, deck_id):
        cards = db.session.query(Cards).filter(Cards.deck_id == deck_id).all()
        return cards

    def post(self):
        args = create_card_parser.parse_args()
        questions = args['question']
        answers = args['answer']
        deck_id = args.get("deck_id", None)

        if questions is None:
            raise BusinessValidationError(status_code=400,error_code="C1001", error_message="Questions are required")
        if answers is None:
            raise BusinessValidationError(status_code=400, error_code="C1002", error_message="Answers are required")

        for i in range(0, len(questions)):
            new_card = Cards(question=questions[i], answer=answers[i], deck_id=deck_id)
            db.session.add(new_card)
            db.session.commit()

        return "", 201

    def put(self):
        args = put_card_parser.parse_args()
        card_id = args.get('card_id', None)
        new_question = args.get('question', None)
        new_answer = args.get('answer', None)

        card = db.session.query(Cards).filter(Cards.card_id == card_id).first()
        card.question = new_question
        card.answer = new_answer
        db.session.add(card)
        db.session.commit()
        return "", 200

    def delete(self, card_id):
        card = db.session.query(Cards).filter(Cards.card_id == card_id).delete(synchronize_session=False)
        db.session.commit()
        return "", 204
