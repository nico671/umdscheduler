from flask import Flask, make_response, request, jsonify
from flask_cors import cross_origin
import scheduler

app = Flask(__name__)


@app.route('/schedule', methods=['POST'])
@cross_origin()
def create_schedule():
    # Get the input data from the request
    data = request.get_json()

    wanted_classes = data.get('wanted_classes', [])
    restrictions = data.get('restrictions', {})
    # Call your scheduling function with the input data
    result = scheduler.create_schedule(wanted_classes, restrictions)
    print(result)
    # Create a Response object
    response = make_response(jsonify(result))
    # Set headers on the Response object
    response.headers['Content-Type'] = 'application/json'
    response.headers['Access-Control-Allow-Origin'] = '*'
    # Return the Response object
    return response


if __name__ == '__main__':
    app.run(debug=True)