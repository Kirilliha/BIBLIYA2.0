from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

DATABASE = 'library.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Таблица книг
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            isbn TEXT UNIQUE,
            publisher TEXT,
            year INTEGER,
            category TEXT,
            quantity INTEGER DEFAULT 1,
            available INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Таблица читателей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS readers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE,
            phone TEXT,
            address TEXT,
            registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Таблица выдачи книг
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS loans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id INTEGER NOT NULL,
            reader_id INTEGER NOT NULL,
            loan_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            return_date TIMESTAMP,
            status TEXT DEFAULT 'active',
            FOREIGN KEY (book_id) REFERENCES books (id),
            FOREIGN KEY (reader_id) REFERENCES readers (id)
        )
    ''')

    conn.commit()
    conn.close()

@app.route('/')
def index():
    conn = get_db_connection()

    total_books = conn.execute('SELECT COUNT(*) as count FROM books').fetchone()['count']
    total_readers = conn.execute('SELECT COUNT(*) as count FROM readers').fetchone()['count']
    active_loans = conn.execute('SELECT COUNT(*) as count FROM loans WHERE status = "active"').fetchone()['count']

    recent_books = conn.execute('SELECT * FROM books ORDER BY created_at DESC LIMIT 5').fetchall()

    conn.close()

    return render_template('index.html',
                         total_books=total_books,
                         total_readers=total_readers,
                         active_loans=active_loans,
                         recent_books=recent_books)

@app.route('/books')
def books():
    conn = get_db_connection()
    search = request.args.get('search', '')
    category = request.args.get('category', '')

    query = 'SELECT * FROM books WHERE 1=1'
    params = []

    if search:
        query += ' AND (title LIKE ? OR author LIKE ? OR isbn LIKE ?)'
        params.extend([f'%{search}%', f'%{search}%', f'%{search}%'])

    if category:
        query += ' AND category = ?'
        params.append(category)

    query += ' ORDER BY title'

    books = conn.execute(query, params).fetchall()
    categories = conn.execute('SELECT DISTINCT category FROM books WHERE category IS NOT NULL').fetchall()

    conn.close()

    return render_template('books.html', books=books, categories=categories, search=search, selected_category=category)

@app.route('/books/add', methods=['GET', 'POST'])
def add_book():
    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        isbn = request.form['isbn']
        publisher = request.form['publisher']
        year = request.form['year']
        category = request.form['category']
        quantity = request.form['quantity']

        conn = get_db_connection()
        try:
            conn.execute('''
                INSERT INTO books (title, author, isbn, publisher, year, category, quantity, available)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (title, author, isbn, publisher, year, category, quantity, quantity))
            conn.commit()
            flash('Книга успешно добавлена!', 'success')
            return redirect(url_for('books'))
        except sqlite3.IntegrityError:
            flash('Книга с таким ISBN уже существует!', 'error')
        finally:
            conn.close()

    return render_template('add_book.html')

@app.route('/books/edit/<int:id>', methods=['GET', 'POST'])
def edit_book(id):
    conn = get_db_connection()

    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        isbn = request.form['isbn']
        publisher = request.form['publisher']
        year = request.form['year']
        category = request.form['category']
        quantity = request.form['quantity']

        try:
            conn.execute('''
                UPDATE books
                SET title=?, author=?, isbn=?, publisher=?, year=?, category=?, quantity=?
                WHERE id=?
            ''', (title, author, isbn, publisher, year, category, quantity, id))
            conn.commit()
            flash('Книга успешно обновлена!', 'success')
            return redirect(url_for('books'))
        except sqlite3.IntegrityError:
            flash('Книга с таким ISBN уже существует!', 'error')
        finally:
            conn.close()

    book = conn.execute('SELECT * FROM books WHERE id = ?', (id,)).fetchone()
    conn.close()

    return render_template('edit_book.html', book=book)

