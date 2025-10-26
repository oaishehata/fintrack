from flask import Flask, request, jsonify
from db import init_db, insert_transaction
from model import train_model, predict_category

app = Flask(__name__)

# ✅ Initialize DB at startup
init_db()

@app.route("/add", methods=["POST"])
def add_transaction():
    data = request.json
    insert_transaction(data)
    return jsonify({"message": "Transaction added."})

@app.route("/train", methods=["POST"])
def train():
    train_model()
    return jsonify({"message": "Model trained successfully."})

@app.route("/predict", methods=["POST"])
def predict():
    transactions = request.json.get("transactions", [])
    results = predict_category(transactions)
    return jsonify(results)

@app.route("/ping")
def ping():
    return "ML service running ✅"

if __name__ == "__main__":
    app.run(port=5001, debug=True)
