import pika # type: ignore
import os
import json
import time
from utils.database import add_apartment_to_db, remove_apartment_from_db, add_booking_to_db, change_booking_in_db, remove_booking_from_db

RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'rabbitmq')
APARTMENT_EXCHANGE = 'apartment_events'
BOOKING_EXCHANGE = 'booking_events'


def handle_apartment_event(event_type, data):
    apartment_id = data.get('apartment_id')
    apartment_name = data.get('name')
    apartment_address = data.get('address')
    apartment_noise_level = data.get('noise_level')
    apartment_floor = data.get('floor')

    if event_type == 'apartment_added':
        add_apartment_to_db(apartment_id, apartment_name, apartment_address, apartment_noise_level, apartment_floor)
        print(f"Apartment {apartment_id} added to local copy.", flush=True)
    elif event_type == 'apartment_removed':
        remove_apartment_from_db(apartment_id)
        print(f"Apartment {apartment_id} removed from local copy.", flush=True)


def handle_booking_event(event_type, data):
    booking_id = data.get('booking_id')

    if event_type == 'booking_added':
        booking_apartment_id = data.get('apartment_id')
        booking_start_date = data.get('start_date')
        booking_end_date = data.get('end_date')
        
        add_booking_to_db(booking_id, booking_apartment_id, booking_start_date, booking_end_date)
        
        print(f"Booking added for apartment {booking_apartment_id}.")

    elif event_type == 'booking_changed':
        booking_new_start_date = data.get('new_start_date')
        booking_new_end_date = data.get('new_end_date')
        
        change_booking_in_db(booking_id, booking_new_start_date, booking_new_end_date)
        
        print(f"Booking {booking_id} updated.")

    elif event_type == 'booking_removed':        
        remove_booking_from_db(booking_id)
        
        print(f"Booking {booking_id} removed.")


def listen_for_messages():
    while True:
        try:
            rabbit_credentials = pika.PlainCredentials(username="guest", password="guest")
            rabbit_conn_params = pika.ConnectionParameters(host=RABBITMQ_HOST, credentials=rabbit_credentials)

            connection = pika.BlockingConnection(rabbit_conn_params)
            channel = connection.channel()

            channel.exchange_declare(exchange=APARTMENT_EXCHANGE, exchange_type='fanout')
            channel.exchange_declare(exchange=BOOKING_EXCHANGE, exchange_type='fanout')

            apartment_result = channel.queue_declare('', exclusive=True)
            apartment_queue_name = apartment_result.method.queue
            channel.queue_bind(exchange=APARTMENT_EXCHANGE, queue=apartment_queue_name)

            booking_result = channel.queue_declare('', exclusive=True)
            booking_queue_name = booking_result.method.queue
            channel.queue_bind(exchange=BOOKING_EXCHANGE, queue=booking_queue_name)

            def callback(ch, method, properties, body):
                message = json.loads(body)
                event_type = message['event']
                data = message['data']

                if method.exchange == APARTMENT_EXCHANGE:
                    print(f"Apartment event received: {event_type}", flush=True)
                    handle_apartment_event(event_type, data)
                elif method.exchange == BOOKING_EXCHANGE:
                    handle_booking_event(event_type, data)
                    print(f"Booking event received: {event_type}", flush=True)


            channel.basic_consume(queue=apartment_queue_name, on_message_callback=callback, auto_ack=True)
            channel.basic_consume(queue=booking_queue_name, on_message_callback=callback, auto_ack=True)

            print("Listening for apartment and booking events...", flush=True)
            channel.start_consuming()
        except pika.exceptions.AMQPConnectionError:
            print("RabbitMQ not available. Retrying in 3 seconds...", flush=True)
            time.sleep(3)
