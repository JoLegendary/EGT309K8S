import requests
import pandas as pd
from io import BytesIO
import pickle
# Example CSV and PKL file contents
csv_data = open("train.csv").read()
test_data = open('test.csv').read()
# print(type(csv_data))
# Send the files to Flask endpoint
url_prep = 'http://multi-app-service.default.svc.cluster.local:6650/upload'
url_train = 'http://multi-app-service.default.svc.cluster.local:6651/upload'
url_pred = 'http://multi-app-service.default.svc.cluster.local:6652/upload'
files = {
    'csv': ('data.csv', csv_data, 'text/csv'),
}

response_prep = requests.post(url_prep, files=files)

# Check the response
print(response_prep.status_code)
data = {
    'csv': ('data.csv', response_prep.content, 'text/csv'),
}

response_train = requests.post(url_train, files=data)

print(response_train.status_code)

pred = {
    'csv': ('data.csv', test_data, 'text/csv'),
    'pkl': ('model.pkl', response_train.content, 'application/octet-stream'),
}
response_pred = requests.post(url_pred, files=pred)

print(response_pred.status_code)
print(response_pred.content)