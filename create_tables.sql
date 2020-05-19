CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR NOT NULL,
    username VARCHAR NOT NULL,
    pass VARCHAR NOT NULL
);

CREATE TABLE books (
    isbn VARCHAR NOT NULL,
    title VARCHAR NOT NULL,
    author VARCHAR NOT NULL,
    year VARCHAR NOT NULL
);

CREATE TABLE reviews (
    review VARCHAR NOT NULL,
    book_id VARCHAR NULL,
    user_id INT NOT NULL,
    rate INT NOT NULL
);