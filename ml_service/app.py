from flask import Flask, request, jsonify
from db import init_db, insert_transaction
from model import train_model, predict_category
import pandas as pd

app = Flask(__name__)
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

@app.route("/upload_csv", methods=["POST"])
def upload_csv():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    try:
        df = pd.read_csv(file)

        required_cols = ["Account Type", "Account Number", "Transaction Date",
                         "Cheque Number", "Description 1", "Description 2", "CAD$", "USD$"]
        if not all(col in df.columns for col in required_cols):
            return jsonify({"error": "Invalid CSV format"}), 400

        for _, row in df.iterrows():
            insert_transaction(row.to_dict())

        return jsonify({"message": f"Uploaded {len(df)} transactions successfully!"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/ping")
def ping():
    return "ML service running ✅"

if __name__ == "__main__":
    app.run(port=5001, debug=True)
