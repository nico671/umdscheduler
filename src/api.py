import json
from flask_cors import CORS
import scheduler
from flask import Flask, jsonify, make_response, request

app = Flask(__name__)
CORS(app, resources={r"/schedule": {"origins": "*"}})


@app.route('/schedule', methods=['POST'])
def create_schedule():
    # Get the input data from the request
    # 
    data = json.loads(json.dumps(request.get_json()))

    print(data)

    wanted_classes = data.get('wanted_classes', [])
    restrictions = data.get('restrictions', {})
    # Call your scheduling function with the input data
    result = scheduler.create_schedule(wanted_classes, restrictions)
    # print(result)
    # Create a Response object
    response = make_response(jsonify(result))
    # Set headers on the Response object
    response.access_control_allow_origin = '*'
    # Return the Response object
    print(response)
    return response


if __name__ == '__main__':
    app.run(debug=True)
