from flask import Flask, render_template, request, jsonify
import json
import os

app = Flask(__name__)

DATA_FILE = "data.json"

# Create file if not exists
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump([], f)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/save", methods=["POST"])
def save_session():
    data = request.json

    with open(DATA_FILE, "r") as f:
        sessions = json.load(f)

    sessions.append(data)

    with open(DATA_FILE, "w") as f:
        json.dump(sessions, f, indent=4)

    return jsonify({"message": "Session Saved"})

@app.route("/history")
def history():
    with open(DATA_FILE, "r") as f:
        sessions = json.load(f)
    return jsonify(sessions)

if __name__ == "__main__":
    app.run(debug=True)
