from flask import Flask, request, jsonify
import scheduler

app = Flask(__name__)

@app.route('/schedule', methods=['POST'])
def create_schedule():
    # Get the input data from the request
    data = request.get_json()

    # Extract the list of wanted classes and restrictions from the data dictionary
    wanted_classes = data.get('wanted_classes', [])
    restrictions = data.get('restrictions', [])

    # Call your scheduling function with the input data
    result = scheduler.backtracking(wanted_classes, restrictions)

    # Return the result as JSON
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)

