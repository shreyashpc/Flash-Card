from flask import render_template
from flask import redirect, url_for
from flask import current_app as app
from flask import session
from flask import request
from datetime import datetime

from application.database import db
from application.models import Cards, Users, Decks
from application import tasks

from sqlalchemy import and_

app.secret_key = b'verySecureKey'


@app.route("/", methods=["GET"])
def home():
    return render_template("home.html")


@app.route("/sign-up", methods=["GET", "POST"])
def sign_up():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        r = requests.post('http://192.168.1.14:8080/api/user/', data={'username': username, 'password': password})
        return redirect(url_for('dashboard'))

    return render_template("signUp.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        if session.get('user_id') == True:
            return redirect(url_for('dashboard'))
        else:
            return render_template("login.html")

    elif request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        user_exists = db.session.query(Users).filter(and_(Users.username == username),
                                                     (Users.password == password)).first()
        if user_exists:
            user_id = Users.query.filter(Users.username == username).first().user_id
            session['user_id'] = user_id
            session['username'] = request.form['username']
            return redirect(url_for('dashboard'))
        else:
            return render_template("error.html", errorMessage="Username & Password combination is incorrect",
                                   goBack=url_for('login'))
    else:
        return render_template("error.html", errorMessage="Page does not exist.")


@app.route("/logout", methods=["GET", "POST"])
def logout():
    session.pop('username', None)
    session.pop('user_id', None)
    return redirect(url_for('login'))


@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if 'username' in session:
        user_id = session['user_id']
        username = session['username']
        decks = requests.get('http://192.168.1.14:8080/api/deck/', {"user_id": user_id}).json()
        # for deck in decks:
        #     deck_id = deck["deck_id"]
        # review = requests.get(url).json()
        # reviews.append(review)
        return render_template("dashboard.html", decks=decks, username=username)

    else:
        loginURL = url_for('login')
        return render_template("error.html", errorMessage="You are not logged in!", goBack=loginURL)


# ~ DECK MANAGEMENT

@app.route("/deck/add", methods=["GET", "POST"])
def add_deck():
    if request.method == "POST":
        response = request.form
        deck_name = response["deck_name"]
        user_id = session["user_id"]
        deck_list = db.session.query(Decks).filter(Decks.user_id == user_id).all()
        addDeckURL = url_for('add_deck')
        for deck in deck_list:
            if deck.deck_name == deck_name:
                return render_template("error.html", errorMessage="Deck name already used.", goBack=addDeckURL)
        # if response["question"] != " ":
        #     questions.append(response["question"])
        # else:
        #     return render_template("error.html", errorMessage="Question can not be empty", goBack=addDeckURL)
        # if response["answer"] != " ":
        #     answers.append(response["answer"])
        # else:
        #     return render_template("error.html", errorMessage="Answer Cannot be empty", goBack=addDeckURL)

        # - Add the deck
        r = requests.post("http://192.168.1.14:8080/api/deck/", data={'deck_name': deck_name, 'user_id': user_id})

        # - Add the cards. For this we need the deck_id.
        # deck = Decks.query.filter(and_(Decks.deck_name == deck_name), (Decks.user_id == user_id)).first()

        # r = requests.post("/api/card/", data={'questions': questions, 'answers': answers, 'deck_id': deck.deck_id})

        # url = "/api/review/{}".format(deck.deck_id)
        # x = datetime.datetime.now()
        # date = x.strftime("%x")
        # results = {
        #     "total_q": 0,
        #     "easy_q": 0,
        #     "medium_q": 0,
        #     "hard_q": 0,
        #     "score": 0,
        #     "last_reviewed": date,
        # }
        #
        # r = requests.post(url, json=results)
        return redirect(url_for('dashboard'))

    return render_template("addDeck.html")


@app.route("/deck/edit", methods=["GET", "PUT", "POST"])
def edit_deck():
    if request.method == "GET":
        deck_id = request.args.get('deck_id')
        deck = db.session.query(Decks).filter(Decks.deck_id == deck_id).first()
        return render_template("editDeck.html", deck=deck)
    if request.method == "POST":
        new_name = request.form['deck_name']
        deck_id = request.args.get('deck_id')
        r = requests.put("http://192.168.1.14:8080/api/deck/", data={'deck_id': deck_id, 'deck_name': new_name})
        return redirect(url_for("dashboard"))


@app.route("/deck/delete", methods=["GET", "POST", "DELETE", "OPTIONS"])
def delete():
    if request.method == "GET":
        deck_id = request.args.get('deck_id')
        card_id = request.args.get('card_id')
        if deck_id:
            deck = db.session.query(Decks).filter(Decks.deck_id == deck_id).first()
            return render_template("deleteDeck.html", deck=deck, card_id=None)
        if card_id:
            return render_template("deleteDeck.html", card_id=card_id, deck=None)
    if request.method == "POST":
        deck_id = request.args.get('deck_id')
        card_id = request.args.get('card_id')
        if deck_id:
            deck = db.session.query(Decks).filter(Decks.deck_id == deck_id).first()
            deck_name = deck.deck_name
            # 1. Delete all the cards related to that deck
            cards = db.session.query(Cards).filter(Cards.deck_id == deck_id).delete(synchronize_session=False)
            db.session.commit()


            # 2. Delete the deck
            url = "http://192.168.1.14:8080api/deck/{}".format(deck_id)
            r = requests.delete(url)
            return redirect(url_for('dashboard'))

        if card_id:
            cards = db.session.query(Cards).filter(Cards.card_id == card_id).delete(synchronize_session=False)
            db.session.commit()
            return redirect(url_for('dashboard'))


@app.route("/deck/cards", methods=["GET", "PUT", "POST", "DELETE", "OPTIONS"])
def edit_cards():
    if request.method == "GET":
        deck_id = request.args.get("deck_id")
        url = "http://192.168.1.14:8080/api/card/{}".format(deck_id)
        cards = requests.get(url).json()
        add_new_card = request.args.get('addCard')
        if add_new_card:
            return render_template("addCard.html", cards=cards, deck_id=deck_id, add_new_card=add_new_card)
        else:
            return render_template("addCard.html", cards=cards, deck_id=deck_id, add_new_card=add_new_card)

    elif request.method == "POST":
        deck_id = request.args.get("deck_id")
        add_new_card = request.form['submit']
        if add_new_card == "Add Card":
            question = request.form['question']
            answer = request.form['answer']
            r = requests.post("http://192.168.1.14:8080/api/card/",
                              data={'question': question, 'answer': answer, 'deck_id': deck_id})
            return redirect(url_for('edit_cards', deck_id=deck_id, addCard=True))
        else:
            question = request.form['question']
            answer = request.form['answer']
            card_id = request.form['submit']
            card = db.session.query(Cards).filter(Cards.card_id == card_id).first()
            r = requests.put("http://192.168.1.14:8080/api/card/",
                             data={'card_id': card_id, 'question': question, 'answer': answer})
            return redirect(url_for('edit_cards', deck_id=deck_id))


# ~ REVIEW and SCORING

@app.route("/view", methods=["GET", "PUT", "POST"])
def view():
    if request.method == "GET":
        deck_id = request.args.get("deck_id")
        url = "http://192.168.1.14:8080/api/card/{}".format(deck_id)
        deck = db.session.query(Decks).filter(Decks.deck_id == deck_id).first()
        cards = requests.get(url).json()
        return render_template("view.html", cards=cards, deck=deck)
    if request.method == "POST":
        deck_id = request.args.get("deck_id")
        card_id = request.form['submit']
        card = db.session.query(Cards).filter(Cards.card_id==card_id).first()
        card.revision = 1
        db.session.add(card)
        db.session.commit()
        return redirect(url_for('view', deck_id=deck_id))
    else:
        return ""
@app.route("/solution", methods=["GET", "PUT", "POST"])
def viewSolution():
    if request.method == "GET":
        deck_id = request.args.get("deck_id")
        url = "http://192.168.1.14:8080/api/card/{}".format(deck_id)
        deck = db.session.query(Decks).filter(Decks.deck_id == deck_id).first()
        cards = requests.get(url).json()
        return render_template("solution.html", cards=cards, deck=deck)
    if request.method == "POST":
        deck_id = request.args.get("deck_id")
        card_id = request.form['submit']
        card = db.session.query(Cards).filter(Cards.card_id==card_id).first()
        card.revision = 1
        db.session.add(card)
        db.session.commit()
        return redirect(url_for('viewSolution', deck_id=deck_id))

@app.route("/revision", methods=["GET", "PUT", "POST"])
def viewRevision():
    if request.method == "GET":
        cards = db.session.query(Cards).filter(Cards.revision == 1).all()
        return render_template('revision.html',cards=cards)
    if request.method == "POST":
        deck_id = request.args.get("deck_id")
        card_id = request.form['submit']
        card = db.session.query(Cards).filter(Cards.card_id==card_id).first()
        card.revision = 0
        db.session.add(card)
        db.session.commit()
        return redirect(url_for('viewRevision', deck_id=deck_id))

@app.route("/revision/delete", methods=["GET", "PUT", "POST"])
def deleteRevision():
    if request.method == "GET":
        cards = db.session.query(Cards).filter(Cards.revision == 1).update({Cards.revision:0},synchronize_session = False)
        db.session.commit()
        return redirect(url_for('dashboard'))
    if request.method == "POST":
        return redirect(url_for('dashboard'))


#Celery Endpoints

@app.route("/hello/<user_name>", methods=["GET", "POST"])
def hello(user_name):
    job=tasks.just_say_hello.delay(user_name)
    result = job.wait()
    return str(result), 200 
    
@app.route("/datetime", methods=["GET", "POST"])
def datet():
    now=datetime.now()
    print("now in FLask", now)
    dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
    print("date and time =", dt_string)
    
    job = tasks.print_current_time_job.apply_async(countdown=10)
    result = job.wait()
    return str(result), 200