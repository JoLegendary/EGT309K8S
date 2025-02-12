from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import accuracy_score
import joblib
import os
from flask import Flask, request, send_file
import pandas as pd
from sklearn.linear_model import LinearRegression
import pickle
from io import BytesIO
from sklearn.model_selection import train_test_split

app = Flask(__name__)

@app.route('/upload', methods=['POST'])
def upload_csv():
    # Get the CSV file from the request
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
    
    model_pkl = random_forest_train(df, ['Age', 'Sex', 'Pclass', 'SibSp', 'Parch'], 'Survived', parameters)

    # Send the pickled model back as a response
    return send_file(model_pkl, mimetype='application/octet-stream', as_attachment=True, download_name="model.pkl"), 222


def random_forest_train(df, xfeature, ytarget, parameters):
    X = df[xfeature]
    y = df[ytarget]

    # Split data into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.15, random_state=42)
    print("Train Test Split Done")
    print("Starting Model Training")
    rf = RandomForestClassifier(random_state=42)
    rf_grid = GridSearchCV(rf, parameters, cv=5, scoring='accuracy')
    rf_grid.fit(X_train, y_train)

    # Predict with best random forest model
    best_rf = rf_grid.best_estimator_
    model_pkl = BytesIO()
    pickle.dump(best_rf, model_pkl)
    model_pkl.seek(0)  # Go to the beginning of the byte stream
    return model_pkl


if __name__ == "__main__":
    app.run(debug=True, port=6651)

