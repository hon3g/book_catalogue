DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS book_list;

CREATE TABLE user (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(50) NOT NULL
);

CREATE TABLE book_list (
    book_id INTEGER PRIMARY KEY AUTOINCREMENT,
    thumbnail TEXT,
    title VARCHAR(500) UNIQUE NOT NULL,
    author VARCHAR(250),
    page_count SMALLINT,
    rating VARCHAR(50),
    user_id INTEGER REFERENCES user(user_id)
);

INSERT INTO user (username, password) VALUES ('user', 'pass');