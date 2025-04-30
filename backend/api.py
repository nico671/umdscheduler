from flask import Flask, make_response, request
from flask_cors import CORS

import scheduler as scheduler

app = Flask(__name__)
CORS(app, resources={r"/schedule": {"origins": "http://localhost:5173"}})


@app.route("/schedule", methods=["POST"])
def create_schedule():
    # Get the input data from the request
    #
    data = request.get_json()
    # print(data)

    wanted_classes = data.get("wanted_classes", [])
    restrictions = data.get("restrictions", {})
    # Call your scheduling function with the input data
    result = scheduler.create_schedule(wanted_classes, restrictions)
    # print(result)
    # Create a Response object
    response = make_response(result)
    # Set headers on the Response object
    response.access_control_allow_origin = "*"
    # Return the Response object
    # print(response.status_code)
    if response.status_code != 200:
        print(response.json)
    else:
        return response
    pass


if __name__ == "__main__":
    app.run(debug=True)
