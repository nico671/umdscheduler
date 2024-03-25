
import json
import requests

input_data = {
    'wanted_classes': ['MATH240', 'CMSC216', 'CMSC250', "JOUR150"],
    'restrictions': {
        'minSeats': 0,
        'prohibitedInstructors': ['Wiseley Wong', 'Raluca Rosca', 'Paul Kline', 'Mohammad Nayeem Teli','Ilchul Yoon'],
        'prohibitedTimes': {},
        'required_classes': []
    }
}

url = 'http://127.0.0.1:5000/schedule'
response = requests.post(
    url, json=input_data, headers={'Content-Type': 'application/json'})

# Check the response data
response_data = response.json()
json_object = json.dumps(response_data, indent=4)
print(len(response_data))
# Writing to sample.json
with open("test.json", "w") as outfile:
    outfile.write(json_object)
# self.assertIsInstance(response_data, list)
# self.assertEqual(len(response_data), 6)


