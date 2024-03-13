from flask import Flask, request, jsonify
import scheduler

app = Flask(__name__)


@app.route('/schedule', methods=['POST'])
def create_schedule():
    # Get the input data from the request
    # print('here')
    data = request.get_json()
    print(data)

    wanted_classes = data.get('wanted_classes', [])
    restrictions = data.get('restrictions', {})

    # Call your scheduling function with the input data
    result = scheduler.create_schedule(wanted_classes, restrictions)
    # print(result)
    # Return the result as JSON
    return jsonify(result)


if __name__ == '__main__':
    app.run(debug=True)