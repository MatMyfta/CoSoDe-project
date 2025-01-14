from flask import Flask, request, jsonify # type: ignore
import threading
import uuid
from utils.rabbitmq import publish_message, listen_for_messages
from utils.database import init_db, is_apartment_in_db, add_booking_to_db, change_booking_in_db, get_booking_apartment_from_db, is_apartment_available, cancel_booking_from_db, list_booking_from_db

app = Flask(__name__)


@app.route('/add', methods=['GET'])
def add_booking():
    apartment_id = request.args.get('apartment')
    start_date = request.args.get('from')
    end_date = request.args.get('to')
    guest_name = request.args.get('who')

    if not apartment_id or not start_date or not end_date or not guest_name:
        return jsonify({'error': 'Missing required parameters'}), 400

    apartment = is_apartment_in_db(apartment_id)

    if not apartment:
        return jsonify({'error': 'Invalid apartment ID'}), 404

    try:
        booking_id = str(uuid.uuid4())
        add_booking_to_db(booking_id, apartment_id, start_date, end_date, guest_name)

        publish_message("booking_added", {
            "booking_id": booking_id,
            "apartment_id": apartment_id,
            "start_date": start_date,
            "end_date": end_date,
            "guest_name": guest_name,
        })

        return jsonify({'message': 'Booking added successfully'}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    
@app.route('/change', methods=['GET'])
def change_booking():
    booking_id = request.args.get('id')
    new_start_date = request.args.get('from')
    new_end_date = request.args.get('to')

    if not booking_id or not new_start_date or not new_end_date:
        return jsonify({'error': 'Missing required parameters'}), 400

    try:
        apartment_id = get_booking_apartment_from_db(booking_id)

        if apartment_id is None:
            return jsonify({'error': 'Booking not found'}), 404

        if not is_apartment_available(apartment_id, new_start_date, new_end_date, booking_id):
            return jsonify({'error': 'Apartment is not available during the requested timeframe'}), 409
        
        change_booking_in_db(booking_id, new_start_date, new_end_date)

        publish_message("booking_changed", {
            "booking_id": booking_id,
            "new_start_date": new_start_date,
            "new_end_date": new_end_date,
        })

        return jsonify({'message': 'Booking updated successfully'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    

@app.route('/cancel', methods=['GET'])
def cancel_booking():
    booking_id = request.args.get('id')

    if booking_id is None:
        return jsonify({'error': 'Missing required parameter: id'}), 400
    
    try:
        booking = cancel_booking_from_db(booking_id)

        if booking is None:
            return jsonify({'error': 'Booking not found'}), 404

        publish_message("booking_canceled", {
            "booking_id": booking_id
        })

        return jsonify({'message': 'Booking removed successfully'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/list', methods=['GET'])
def list_bookings():
    booking_list = list_booking_from_db()

    return jsonify({'bookings': booking_list}), 200


@app.route('/')
def hello(): 
    return "This is the bookings microservice!"


init_db()

threading.Thread(target=listen_for_messages, daemon=True).start()

if __name__ == "__main__":
    app.run()