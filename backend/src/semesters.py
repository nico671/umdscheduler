import requests

print(requests.get('https://api.umd.io/v1/courses/semesters').json())
