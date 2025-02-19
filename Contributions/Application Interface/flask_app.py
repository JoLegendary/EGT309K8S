from flask import Flask, send_file
import io
import time

app = Flask(__name__)

t = time.time()

@app.route("/upload", methods=["POST"])
def a():
    global t
    fakefile = io.BytesIO()
    fakefile.write(b"GAGAG OLALALA")
    fakefile.seek(0)
    t = time.time()
    time.sleep(10)
    return send_file(fakefile, mimetype='text/csv', as_attachment=True, download_name="processed_output.csv"), 221

@app.route("/poll", methods=["GET"])
def aa():
    what = {"status": "1-0:Test", "percentage": min((time.time() - t)/10*100,100)}
    print(what)
    return what, 211

app.run(port=3000)
