from flask import Flask, render_template, request, send_file
import requests
import io
import pickle

app = Flask(__name__)

csv_data = None
test_data = None
output_filename = "prediction.csv"

def run_pipeline():
    print("Pipeline is running...")  # Replace with actual processing logic
    url_prep = 'http://multi-app-service.default.svc.cluster.local:6650/upload'
    url_train = 'http://multi-app-service.default.svc.cluster.local:6651/upload'
    url_pred = 'http://multi-app-service.default.svc.cluster.local:6652/upload'
    files = {
        'csv': ('data.csv', csv_data, 'text/csv'),
    }

    response_prep = requests.post(url_prep, files=files)
    response_poll_prep = requests.get("http://multi-app-service.default.svc.cluster.local:6650/poll")
    print(response_poll_prep.status_code, response_poll_prep.content)
    # Check the response
    print(response_prep.status_code)
    data = {
        'csv': ('data.csv', response_prep.content, 'text/csv'),
    }

    response_train = requests.post(url_train, files=data)
    response_poll_train = requests.get("http://multi-app-service.default.svc.cluster.local:6651/poll")
    print(response_poll_train.status_code, response_poll_train.content)
    print(response_train.status_code)

    pred = {
        'csv': ('data.csv', test_data, 'text/csv'),
        'pkl': None, #('model.pkl', response_train.content, 'application/octet-stream'),
    }
    response_pred = requests.post(url_pred, files=pred)
    response_poll_pred = requests.get("http://multi-app-service.default.svc.cluster.local:6652/poll")
    print(response_poll_pred.status_code, response_poll_pred.content)
    print(response_pred.status_code)
    if response_pred.status_code == 223:
        output_buffer = io.BytesIO(response_pred.content)  # Save the response file
        return output_buffer
    else:
        return None

@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")

@app.route("/upload_train", methods=["POST"])
def upload_train():
    global csv_data
    if "train_file" in request.files:
        train_file = request.files["train_file"]
        if train_file.filename.endswith(".csv"):
            csv_data = train_file.read()
            return "Train file uploaded!", 200
    return "Invalid Train file!", 400

@app.route("/upload_test", methods=["POST"])
def upload_test():
    global test_data
    if "test_file" in request.files:
        test_file = request.files["test_file"]
        if test_file.filename.endswith(".csv"):
            test_data = test_file.read()
            return "Test file uploaded!", 200
    return "Invalid Test file!", 400

@app.route("/run_pipeline", methods=["POST"])
def trigger_pipeline():
    if csv_data is not None and test_data is not None:
        output_buffer = run_pipeline()
        
        if output_buffer:
            return send_file(
                output_buffer,
                mimetype="text/csv",
                as_attachment=True,
                download_name=output_filename
            )
        return "Pipeline failed!", 400
    return "Files not uploaded!", 400

if __name__ == "__main__":
    app.run(debug=True, port=8080, host='0.0.0.0')
