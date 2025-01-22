
import pika # type: ignore
import json
import time
import os
from utils.database import add_apartment_to_db, remove_apartment_from_db


RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'rabbitmq')
APARTMENT_EXCHANGE = 'apartment_events'
BOOKING_EXCHANGE = 'booking_events'


def publish_message(event_type, data):
    max_retries = 5
    for attempt in range(max_retries):
        try:
            print(f"Attempting to connect to RabbitMQ at {RABBITMQ_HOST}:5672... (attempt {attempt + 1})", flush=True)

            rabbit_credentials = pika.PlainCredentials(username="guest", password="guest")
            rabbit_conn_params = pika.ConnectionParameters(host=RABBITMQ_HOST, credentials=rabbit_credentials)

            connection = pika.BlockingConnection(rabbit_conn_params)
            channel = connection.channel()
            channel.exchange_declare(exchange=BOOKING_EXCHANGE, exchange_type='fanout')

            message = json.dumps({"event": event_type, "data": data})
            channel.basic_publish(exchange=BOOKING_EXCHANGE, routing_key='', body=message)
            print(f"Message published: {message}", flush=True)
            connection.close()
            return
        except pika.exceptions.AMQPConnectionError as e:
            print(f"RabbitMQ connection error: {e}. Retrying in 3 seconds...", flush=True)
            time.sleep(3)
        except Exception as e:
            print(f"An unexpected error occurred while publishing the message: {e}", flush=True)
            break
    print("Failed to connect to RabbitMQ after multiple attempts. Message not published.", flush=True)


def handle_apartment_event(event_type, data):
    apartment_id = data.get('apartment_id')

    if event_type == 'apartment_added':
        add_apartment_to_db(apartment_id)
        print(f"Apartment {apartment_id} added to local copy.", flush=True)
    elif event_type == 'apartment_removed':
        remove_apartment_from_db(apartment_id)
        print(f"Apartment {apartment_id} removed from local copy.", flush=True)


def listen_for_messages():
    while True:
        try:
            rabbit_credentials = pika.PlainCredentials(username="guest", password="guest")
            rabbit_conn_params = pika.ConnectionParameters(host=RABBITMQ_HOST, credentials=rabbit_credentials)

            connection = pika.BlockingConnection(rabbit_conn_params)
            channel = connection.channel()
            channel.exchange_declare(exchange=APARTMENT_EXCHANGE, exchange_type='fanout')

            result = channel.queue_declare('', exclusive=True)
            queue_name = result.method.queue
            channel.queue_bind(exchange=APARTMENT_EXCHANGE, queue=queue_name)

            def callback(ch, method, properties, body):
                message = json.loads(body)
                event_type = message['event']
                data = message['data']
                handle_apartment_event(event_type, data)

            channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
            print("Listening for apartment events...", flush=True)
            channel.start_consuming()
        except pika.exceptions.AMQPConnectionError:
            print("RabbitMQ not available. Retrying in 3 seconds...", flush=True)
            time.sleep(3)