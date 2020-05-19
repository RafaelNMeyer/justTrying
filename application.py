import os
import requests

from flask import Flask, session, render_template, request, flash, redirect, url_for, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from flask_json import FlaskJSON, JsonError, json_response, as_json

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)
session

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

@app.route("/")
def index():
    session["logged"] = False
    return render_template("index.html")

# user login    
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    session["logged"] = False
    email_username = request.form.get("email_username")
    password = request.form.get("password") 

    if email_username == "" or password=="":
        flash("Please, complete the form")
        return render_template("login.html")
    else:              
        users = db.execute("SELECT * FROM users").fetchall()

        for user in users:
            if (email_username == user.username or email_username == user.email) and password == user.password:
                session["logged"] = user
                return redirect(url_for('bookreview'))
        flash("Username or password incorrect")
        return render_template("login.html")  

#user register
@app.route("/register", methods=["GET", "POST"])
def register():    

    if request.method == "GET":
        return render_template("register.html")
    session["logged"] = False
    email = request.form.get("email")
    username = request.form.get("username")
    password = request.form.get("password")    
    passAgain = request.form.get("pass-again")

    if email == "" or username == "" or password == "":
        flash("Please, complete the form")
        return render_template("register.html", email_value=email, username_value=username)
    if password != passAgain:
        flash("Passwords doesn't match")
        flash(password)
        flash(passAgain)
        return render_template("register.html", email_value=email, username_value=username)
    else:
        # verify if already exist
        users = db.execute("SELECT email, username FROM users").fetchall()
        for user in users:
            if email == user.email:
                flash("This email already exists")
                return render_template("register.html", email_value=email, username_value=username)
            if username == user.username:
                flash("This username already exists")
                return render_template("register.html", email_value=email, username_value=username)
        db.execute("INSERT INTO users (email, username, password) VALUES (:email, :username, :password)", {"email": email, "username": username, "password": password}) 
        db.commit()
        flash("Register complete!")
        return render_template("login.html") 



@app.route("/bookreview", methods=["GET", "POST"])
def bookreview():
    if not session.get("logged"):
        flash("Please, login")
        return redirect(url_for('index'))
    search = request.form.get("search")
    radio_search = request.form.get("radio_search")
    all_checked = None
    isbn_checked = None
    title_checked = None
    author_checked = None
    year_checked = None
    # search for books
    if search == "" or search == None:
        books = ""
        search = ""
        all_checked = "checked"
    else:
        if radio_search == "all":
            books = db.execute("SELECT * FROM books WHERE (LOWER(title) LIKE :search) or (LOWER(isbn) LIKE :search) or (LOWER(author) LIKE :search) or (LOWER(year) LIKE :search)", {"search": "%"+search.lower()+"%"}).fetchall()
            all_checked = "checked"

        if radio_search == "isbn":
            books = db.execute("SELECT * FROM books WHERE isbn LIKE :search", {"radio_search": radio_search, "search": "%"+search.lower()+"%"}).fetchall()
            isbn_checked = "checked"

        if radio_search == "title":
            books = db.execute("SELECT * FROM books WHERE LOWER(title) LIKE :search", {"radio_search": radio_search, "search": "%"+search.lower()+"%"}).fetchall()
            title_checked = "checked"

        if radio_search == "author":
            books = db.execute("SELECT * FROM books WHERE LOWER(author) LIKE :search", {"radio_search": radio_search, "search": "%"+search.lower()+"%"}).fetchall()
            author_checked = "checked"

        if radio_search == "year":
            books = db.execute("SELECT * FROM books WHERE year LIKE :search", {"radio_search": radio_search, "search": "%"+search.lower()+"%"}).fetchall()
            year_checked = "checked"

        if not books:
            flash("No books found.")
        else:
            flash(search)
    qtd = 0
    for book in books:
        qtd+=1
    return render_template("bookreview.html", username=session.get("logged").username, books=books, qtd=qtd, all=all_checked, isbn=isbn_checked, title=title_checked, author=author_checked, year=year_checked, inside_search=search)

@app.route("/bookreview/<book_isbn>", methods=["GET", "POST"])
def book(book_isbn):
    if not session.get("logged"):
        flash("Please, login")
        return redirect(url_for('login'))
    book = db.execute("SELECT * FROM books where isbn = :book_isbn", {"book_isbn": book_isbn}).fetchall()
    users = db.execute("SELECT * FROM users").fetchall()
    user_reviews = db.execute("SELECT * FROM reviews where user_id = :user_id", {"user_id": session["logged"].id}).fetchall()
    review = request.form.get("review")
    rate = request.form.get("radio_rate")

    book_reviewed = False
    if request.method == "POST":
        for user_review in user_reviews:
            if user_review.book_id == book_isbn:
                book_reviewed = True
                flash("You've already done a review")
        if book_reviewed == False:
            review = request.form.get("review")
            radio_rate = request.form.get("radio_rate")
            if review == "" or review == None:
                flash("Please, write a comment")
                return redirect(url_for('book', book_isbn=book_isbn))
            if radio_rate == "" or radio_rate == None:
                flash("Please, rate this book instead")
                return redirect(url_for('book', book_isbn=book_isbn))
            db.execute("INSERT INTO reviews (review, book_id, user_id, rate) VALUES (:review, :book_id, :user_id, :rate)", {"review": review, "book_id": 
            book_isbn, "user_id": session.get("logged").id, "rate": int(radio_rate)})
            db.commit()
    reviews = db.execute("SELECT * FROM reviews INNER JOIN users ON reviews.user_id=users.id WHERE book_id = :book_isbn", {"book_isbn": book_isbn}).fetchall()

    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "gkaUL2egpnCfAXrp044dBg", "isbns": book_isbn})
    data = res.json()
   

    # res_img = requests.get("https://www.googleapis.com/books/v1/volumes/zyTCAlFPjgYC?key=AIzaSyD4-GFGwnOUtKbVQghqYRcahnZ4QTWtrNA", {"ISBN_13": data["books"][0]["isbn13"]})
    # data_img = res_img.json()
    # flash(data_img)

    rate_count = data["books"][0]["work_ratings_count"]
    rate_average = data["books"][0]["average_rating"]
    
    return render_template("book.html", book=book, users=users, reviews=reviews, rate_count=rate_count,rate_average=rate_average)


@app.route("/api/<isbn>")
def api(isbn):
    book = db.execute("SELECT * from books WHERE isbn = :isbn", {"isbn": isbn}).fetchall()
    if not book:
        return jsonify({"error": "Invalid isbn"}), 404
    
    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "gkaUL2egpnCfAXrp044dBg", "isbns": isbn})
    data = res.json()
    rate_count = data["books"][0]["work_ratings_count"]
    rate_average = data["books"][0]["average_rating"]
    for book in book:
        return jsonify({
                    "title": book.title,
                    "author": book.author,
                    "year": book.year,
                    "isbn": book.isbn,
                    "review_count": rate_count,
                    "average_score": rate_average
                })