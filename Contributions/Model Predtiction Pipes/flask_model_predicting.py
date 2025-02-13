from flask import Flask, request, send_file
import pandas as pd
import pickle
from io import BytesIO
import os
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split

app = Flask(__name__)

@app.route('/upload', methods=['POST'])
def upload_files():
    # Get files from request
    csv_file = request.files.get('csv')
    pkl_file = request.files.get('pkl')
    
    # Check if files are provided
    if not csv_file or not pkl_file:
        return "CSV and PKL files are required!", 400
    
    # Read CSV file into a pandas DataFrame
    csv_df = pd.read_csv(csv_file)
    
    # Read PKL file into a model or data (adjust depending on your use case)
    model = pickle.load(pkl_file)
    csv_df = combined_data_preparation(csv_df, ['Age', 'Ticket', 'PassengerId', 'Embarked', 'Name', 'Cabin'])
    # Example processing: Let's assume the model is used to make predictions
    # Assuming the model is a regression model and csv_df has required features for prediction
    clean_data = csv_df
    csv_df = predicting_the_test_dataset(clean_data, csv_df, model)
    # Convert the processed DataFrame to CSV (in-memory)
    output = BytesIO()
    csv_df.to_csv(output, index=False)
    output.seek(0)

    # Send back the processed CSV as a response
    return send_file(output, mimetype='text/csv', as_attachment=True, download_name="processed_output.csv"), 223

def predicting_the_test_dataset(clean_data, predict_data, loaded_model):

    predict_data['predicted_survived'] = loaded_model.predict(clean_data[['Age', 'Sex', 'Pclass', 'SibSp', 'Parch']])
    return predict_data


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
    app.run(debug=True, port=6652)
