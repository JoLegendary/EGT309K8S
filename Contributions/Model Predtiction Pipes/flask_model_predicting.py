from flask import Flask, request, send_file, session, jsonify
import pandas as pd
import pickle
from io import BytesIO
import os
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
import random

app = Flask(__name__)
app.secret_key = '1'
cookie_dict = {}
session_id = False
@app.route('/upload', methods=['POST'])
def upload_files():
    global session_id, cookie_dict
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
    pkl_file = request.files.get('pkl')
    
    # Check if files are provided
    if not csv_file:
        return "CSV is required!", 400
    
    # Read CSV file into a pandas DataFrame
    csv_df = pd.read_csv(csv_file)
    if pkl_file:
        model = pickle.load(pkl_file)
    else:
        with open("/data/model.pkl", "rb") as f:
            model = pickle.load(f)

    cookie_dict[session_id]["status"] = "1-1:Files Read, Preparing test data"
    cookie_dict[session_id]["percentage"] = 5
    clean_data = csv_df
    csv_df = combined_data_preparation(csv_df, ['Age', 'Ticket', 'PassengerId', 'Embarked', 'Name', 'Cabin'], session_id)
    # Example processing: Let's assume the model is used to make predictions
    # Assuming the model is a regression model and csv_df has required features for prediction
    csv_df = predicting_the_test_dataset(clean_data, csv_df, model, session_id)
    # Convert the processed DataFrame to CSV (in-memory)
    output = BytesIO()
    csv_df.to_csv(output, index=False)
    output.seek(0)

    cookie_dict[session_id]["status"] = "2-1:Finishing Model Prediction"
    cookie_dict[session_id]["percentage"] = 100

    # Send back the processed CSV as a response
    return send_file(output, mimetype='text/csv', as_attachment=True, download_name="processed_output.csv"), 223


@app.route('/poll', methods=['GET'])
def poll():
    if session_id:
        return jsonify(cookie_dict[session_id]), 200
    else:
        # Return a valid response if no session id exists
        return jsonify({"status": "Waiting...", "percentage": 0}), 200
    #return (list(cookie_dict.values()) + ["No cookies!"])[-2:][0] if session.get("id") is None else cookie_dict[session.get("id")]


def predicting_the_test_dataset(clean_data, predict_data, loaded_model, session_id):

    clean_data['predicted_survived'] = loaded_model.predict(predict_data[['Age', 'Sex', 'Pclass', 'SibSp', 'Parch']])

    cookie_dict[session_id]["status"] = "1-6:Predicted target values on test data"
    cookie_dict[session_id]["percentage"] = 90

    return clean_data


def binary_sex(data):
    data['Sex'] = data['Sex'].replace({'male': 0, 'female': 1})
    print("Binary Sex done")
    return data

def add_age_with_model(data, xfeature, session_id):
    data_non_missing = data[data['Age'].notna()]

    X = data_non_missing.drop(columns=xfeature)  # Features
    y = data_non_missing['Age']                   # Target
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    cookie_dict[session_id]["status"] = "1-3:Training Model for missing ages, this will take a while"
    cookie_dict[session_id]["percentage"] = 15

    model = RandomForestRegressor()
    model.fit(X_train, y_train)
    missing_ages = data[data['Age'].isna()]
    X_missing = missing_ages.drop(columns=xfeature)

    cookie_dict[session_id]["status"] = "1-4:Running Model to predict missing ages"
    cookie_dict[session_id]["percentage"] = 50

    predicted_ages = model.predict(X_missing)

    # Fill the missing values in the original DataFrame
    data.loc[data['Age'].isna(), 'Age'] = predicted_ages

    cookie_dict[session_id]["status"] = "1-5:Added Missing Ages, now doing prediction"
    cookie_dict[session_id]["percentage"] = 70

    print("Adding Missing Age done")
    return data

def combined_data_preparation(data, xfeature, session_id):
    data = binary_sex(data)

    cookie_dict[session_id]["status"] = "1-2:Changed Sex Column to 0 or 1, now adding missing age"
    cookie_dict[session_id]["percentage"] = 10

    data = add_age_with_model(data, xfeature, session_id)
    return data


if __name__ == "__main__":
    app.run(debug=True, port=6652, host='0.0.0.0')
