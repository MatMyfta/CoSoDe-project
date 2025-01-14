import os
import sqlite3
import requests


DATABASE = './data/bookings.db'
APARTMENTS_SERVICE_URL = "http://apartments:5000/list"


def init_db():
    if not os.path.exists(DATABASE):
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
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
        conn.close()

        initialize_apartments()


def initialize_apartments():
    conn = sqlite3.connect(DATABASE)
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

    conn.close()


def is_apartment_available(apartment_id, new_start_date, new_end_date, booking_id):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM bookings
        WHERE apartment_id = ?
        AND id != ?
        AND (
            (start_date <= ? AND end_date >= ?)
            OR (start_date <= ? AND end_date >= ?)
            OR (start_date >= ? AND end_date <= ?)
        )
    ''', (apartment_id, booking_id, new_start_date, new_start_date, new_end_date, new_end_date, new_start_date, new_end_date))
    overlapping_booking = cursor.fetchone()
    conn.close()
    return overlapping_booking is None


def add_apartment_to_db(apartment_id, name, address, noise_level, floor):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO apartments (id, name, address, noise_level, floor)
        VALUES (?, ?, ?, ?, ?)
    ''', (apartment_id, name, address, noise_level, floor))
    conn.commit()
    conn.close()


def is_apartment_in_db(apartment_id):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM apartments WHERE id = ?', (apartment_id,))
    apartment = cursor.fetchone()

    return apartment


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


def add_booking_to_db(id, apartment_id, start_date, end_date, guest_name):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO bookings (id, apartment_id, start_date, end_date, guest_name)
        VALUES (?, ?, ?, ?, ?)
    ''', (id, apartment_id, start_date, end_date, guest_name))
    conn.commit()
    conn.close()


def get_booking_apartment_from_db(booking_id):
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        cursor.execute('SELECT apartment_id FROM bookings WHERE id = ?', (booking_id,))
        booking = cursor.fetchone()

        if booking is None:
            conn.close()
            return None

        apartment_id = booking[0]
        return apartment_id

def change_booking_in_db(new_start_date, new_end_date, booking_id):
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE bookings
            SET start_date = ?, end_date = ?
            WHERE id = ?
        ''', (new_start_date, new_end_date, booking_id))

        conn.commit()
        conn.close()


def cancel_booking_from_db(booking_id):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM bookings WHERE id = ?', (booking_id,))
    booking = cursor.fetchone()

    if booking is None:
        conn.close()
        return None

    cursor.execute('DELETE FROM bookings WHERE id = ?', (booking_id,))

    conn.commit()
    conn.close()

    return booking


def list_booking_from_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM bookings')
    bookings = cursor.fetchall()
    conn.close()

    booking_list = [
        {
            'id': row[0],
            'apartment_id': row[1],
            'start_date': row[2],
            'end_date': row[3],
            'guest_name': row[4]
        }
        for row in bookings
    ]

    return booking_list