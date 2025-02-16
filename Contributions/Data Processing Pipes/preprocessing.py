from flask import Flask, request, send_file, session
import pandas as pd
import pickle
from io import BytesIO, StringIO
import os
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
status = 0
app = Flask(__name__)
app.secret_key = '1'
@app.route('/upload', methods=['POST'])
def upload_files():
    # Get files from request
    csv_file = request.files.get('csv')

    csv_df = pd.read_csv(csv_file )
    msg = "\033[92m" + str(csv_df) + "\033[0m"
    print(msg)
    
    # Check if files are provided
    if not csv_file:
        return "CSV files are required!", 400
    
    # Read CSV file into a pandas DataFrame
    
    csv_df = combined_data_preparation(csv_df, ['Age', 'Ticket', 'PassengerId', 'Embarked', 'Name', 'Cabin'])

    # Convert the processed DataFrame to CSV (in-memory)
    output = BytesIO()
    csv_df.to_csv(output, index=False)
    output.seek(0)

    # Send back the processed CSV as a response
    return send_file(output, mimetype='text/csv', as_attachment=True, download_name="processed_output.csv"), 221

@app.route('/poll', methods=['POST'])
def poll():
    print(f"{session.get("id","No id yet")} is logged in")
    if session.get("id") is None: session["id"] = 1
    return str(session.get('id'))

def binary_sex(data):
    data['Sex'] = data['Sex'].replace({'male': 0, 'female': 1})
    print("Binary Sex done")
    return data

def add_age_with_model(data, xfeature):
    data_non_missing = data[data['Age'].notna()]

    X = data_non_missing.drop(columns=xfeature)  # Features
    y = data_non_missing['Age']                   # Target
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = RandomForestRegressor()
    model.fit(X_train, y_train)
    missing_ages = data[data['Age'].isna()]
    X_missing = missing_ages.drop(columns=xfeature)

    predicted_ages = model.predict(X_missing)

    # Fill the missing values in the original DataFrame
    data.loc[data['Age'].isna(), 'Age'] = predicted_ages
    print("Adding Missing Age done")
    return data

def combined_data_preparation(data, xfeature):
    data = binary_sex(data)
    data = add_age_with_model(data, xfeature)
    return data



if __name__ == "__main__":
    app.run(debug=True, port=6650)
