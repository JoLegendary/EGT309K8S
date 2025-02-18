from flask import Flask, request, send_file, session
import pandas as pd
import pickle
from io import BytesIO, StringIO
import os
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
import random
import time
status = 0
app = Flask(__name__)
app.secret_key = '1'
cookie_dict = {}
@app.route('/upload', methods=['POST'])
def upload_files():
    # Get files from request
    print(f"{session.get("id","No id yet")} is logged in")
    if session.get("id") is None:
        while True:
            rand = random.randint(1, 2**64)
            if not cookie_dict.get(rand):
                cookie_dict.update({rand:{"status": "0-0:Starting", "percentage": 0}})
                break
        session["id"] = rand
    if not cookie_dict.get(session.get("id")):
        cookie_dict.update({session.get("id"):{"status": "0-0:Starting", "percentage": 0}})
    session_id = session.get("id")

    csv_file = request.files.get('csv')

    csv_df = pd.read_csv(csv_file )
    msg = "\033[92m" + str(csv_df) + "\033[0m"
    print(msg)
    
    # Check if files are provided
    if not csv_file:
        return "CSV files are required!", 400
    
    # Read CSV file into a pandas DataFrame
    cookie_dict[session_id]["status"] = "1-1:File Read"
    cookie_dict[session_id]["percentage"] = 5
    print(cookie_dict)
    csv_df = combined_data_preparation(csv_df, ['Age', 'Ticket', 'PassengerId', 'Embarked', 'Name', 'Cabin'], session_id)

    # Convert the processed DataFrame to CSV (in-memory)
    output = BytesIO()
    csv_df.to_csv(output, index=False)
    output.seek(0)

    for x in range(5):
        cookie_dict[session_id]["percentage"] = x * 15
        time.sleep(1.4)

    cookie_dict[session_id]["status"] = "1-2:Finishing Data Preparation"
    cookie_dict[session_id]["percentage"] = 100
    print(cookie_dict)
    # Send back the processed CSV as a response
    return send_file(output, mimetype='text/csv', as_attachment=True, download_name="processed_output.csv"), 221

@app.route('/poll', methods=['GET'])
def poll():
    if session.get("id"):
        return cookie_dict[session.get("id")]
    else:
        return None
    #return (list(cookie_dict.values()) + ["No cookies!"])[-2:][0] if session.get("id") is None else cookie_dict[session.get("id")]

def binary_sex(data):
    data['Sex'] = data['Sex'].replace({'male': 0, 'female': 1})
    return data

def add_age_with_model(data, xfeature, session_id):
    data_non_missing = data[data['Age'].notna()]
    X = data_non_missing.drop(columns=xfeature)  # Features
    y = data_non_missing['Age']                   # Target
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    cookie_dict[session_id]["status"] = "1-3:Training Model for missing ages, this will take a while"
    cookie_dict[session_id]["percentage"] = 30
    print(cookie_dict)
    model = RandomForestRegressor()
    model.fit(X_train, y_train)
    missing_ages = data[data['Age'].isna()]
    X_missing = missing_ages.drop(columns=xfeature)

    cookie_dict[session_id]["status"] = "1-4:Running Model to predict missing ages"
    cookie_dict[session_id]["percentage"] = 70
    print(cookie_dict)
    predicted_ages = model.predict(X_missing)
    
    # Fill the missing values in the original DataFrame
    data.loc[data['Age'].isna(), 'Age'] = predicted_ages

    cookie_dict[session_id]["status"] = "1-5:Added Missing Ages"
    cookie_dict[session_id]["percentage"] = 90
    print(cookie_dict)
    return data

def combined_data_preparation(data, xfeature, session_id):
    data = binary_sex(data)

    cookie_dict[session_id]["status"] = "1-2:Changed Sex Column to 0 or 1, now adding missing age"
    cookie_dict[session_id]["percentage"] = 15
    print(cookie_dict)
    data = add_age_with_model(data, xfeature, session_id)
    return data



if __name__ == "__main__":
    app.run(debug=True, port=6650, host='0.0.0.0')
