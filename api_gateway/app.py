from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

APARTMENT_SERVICE_URL = "http://apartments:5000"
BOOKING_SERVICE_URL = "http://booking:5000"
SEARCH_SERVICE_URL = "http://search:5000"


@app.route('/apartments/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def apartments_proxy(path):
    url = f"{APARTMENT_SERVICE_URL}/{path}"
    return forward_request(url)


@app.route('/bookings/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def bookings_proxy(path):
    url = f"{BOOKING_SERVICE_URL}/{path}"
    return forward_request(url)


@app.route('/search/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def search_proxy(path):
    url = f"{SEARCH_SERVICE_URL}/{path}"
    return forward_request(url)


def forward_request(url):
    try:
        response = requests.request(
            method=request.method,
            url=url,
            headers={key: value for key, value in request.headers if key != 'Host'},
            params=request.args,
            data=request.data,
            json=request.get_json(silent=True),
            timeout=5
        )
        return (response.content, response.status_code, response.headers.items())
    except requests.RequestException as e:
        return jsonify({'error': f"Failed to connect to service: {str(e)}"}), 502


if __name__ == '__main__':
    app.run()