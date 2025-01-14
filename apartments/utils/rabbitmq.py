import pika # type: ignore
import json
import time

RABBITMQ_HOST = 'rabbitmq'
APARTMENT_EXCHANGE = 'apartment_events'

def publish_message(event_type, data):
    max_retries = 5
    for attempt in range(max_retries):
        try:
            print(f"Attempting to connect to RabbitMQ at {RABBITMQ_HOST}:5672... (attempt {attempt + 1})", flush=True)

            rabbit_credentials = pika.PlainCredentials(username="guest", password="guest")
            rabbit_conn_params = pika.ConnectionParameters(host=RABBITMQ_HOST, credentials=rabbit_credentials)

            connection = pika.BlockingConnection(rabbit_conn_params)
            channel = connection.channel()
            channel.exchange_declare(exchange=APARTMENT_EXCHANGE, exchange_type='fanout')

            message = json.dumps({"event": event_type, "data": data})
            channel.basic_publish(exchange=APARTMENT_EXCHANGE, routing_key='', body=message)
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