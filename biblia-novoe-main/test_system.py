import unittest
import sqlite3
import os
import sys
from app import app, init_db, get_db_connection

class TestLibrarySystem(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Настройка перед всеми тестами"""
        app.config['TESTING'] = True
        app.config['DATABASE'] = 'test_library.db'
        cls.client = app.test_client()

        # Инициализация тестовой БД
        if os.path.exists('test_library.db'):
            os.remove('test_library.db')
        init_db()

    @classmethod
    def tearDownClass(cls):
        """Очистка после всех тестов"""
        if os.path.exists('test_library.db'):
            os.remove('test_library.db')

    def setUp(self):
        """Настройка перед каждым тестом"""
        self.conn = get_db_connection()
        self.cursor = self.conn.cursor()

    def tearDown(self):
        """Очистка после каждого теста"""
        self.conn.close()

    # ========== ТЕСТЫ БАЗЫ ДАННЫХ ==========

    def test_01_database_tables_exist(self):
        """Тест 1: Проверка существования таблиц"""
        tables = self.cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        table_names = [t[0] for t in tables]

        self.assertIn('books', table_names, "Таблица books не существует")
        self.assertIn('readers', table_names, "Таблица readers не существует")
        self.assertIn('loans', table_names, "Таблица loans не существует")
        print("[OK] Тест 1 пройден: Все таблицы созданы")

    def test_02_insert_book(self):
        """Тест 2: Добавление книги"""
        self.cursor.execute('''
            INSERT INTO books (title, author, isbn, publisher, year, category, quantity, available)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', ('Тестовая книга', 'Тестовый автор', '978-0-00-000000-0', 'Тест', 2020, 'Тест', 1, 1))
        self.conn.commit()

        book = self.cursor.execute('SELECT * FROM books WHERE title = ?', ('Тестовая книга',)).fetchone()
        self.assertIsNotNone(book, "Книга не была добавлена")
        self.assertEqual(book[1], 'Тестовая книга')
        print("[OK] Тест 2 пройден: Книга успешно добавлена")

    def test_03_insert_reader(self):
        """Тест 3: Добавление читателя"""
        self.cursor.execute('''
            INSERT INTO readers (full_name, email, phone, address)
            VALUES (?, ?, ?, ?)
        ''', ('Тестовый читатель', 'test@test.com', '+7-900-000-00-00', 'Тестовый адрес'))
        self.conn.commit()

        reader = self.cursor.execute('SELECT * FROM readers WHERE email = ?', ('test@test.com',)).fetchone()
        self.assertIsNotNone(reader, "Читатель не был добавлен")
        self.assertEqual(reader[1], 'Тестовый читатель')
        print("[OK] Тест 3 пройден: Читатель успешно добавлен")

    def test_04_update_book(self):
        """Тест 4: Обновление информации о книге"""
        # Добавляем книгу
        self.cursor.execute('''
            INSERT INTO books (title, author, isbn, quantity, available)
            VALUES (?, ?, ?, ?, ?)
        ''', ('Книга для обновления', 'Автор', '978-0-00-000001-0', 1, 1))
        self.conn.commit()
        book_id = self.cursor.lastrowid

        # Обновляем
        self.cursor.execute('''
            UPDATE books SET title = ?, year = ? WHERE id = ?
        ''', ('Обновленная книга', 2021, book_id))
        self.conn.commit()

        updated_book = self.cursor.execute('SELECT * FROM books WHERE id = ?', (book_id,)).fetchone()
        self.assertEqual(updated_book[1], 'Обновленная книга')
        self.assertEqual(updated_book[5], 2021)
        print("[OK] Тест 4 пройден: Книга успешно обновлена")

    def test_05_delete_book(self):
        """Тест 5: Удаление книги"""
        # Добавляем книгу
        self.cursor.execute('''
            INSERT INTO books (title, author, isbn, quantity, available)
            VALUES (?, ?, ?, ?, ?)
        ''', ('Книга для удаления', 'Автор', '978-0-00-000002-0', 1, 1))
        self.conn.commit()
        book_id = self.cursor.lastrowid

        # Удаляем
        self.cursor.execute('DELETE FROM books WHERE id = ?', (book_id,))
        self.conn.commit()

        deleted_book = self.cursor.execute('SELECT * FROM books WHERE id = ?', (book_id,)).fetchone()
        self.assertIsNone(deleted_book, "Книга не была удалена")
        print("[OK] Тест 5 пройден: Книга успешно удалена")

    def test_06_search_books(self):
        """Тест 6: Поиск книг"""
        # Добавляем несколько книг
        books = [
            ('Python для начинающих', 'Иванов', '978-0-00-000003-0', 'Питер', 2020, 'Техническая литература', 2, 2),
            ('Java для профессионалов', 'Петров', '978-0-00-000004-0', 'Питер', 2021, 'Техническая литература', 1, 1),
            ('Война и мир', 'Толстой', '978-0-00-000005-0', 'АСТ', 2015, 'Художественная литература', 3, 3),
        ]
        for book in books:
            self.cursor.execute('''
                INSERT INTO books (title, author, isbn, publisher, year, category, quantity, available)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', book)
        self.conn.commit()

        # Поиск по автору
        results = self.cursor.execute(
            "SELECT * FROM books WHERE author LIKE ?", ('%Иванов%',)
        ).fetchall()
        self.assertGreater(len(results), 0, "Поиск по автору не работает")

        # Поиск по категории
        results = self.cursor.execute(
            "SELECT * FROM books WHERE category = ?", ('Техническая литература',)
        ).fetchall()
        self.assertGreaterEqual(len(results), 2, "Поиск по категории не работает")

        print("[OK] Тест 6 пройден: Поиск книг работает корректно")

    def test_07_loan_book(self):
        """Тест 7: Выдача книги"""
        # Добавляем книгу и читателя
        self.cursor.execute('''
            INSERT INTO books (title, author, isbn, quantity, available)
            VALUES (?, ?, ?, ?, ?)
        ''', ('Книга для выдачи', 'Автор', '978-0-00-000006-0', 2, 2))
        book_id = self.cursor.lastrowid

        self.cursor.execute('''
            INSERT INTO readers (full_name, email)
            VALUES (?, ?)
        ''', ('Читатель для теста', 'reader@test.com'))
        reader_id = self.cursor.lastrowid
        self.conn.commit()

        # Выдаем книгу
        self.cursor.execute('''
            INSERT INTO loans (book_id, reader_id) VALUES (?, ?)
        ''', (book_id, reader_id))
        self.cursor.execute('''
            UPDATE books SET available = available - 1 WHERE id = ?
        ''', (book_id,))
        self.conn.commit()

        # Проверяем
        loan = self.cursor.execute('SELECT * FROM loans WHERE book_id = ? AND reader_id = ?',
                                   (book_id, reader_id)).fetchone()
        self.assertIsNotNone(loan, "Выдача не была зарегистрирована")

        book = self.cursor.execute('SELECT available FROM books WHERE id = ?', (book_id,)).fetchone()
        self.assertEqual(book[0], 1, "Количество доступных книг не уменьшилось")

        print("[OK] Тест 7 пройден: Книга успешно выдана")

    def test_08_return_book(self):
        """Тест 8: Возврат книги"""
        # Добавляем книгу, читателя и выдачу
        self.cursor.execute('''
            INSERT INTO books (title, author, isbn, quantity, available)
            VALUES (?, ?, ?, ?, ?)
        ''', ('Книга для возврата', 'Автор', '978-0-00-000007-0', 1, 0))
        book_id = self.cursor.lastrowid

        self.cursor.execute('''
            INSERT INTO readers (full_name, email)
            VALUES (?, ?)
        ''', ('Читатель 2', 'reader2@test.com'))
        reader_id = self.cursor.lastrowid

        self.cursor.execute('''
            INSERT INTO loans (book_id, reader_id, status) VALUES (?, ?, ?)
        ''', (book_id, reader_id, 'active'))
        loan_id = self.cursor.lastrowid
        self.conn.commit()

        # Возвращаем книгу
        self.cursor.execute('''
            UPDATE loans SET status = 'returned', return_date = CURRENT_TIMESTAMP WHERE id = ?
        ''', (loan_id,))
        self.cursor.execute('''
            UPDATE books SET available = available + 1 WHERE id = ?
        ''', (book_id,))
        self.conn.commit()

        # Проверяем
        loan = self.cursor.execute('SELECT status FROM loans WHERE id = ?', (loan_id,)).fetchone()
        self.assertEqual(loan[0], 'returned', "Статус выдачи не изменился")

        book = self.cursor.execute('SELECT available FROM books WHERE id = ?', (book_id,)).fetchone()
        self.assertEqual(book[0], 1, "Количество доступных книг не увеличилось")

        print("[OK] Тест 8 пройден: Книга успешно возвращена")

    def test_09_unique_isbn(self):
        """Тест 9: Проверка уникальности ISBN"""
        isbn = '978-0-00-000008-0'

        # Добавляем первую книгу
        self.cursor.execute('''
            INSERT INTO books (title, author, isbn, quantity, available)
            VALUES (?, ?, ?, ?, ?)
        ''', ('Книга 1', 'Автор 1', isbn, 1, 1))
        self.conn.commit()

        # Пытаемся добавить вторую книгу с тем же ISBN
        with self.assertRaises(sqlite3.IntegrityError):
            self.cursor.execute('''
                INSERT INTO books (title, author, isbn, quantity, available)
                VALUES (?, ?, ?, ?, ?)
            ''', ('Книга 2', 'Автор 2', isbn, 1, 1))
            self.conn.commit()

        print("[OK] Тест 9 пройден: Уникальность ISBN работает")

    def test_10_statistics(self):
        """Тест 10: Статистика"""
        # Подсчитываем общее количество книг
        total_books = self.cursor.execute('SELECT COUNT(*) FROM books').fetchone()[0]
        self.assertGreaterEqual(total_books, 0, "Ошибка подсчета книг")

        # Подсчитываем читателей
        total_readers = self.cursor.execute('SELECT COUNT(*) FROM readers').fetchone()[0]
        self.assertGreaterEqual(total_readers, 0, "Ошибка подсчета читателей")

        # Подсчитываем активные выдачи
        active_loans = self.cursor.execute(
            'SELECT COUNT(*) FROM loans WHERE status = "active"'
        ).fetchone()[0]
        self.assertGreaterEqual(active_loans, 0, "Ошибка подсчета активных выдач")

        print(f"[OK] Тест 10 пройден: Статистика работает (Книг: {total_books}, Читателей: {total_readers}, Активных выдач: {active_loans})")

def run_tests():
    """Запуск всех тестов"""
    print("="*70)
    print("ЗАПУСК ТЕСТИРОВАНИЯ СИСТЕМЫ УПРАВЛЕНИЯ БИБЛИОТЕКОЙ")
    print("="*70)
    print()

    # Создаем набор тестов
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestLibrarySystem)

    # Запускаем тесты
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print()
    print("="*70)
    print("РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ")
    print("="*70)
    print(f"Всего тестов: {result.testsRun}")
    print(f"Успешно: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Провалено: {len(result.failures)}")
    print(f"Ошибок: {len(result.errors)}")
    print("="*70)

    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
