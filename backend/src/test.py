
# import json
# import requests
import scheduler


input_data = {
    'wanted_classes': ['MATH240', 'MATH241', 'CMSC216', 'CMSC250',],
    'restrictions': {
        'minSeats': 0,
        'prohibitedInstructors': [],
        'prohibitedTimes': [],
        'required_classes': []
    }
}


sched = scheduler.create_schedule(
    input_data['wanted_classes'], input_data['restrictions'])

# url = 'http://127.0.0.1:5000/schedule'
# response = requests.post(
#     url, json=input_data, headers={'Content-Type': 'application/json'})

# # Check the response data
# print(response.status_code)
# response_data = response.json()
# json_object = json.dumps(response_data, indent=4)
# print(json_object)
# # Writing to sample.json
# with open("/src/api/test.json", "w") as outfile:
#     outfile.write(json_object)
# self.assertIsInstance(response_data, list)
# self.assertEqual(len(response_data), 6)
