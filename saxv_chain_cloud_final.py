from flask import Flask, request, jsonify
import json
import os

app = Flask(__name__)

LEDGER_FILE = "ledger.json"

# Load ledger jika ada
if os.path.exists(LEDGER_FILE):
    with open(LEDGER_FILE, "r") as f:
        blockchain = json.load(f)
else:
    blockchain = {"chain": []}

@app.route("/upload_snapshot", methods=["POST"])
def upload_snapshot():
    global blockchain
    data = request.get_json()
    if "chain" in data:
        blockchain = data
        with open(LEDGER_FILE, "w") as f:
            json.dump(blockchain, f, indent=4)
        return jsonify({"status": "success"}), 200
    return jsonify({"status": "failed"}), 400

@app.route("/ledger", methods=["GET"])
def get_ledger():
    return jsonify(blockchain)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)