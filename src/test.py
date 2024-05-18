
import json
import requests

input_data = {
    'wanted_classes': ['MATH240', 'CMSC216', 'CMSC250', "PHIL211"],
    'restrictions': {
        'minSeats': 0,
        'prohibitedInstructors': [],
        'prohibitedTimes': tuple([{"day": "Th", "start": "8:00am", "end": "9:00am"}, {"day": "F", "start": "8:00am", "end": "11:00am"}, {"day": "W", "start": "8:00am", "end": "9:00am"}]),
        'required_classes': []
    }
}

url = 'https://umdscheduler.onrender.com/schedule'
response = requests.post(
    url, json=input_data, headers={'Content-Type': 'application/json'})

# Check the response data
print(response.status_code)
response_data = response.json()
json_object = json.dumps(response_data, indent=4)
print(json_object)
# Writing to sample.json
with open("/src/api/test.json", "w") as outfile:
    outfile.write(json_object)
# self.assertIsInstance(response_data, list)
# self.assertEqual(len(response_data), 6)


