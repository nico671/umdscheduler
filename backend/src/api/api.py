from flask import Flask, request, jsonify
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
    # Return the result as JSON
    return jsonify(result)


if __name__ == '__main__':
    app.run(debug=True)