import os
import sqlite3


DATABASE = './data/apartments.db'


def init_db():
    if not os.path.exists(DATABASE):
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS apartments (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                address TEXT NOT NULL,
                noise_level INTEGER NOT NULL,
                floor INTEGER NOT NULL
            )
        ''')
        conn.commit()
        conn.close()


def add_apartment_to_db(apartment_id, name, address, noise_level, floor):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO apartments (id, name, address, noise_level, floor)
        VALUES (?, ?, ?, ?, ?)
    ''', (apartment_id, name, address, noise_level, floor))
    conn.commit()
    conn.close()


def remove_apartment_from_db(apartment_id):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM apartments WHERE id = ?', (apartment_id,))
    apartment = cursor.fetchone()

    if apartment is None:
        conn.close()
        return None

    cursor.execute('DELETE FROM apartments WHERE id = ?', (apartment_id,))
    conn.commit()
    conn.close()
    return apartment


def list_apartments_from_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM apartments')
    apartments = cursor.fetchall()
    conn.close()
    return [
        {
            'id': row[0],
            'name': row[1],
            'address': row[2],
            'noise_level': row[3],
            'floor': row[4]
        }
        for row in apartments
    ]
