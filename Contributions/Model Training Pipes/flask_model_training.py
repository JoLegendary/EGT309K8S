from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import accuracy_score
import joblib
import os
from flask import Flask, request, send_file, session
import pandas as pd
from sklearn.linear_model import LinearRegression
import pickle
from io import BytesIO
from sklearn.model_selection import train_test_split
import random

app = Flask(__name__)
app.secret_key = '1'
cookie_dict = {}
@app.route('/upload', methods=['POST'])
def upload_csv():
    # Get the CSV file from the request
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

    # Check if the CSV file is provided
    if not csv_file:
        return "CSV file is required!", 400

    # Read the CSV file into a DataFrame
    df = pd.read_csv(csv_file)
    parameters =  { "n_estimators": [50, 100, 200],
        "max_depth": [None, 10, 20, 30],
        "min_samples_split": [2, 5, 10],
        "min_samples_leaf": [1, 2, 4]}
    
    cookie_dict[session_id]["status"] = '1-1:File Read'
    cookie_dict[session_id]["percentage"] = 5

    model_pkl = random_forest_train(df, ['Age', 'Sex', 'Pclass', 'SibSp', 'Parch'], 'Survived', parameters, session_id)

    cookie_dict[session_id]["status"] = "2-1:Finishing Model Training"
    cookie_dict[session_id]["percentage"] = 100

    # Send the pickled model back as a response
    return send_file(model_pkl, mimetype='application/octet-stream', as_attachment=True, download_name="model.pkl"), 222


@app.route('/poll', methods=['GET'])
def poll():
    return (list(cookie_dict.values()) + ["No cookies!"])[-2:][0] if session.get("id") is None else cookie_dict[session.get("id")]

def random_forest_train(df, xfeature, ytarget, parameters, session_id):
    X = df[xfeature]
    y = df[ytarget]

    # Split data into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.15, random_state=42)


    cookie_dict[session_id]["status"] = "1-2:Starting model Training, This will take a long time"
    cookie_dict[session_id]["percentage"] = 10

    rf = RandomForestClassifier(random_state=42)
    rf_grid = GridSearchCV(rf, parameters, cv=5, scoring='accuracy')
    rf_grid.fit(X_train, y_train)

    # Predict with best random forest model
    best_rf = rf_grid.best_estimator_


    cookie_dict[session_id]["status"] = "1-3:Model Done Training, saving pkl file"
    cookie_dict[session_id]["percentage"] = 90

    model_pkl = BytesIO()
    pickle.dump(best_rf, model_pkl)
    model_pkl.seek(0)  # Go to the beginning of the byte stream
    pkl = "model" + session.get("id") + ".pkl"
    with open(pkl, "wb") as f:
        pickle.dump(best_rf, f)
    return model_pkl


if __name__ == "__main__":
    app.run(debug=True, port=6651, host='0.0.0.0')

