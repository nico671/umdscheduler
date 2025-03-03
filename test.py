import requests

data = requests.get("https://api.umd.io/v1/courses/semesters")
print(data.json())
