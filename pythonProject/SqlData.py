import mysql.connector


def connect_to_db():
    return mysql.connector.connect(
        user='root',
        password='',
        host='db',
        database='aml'
    )


def add_transactions(user_id, transactions):
    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO user_transactions (user_id, remaining_transactions)
        VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE remaining_transactions = remaining_transactions + %s;
    ''', (user_id, transactions, transactions))
    conn.commit()
    conn.close()


def subtract_transaction(user_id):
    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE user_transactions
        SET remaining_transactions = remaining_transactions - 1
        WHERE user_id = %s AND remaining_transactions > 0;
    ''', (user_id,))
    conn.commit()
    conn.close()


def get_remaining_transactions(user_id):
    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute('SELECT remaining_transactions FROM user_transactions WHERE user_id = %s', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else 0
