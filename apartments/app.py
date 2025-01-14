from flask import Flask, request, jsonify
from utils.database import init_db, add_apartment_to_db, remove_apartment_from_db, list_apartments_from_db
from utils.rabbitmq import publish_message
import sqlite3
import uuid


app = Flask(__name__)
DATABASE = 'apartments.db'


@app.route('/add', methods=['GET'])
def add_apartment():
    name = request.args.get('name')
    address = request.args.get('address')
    noise_level = request.args.get('noiselevel', type=int)
    floor = request.args.get('floor', type=int)

    if not name or not address or noise_level is None or floor is None:
        return jsonify({'error': 'Missing required parameters'}), 400

    try:
        apartment_id = str(uuid.uuid4())
        add_apartment_to_db(apartment_id, name, address, noise_level, floor)

        publish_message("apartment_added", {
            "apartment_id": apartment_id,
            "name": name,
            "address": address,
            "noise_level": noise_level,
            "floor": floor
        })

        return jsonify({'message': 'Apartment added successfully'}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    

@app.route('/list', methods=['GET'])
def list_apartments():
    try:
        apartments = list_apartments_from_db()

        return jsonify({'apartments': apartments}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/remove', methods=['GET'])
def remove_apartment():
    apartment_id = request.args.get('id')

    if apartment_id is None:
        return jsonify({'error': 'Missing required parameter: id'}), 400

    try:
        apartment = remove_apartment_from_db(apartment_id)

        if apartment is None:
            return jsonify({'error': 'Apartment not found'}), 404

        publish_message("apartment_removed", {
            "apartment_id": apartment_id
        })

        return jsonify({'message': 'Apartment removed successfully'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500



@app.route('/')
def hello(): 
    return "This is the apartment microservice!"


init_db()

if __name__ == "__main__":
    app.run()
