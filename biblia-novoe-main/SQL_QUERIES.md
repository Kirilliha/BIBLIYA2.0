# SQL-запросы для АИС "Система управления библиотекой"

## 1. Создание таблиц (DDL - Data Definition Language)

### Таблица books (Книги)
```sql
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
);
```

### Таблица readers (Читатели)
```sql
CREATE TABLE IF NOT EXISTS readers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    email TEXT UNIQUE,
    phone TEXT,
    address TEXT,
    registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Таблица loans (Выдача книг)
```sql
CREATE TABLE IF NOT EXISTS loans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id INTEGER NOT NULL,
    reader_id INTEGER NOT NULL,
    loan_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    return_date TIMESTAMP,
    status TEXT DEFAULT 'active',
    FOREIGN KEY (book_id) REFERENCES books (id),
    FOREIGN KEY (reader_id) REFERENCES readers (id)
);
```

## 2. Вставка данных (INSERT)

### Добавление книги
```sql
INSERT INTO books (title, author, isbn, publisher, year, category, quantity, available)
VALUES ('Война и мир', 'Лев Толстой', '978-5-17-098352-3', 'АСТ', 2015, 'Художественная литература', 3, 3);
```

### Добавление читателя
```sql
INSERT INTO readers (full_name, email, phone, address)
VALUES ('Иванов Иван Иванович', 'ivanov@example.com', '+7-900-123-45-67', 'г. Москва, ул. Ленина, д. 1');
```

### Выдача книги читателю
```sql
INSERT INTO loans (book_id, reader_id)
VALUES (1, 1);
```

## 3. Выборка данных (SELECT)

### Получить все книги
```sql
SELECT * FROM books ORDER BY title;
```

### Поиск книг по автору
```sql
SELECT * FROM books 
WHERE author LIKE '%Толстой%' 
ORDER BY title;
```

### Поиск книг по категории
```sql
SELECT * FROM books 
WHERE category = 'Художественная литература' 
ORDER BY title;
```

### Получить доступные книги
```sql
SELECT * FROM books 
WHERE available > 0 
ORDER BY title;
```

### Получить всех читателей
```sql
SELECT * FROM readers 
ORDER BY full_name;
```

### Поиск читателя по email
```sql
SELECT * FROM readers 
WHERE email = 'ivanov@example.com';
```

### Получить все активные выдачи
```sql
SELECT l.*, b.title, b.author, r.full_name
FROM loans l
JOIN books b ON l.book_id = b.id
JOIN readers r ON l.reader_id = r.id
WHERE l.status = 'active'
ORDER BY l.loan_date DESC;
```

### Получить историю выдач конкретной книги
```sql
SELECT l.*, r.full_name, r.email
FROM loans l
JOIN readers r ON l.reader_id = r.id
WHERE l.book_id = 1
ORDER BY l.loan_date DESC;
```

### Получить книги, взятые конкретным читателем
```sql
SELECT l.*, b.title, b.author
FROM loans l
JOIN books b ON l.book_id = b.id
WHERE l.reader_id = 1 AND l.status = 'active'
ORDER BY l.loan_date DESC;
```

### Статистика: количество книг по категориям
```sql
SELECT category, COUNT(*) as count, SUM(quantity) as total_copies
FROM books
GROUP BY category
ORDER BY count DESC;
```

### Статистика: самые популярные книги
```sql
SELECT b.title, b.author, COUNT(l.id) as loan_count
FROM books b
LEFT JOIN loans l ON b.id = l.book_id
GROUP BY b.id
ORDER BY loan_count DESC
LIMIT 10;
```

### Статистика: активные читатели
```sql
SELECT r.full_name, r.email, COUNT(l.id) as books_taken
FROM readers r
LEFT JOIN loans l ON r.id = l.reader_id
WHERE l.status = 'active'
GROUP BY r.id
ORDER BY books_taken DESC;
```

## 4. Обновление данных (UPDATE)

### Обновить информацию о книге
```sql
UPDATE books
SET title = 'Война и мир (полное издание)', 
    year = 2020,
    quantity = 5
WHERE id = 1;
```

### Обновить данные читателя
```sql
UPDATE readers
SET phone = '+7-900-999-88-77',
    address = 'г. Москва, ул. Новая, д. 10'
