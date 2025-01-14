from flask import Flask, request, jsonify
import threading
from utils.database import init_db, search_apartments_in_db
from utils.rabbitmq import listen_for_messages

app = Flask(__name__)


@app.route('/')
def hello(): 
    return "This is the search microservice!"


@app.route('/search', methods=['GET'])
def search():
    try:
        date_from = request.args.get('from')
        date_to = request.args.get('to')

        apartments_list = search_apartments_in_db(date_from, date_to)

        return jsonify({'apartments': apartments_list}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


init_db()

threading.Thread(target=listen_for_messages, daemon=True).start()

if __name__ == "__main__":
    app.run()