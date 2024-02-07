import mysql.connector

def connect_to_db():
    return mysql.connector.connect(
        user='root',  # Измените на ваше имя пользователя
        password='',  # Измените на ваш пароль
        host='127.0.0.1',
        database='aml'  # Измените на название вашей базы данных
    )

def add_test_user(user_id, transactions):
    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO user_transactions (user_id, remaining_transactions)
        VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE remaining_transactions = %s;
    ''', (user_id, transactions, transactions))
    conn.commit()
    conn.close()

# Добавление тестового пользователя
add_test_user(361807178, 50)  # 12345678 - это пример ID пользователя
