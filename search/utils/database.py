
import requests
import os
import sqlite3

DATABASE = './data/search.db'
APARTMENTS_SERVICE_URL = "http://apartments:5000/list"
BOOKINGS_SERVICE_URL = "http://booking:5000/list"


def initialize_apartments(conn):
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM apartments')
    count = cursor.fetchone()[0]

    if count == 0:
        print("Initializing apartments from Apartments service...")
        try:
            response = requests.get(APARTMENTS_SERVICE_URL)
            response.raise_for_status()
            apartments = response.json().get('apartments', [])

            for row in apartments:
                cursor.execute('''
                    INSERT OR REPLACE INTO apartments (id, name, address, noise_level, floor)
                    VALUES (?, ?, ?, ?, ?)
                ''', (row['id'], row['name'], row['address'], row['noise_level'], row['floor']))

            conn.commit()
            print("Apartments initialized successfully.")
        except Exception as e:
            print(f"Failed to initialize apartments: {e}")



def initialize_bookings(conn):
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM bookings')
    count = cursor.fetchone()[0]

    if count == 0:
        print("Initializing bookings from Bookings service...")
        try:
            response = requests.get(BOOKINGS_SERVICE_URL)
            response.raise_for_status()
            bookings = response.json().get('bookings', [])

            for row in bookings:
                cursor.execute('''
                    INSERT OR REPLACE INTO bookings (id, apartment_id, start_date, end_date, guest_name)
                    VALUES (?, ?, ?, ?, ?)
                ''', (row['id'], row['apartment_id'], row['start_date'], row['end_date'], row['guest_name']))

            conn.commit()
            print("Bookings initialized successfully.")
        except Exception as e:
            print(f"Failed to initialize bookings: {e}")


def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    if not os.path.exists(DATABASE):
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bookings (
                id TEXT PRIMARY KEY,
                apartment_id TEXT NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                guest_name TEXT NOT NULL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS apartments (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                address TEXT NOT NULL,
                noise_level REAL NOT NULL,
                floor INTEGER NOT NULL
            )
        ''')
        conn.commit()

    initialize_apartments(conn)
    initialize_bookings(conn)

    conn.close()


def search_apartments_in_db(date_from, date_to):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM apartments AS a
        LEFT JOIN bookings AS b
        ON a.id = b.apartment_id
            AND (
                (b.start_date <= ? AND b.end_date >= ?)
                OR (b.start_date <= ? AND b.end_date >= ?)
                OR (b.start_date >= ? AND b.end_date <= ?)
            )
        WHERE b.id IS NULL;
    ''', (date_from, date_from, date_to, date_to, date_from, date_to))
    apartments = cursor.fetchall()
    conn.close()

    apartments_list = [
        {
            'id': row[0],
            'name': row[1],
            'address': row[2],
            'noise_level': row[3],
            'floor': row[4]
        }
        for row in apartments
    ]

    return apartments_list


def add_apartment_to_db(id, name, address, noise_level, floor):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute('''
        INSERT OR REPLACE INTO apartments (id, name, address, noise_level, floor)
        VALUES (?, ?, ?, ?, ?)
    ''', (id, name, address, noise_level, floor))

    conn.commit()
    conn.close()


def remove_apartment_from_db(id):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) FROM apartments WHERE id = ?', (id))
    count = cursor.fetchone()[0]

    if count > 0:
        cursor.execute('DELETE FROM apartments WHERE id = ?', (id))
        conn.commit()

    conn.close()

    
def add_booking_to_db(id, apartment_id, start_date, end_date, guest_name):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT OR REPLACE INTO bookings (id, apartment_id, start_date, end_date, guest_name)
        VALUES (?, ?, ?, ?, ?)
    ''', (id, apartment_id, start_date, end_date, guest_name))

    conn.commit()
    conn.close()


def change_booking_in_db(id, new_start_date, new_end_date):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) FROM bookings WHERE id = ?', (id))
    count = cursor.fetchone()[0]

    if count > 0:
        cursor.execute('''
            UPDATE bookings
            SET start_date = ?, end_date = ?
            WHERE id = ?
        ''', (new_start_date, new_end_date, id))
        conn.commit()
        
    conn.close()


def remove_booking_from_db(id):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) FROM bookings WHERE id = ?', (id))
    count = cursor.fetchone()[0]

    if count > 0:
        cursor.execute('''
            DELETE FROM bookings WHERE id = ?
        ''', (id))
        conn.commit()
    
    conn.close()

