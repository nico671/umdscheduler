from scraper import *
import unittest
import api
import json

class APITestCase(unittest.TestCase):
    def setUp(self):
        self.app = api.app.test_client()
        self.app.testing = True

    def test_create_schedule(self):
        # Define your input data
        input_data = {
            'wanted_classes': ['ENGL142', 'TLPL443', 'WEID139T'],
            'restrictions': {
                'minSeats': 0,
                'prohibitedInstructors': [''],
                'prohibitedTimes': {},
                'required_classes': ['ENGL142', 'TLPL443', 'WEID139T']
            }
        }

        # Send a POST request to the /schedule endpoint
        response = self.app.post('/schedule', data=json.dumps(input_data), content_type='application/json')

        # Check the response status code
        self.assertEqual(response.status_code, 200)

        # Check the response data
        response_data = json.loads(response.get_data())
        self.assertIsInstance(response_data, list)

if __name__ == '__main__':
    unittest.main()