WHERE id = 1;
```

### Уменьшить количество доступных книг при выдаче
```sql
UPDATE books
SET available = available - 1
WHERE id = 1;
```

### Увеличить количество доступных книг при возврате
```sql
UPDATE books
SET available = available + 1
WHERE id = 1;
```

### Отметить книгу как возвращенную
```sql
UPDATE loans
SET status = 'returned',
    return_date = CURRENT_TIMESTAMP
WHERE id = 1;
```

## 5. Удаление данных (DELETE)

### Удалить книгу
```sql
DELETE FROM books WHERE id = 1;
```

### Удалить читателя
```sql
DELETE FROM readers WHERE id = 1;
```

### Удалить запись о выдаче
```sql
DELETE FROM loans WHERE id = 1;
```

### Удалить все возвращенные записи старше года
```sql
DELETE FROM loans 
WHERE status = 'returned' 
AND return_date < datetime('now', '-1 year');
```

## 6. Сложные запросы

### Найти книги, которые никогда не выдавались
```sql
SELECT b.*
FROM books b
LEFT JOIN loans l ON b.id = l.book_id
WHERE l.id IS NULL;
```

### Найти читателей, которые не брали книги
```sql
SELECT r.*
FROM readers r
LEFT JOIN loans l ON r.id = l.reader_id
WHERE l.id IS NULL;
```

### Найти просроченные книги (не возвращены более 30 дней)
```sql
SELECT l.*, b.title, r.full_name, 
       julianday('now') - julianday(l.loan_date) as days_overdue
FROM loans l
JOIN books b ON l.book_id = b.id
JOIN readers r ON l.reader_id = r.id
WHERE l.status = 'active' 
AND julianday('now') - julianday(l.loan_date) > 30
ORDER BY days_overdue DESC;
```

### Получить топ-5 самых активных читателей
```sql
SELECT r.full_name, r.email, COUNT(l.id) as total_loans
FROM readers r
JOIN loans l ON r.id = l.reader_id
GROUP BY r.id
ORDER BY total_loans DESC
LIMIT 5;
```

## 7. Транзакции

### Выдача книги (с проверкой доступности)
```sql
BEGIN TRANSACTION;

-- Проверяем доступность
SELECT available FROM books WHERE id = 1;

-- Если available > 0, выполняем выдачу
INSERT INTO loans (book_id, reader_id) VALUES (1, 1);
UPDATE books SET available = available - 1 WHERE id = 1;

COMMIT;
```

### Возврат книги
```sql
BEGIN TRANSACTION;

UPDATE loans 
SET status = 'returned', return_date = CURRENT_TIMESTAMP 
WHERE id = 1;

UPDATE books 
SET available = available + 1 
WHERE id = (SELECT book_id FROM loans WHERE id = 1);

COMMIT;
```

## 8. Индексы для оптимизации

```sql
-- Индекс для поиска по ISBN
CREATE INDEX idx_books_isbn ON books(isbn);

-- Индекс для поиска по автору
CREATE INDEX idx_books_author ON books(author);

-- Индекс для поиска по категории
CREATE INDEX idx_books_category ON books(category);

-- Индекс для поиска по email читателя
CREATE INDEX idx_readers_email ON readers(email);

-- Индекс для активных выдач
CREATE INDEX idx_loans_status ON loans(status);

-- Составной индекс для выдач
CREATE INDEX idx_loans_book_reader ON loans(book_id, reader_id);
```

## 9. Представления (Views)

### Представление для активных выдач
```sql
CREATE VIEW active_loans_view AS
SELECT 
    l.id,
    b.title as book_title,
    b.author as book_author,
    r.full_name as reader_name,
    r.email as reader_email,
    l.loan_date,
    julianday('now') - julianday(l.loan_date) as days_borrowed
FROM loans l
JOIN books b ON l.book_id = b.id
JOIN readers r ON l.reader_id = r.id
WHERE l.status = 'active';
```

### Представление для статистики по книгам
```sql
CREATE VIEW books_statistics AS
SELECT 
    b.id,
    b.title,
    b.author,
    b.category,
    b.quantity,
    b.available,
    COUNT(l.id) as total_loans,
    SUM(CASE WHEN l.status = 'active' THEN 1 ELSE 0 END) as current_loans
FROM books b
LEFT JOIN loans l ON b.id = l.book_id
GROUP BY b.id;
```
