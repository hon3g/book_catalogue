from flask import Flask, request, session, redirect, render_template, url_for, g, flash
import sqlite3
import json
from urllib.request import urlopen
import ssl

ssl._create_default_https_context = ssl._create_unverified_context

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev'

book_info = None


def init_db():
    con = sqlite3.connect("app.db")
    con.cursor().executescript(open("schema.sql").read())


def connect_db():
    db = sqlite3.connect("app.db")
    db.row_factory = sqlite3.Row
    return db


@app.teardown_appcontext
def close_db(Exception):
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()


@app.before_request
def before_request():
    g.db = connect_db()


@app.route('/')
def index():
    if 'user' in session:
        return redirect('/book_list')
    else:
        return redirect('/login')


@app.route('/login', methods=['GET', 'POST'])
def login():
    session.pop('_flashes', None)

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cur = g.db.execute("SELECT * FROM user")
        res = cur.fetchall()

        usernames = set(r[1] for r in res)
        passwords = set(r[2] for r in res)

        if username in usernames and password in passwords:
            session['user'] = request.form['username']
            return redirect('/book_list')
        else:
            flash('The username or password is incorrect')
            return render_template('login.html')
    else:
        return render_template('login.html')


@app.route('/book_list', methods=['GET', 'POST'])
def book_list():
    session.pop('_flashes', None)
    global book_info

    if request.method == 'POST':
        api = 'https://www.googleapis.com/books/v1/volumes?q=isbn:'
        isbn = max(request.form['ISBN'], '0')
        resp = urlopen(api + isbn)
        book_data = json.load(resp)

        if book_data['totalItems'] != 0:
            try:
                image = book_data['items'][0]['volumeInfo']['imageLinks']['smallThumbnail']
                title = book_data['items'][0]['volumeInfo']['title']
                authors = '/'.join(a for a in book_data['items'][0]['volumeInfo']['authors'])
                page_count = book_data['items'][0]['volumeInfo']['pageCount']
                rating = book_data['items'][0]['volumeInfo']['maturityRating']

                book_info = image, title, authors, page_count, rating, 1
            except KeyError:
                pass
        else:
            book_info = None
            flash('There is no result that matched your search')

    if 'user' in session:
        books = get_books()
        return render_template('/book_list.html',
                               book_info=book_info,
                               books=books)
    else:
        return redirect('/login')


def get_books():
    res = g.db.execute("""SELECT * FROM book_list""").fetchall()
    books= []
    for r in res:
        books.append(dict(
            image = r[1],
            title = r[2],
            authors = r[3],
            page_count = r[4],
            rating = r[5]))
    return books


@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/login')


@app.route('/delete_book', methods=['GET', 'POST'])
def delete_book():
    g.db.execute(f"DELETE FROM book_list WHERE title='{request.form['d_book']}'")
    g.db.commit()
    return redirect('/book_list')


@app.route('/save_book')
def save_book():
    titles = set(b['title'] for b in get_books())
    global book_info
    if book_info[1] not in titles:
        g.db.execute("""
        INSERT INTO book_list
        (thumbnail, title, author, page_count, rating, user_id)
        VALUES(?,?,?,?,?,?)""", book_info)
        g.db.commit()
    book_info = None
    return redirect('/book_list')


if __name__ == '__main__':
    init_db()
    app.run(debug=True)