@app.route('/books/delete/<int:id>')
def delete_book(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM books WHERE id = ?', (id,))
    conn.commit()
    conn.close()

    flash('Книга успешно удалена!', 'success')
    return redirect(url_for('books'))

@app.route('/readers')
def readers():
    conn = get_db_connection()
    search = request.args.get('search', '')

    query = 'SELECT * FROM readers WHERE 1=1'
    params = []

    if search:
        query += ' AND (full_name LIKE ? OR email LIKE ? OR phone LIKE ?)'
        params.extend([f'%{search}%', f'%{search}%', f'%{search}%'])

    query += ' ORDER BY full_name'

    readers = conn.execute(query, params).fetchall()
    conn.close()

    return render_template('readers.html', readers=readers, search=search)

@app.route('/readers/add', methods=['GET', 'POST'])
def add_reader():
    if request.method == 'POST':
        full_name = request.form['full_name']
        email = request.form['email']
        phone = request.form['phone']
        address = request.form['address']

        conn = get_db_connection()
        try:
            conn.execute('''
                INSERT INTO readers (full_name, email, phone, address)
                VALUES (?, ?, ?, ?)
            ''', (full_name, email, phone, address))
            conn.commit()
            flash('Читатель успешно добавлен!', 'success')
            return redirect(url_for('readers'))
        except sqlite3.IntegrityError:
            flash('Читатель с таким email уже существует!', 'error')
        finally:
            conn.close()

    return render_template('add_reader.html')

@app.route('/readers/edit/<int:id>', methods=['GET', 'POST'])
def edit_reader(id):
    conn = get_db_connection()

    if request.method == 'POST':
        full_name = request.form['full_name']
        email = request.form['email']
        phone = request.form['phone']
        address = request.form['address']

        try:
            conn.execute('''
                UPDATE readers
                SET full_name=?, email=?, phone=?, address=?
                WHERE id=?
            ''', (full_name, email, phone, address, id))
            conn.commit()
            flash('Читатель успешно обновлен!', 'success')
            return redirect(url_for('readers'))
        except sqlite3.IntegrityError:
            flash('Читатель с таким email уже существует!', 'error')
        finally:
            conn.close()

    reader = conn.execute('SELECT * FROM readers WHERE id = ?', (id,)).fetchone()
    conn.close()

    return render_template('edit_reader.html', reader=reader)

@app.route('/readers/delete/<int:id>')
def delete_reader(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM readers WHERE id = ?', (id,))
    conn.commit()
    conn.close()

    flash('Читатель успешно удален!', 'success')
    return redirect(url_for('readers'))

@app.route('/loans')
def loans():
    conn = get_db_connection()

    loans = conn.execute('''
        SELECT l.*, b.title, b.author, r.full_name
        FROM loans l
        JOIN books b ON l.book_id = b.id
        JOIN readers r ON l.reader_id = r.id
        ORDER BY l.loan_date DESC
    ''').fetchall()

    conn.close()

    return render_template('loans.html', loans=loans)

@app.route('/loans/add', methods=['GET', 'POST'])
def add_loan():
    conn = get_db_connection()

    if request.method == 'POST':
        book_id = request.form['book_id']
        reader_id = request.form['reader_id']

        book = conn.execute('SELECT * FROM books WHERE id = ?', (book_id,)).fetchone()

        if book['available'] > 0:
            conn.execute('INSERT INTO loans (book_id, reader_id) VALUES (?, ?)', (book_id, reader_id))
            conn.execute('UPDATE books SET available = available - 1 WHERE id = ?', (book_id,))
            conn.commit()
            flash('Книга успешно выдана!', 'success')
            return redirect(url_for('loans'))
        else:
            flash('Книга недоступна для выдачи!', 'error')

    books = conn.execute('SELECT * FROM books WHERE available > 0 ORDER BY title').fetchall()
    readers = conn.execute('SELECT * FROM readers ORDER BY full_name').fetchall()

    conn.close()

    return render_template('add_loan.html', books=books, readers=readers)

@app.route('/loans/return/<int:id>')
def return_loan(id):
    conn = get_db_connection()

    loan = conn.execute('SELECT * FROM loans WHERE id = ?', (id,)).fetchone()

    if loan:
        conn.execute('UPDATE loans SET status = "returned", return_date = CURRENT_TIMESTAMP WHERE id = ?', (id,))
        conn.execute('UPDATE books SET available = available + 1 WHERE id = ?', (loan['book_id'],))
        conn.commit()
        flash('Книга успешно возвращена!', 'success')

    conn.close()

    return redirect(url_for('loans'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
