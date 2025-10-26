from flask import Flask, request, jsonify
from flask_cors import CORS
from db import init_db, insert_transaction
from model import train_model, predict_category
import pandas as pd

app = Flask(__name__)
CORS(app)

def setup_db_once():
    if not getattr(app, "_db_initialized", False):
        init_db()
        app._db_initialized = True
        print("Database initialized")

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
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    try:

        df = pd.read_csv(file, index_col=False)

        print("\n===== CSV HEAD =====")
        print(df.head())
        print("Columns detected:", list(df.columns))

        required_cols = [
            "Account Type", "Account Number", "Transaction Date",
            "Cheque Number", "Description 1", "Description 2",
            "CAD$", "USD$"
        ]

        col = df["Transaction Date"]
        if pd.api.types.is_numeric_dtype(col):
            df["Transaction Date"] = pd.to_datetime(
                col,
                origin="1899-12-30",
                unit="D",
                errors="coerce"
            ).dt.date
        else:
            df["Transaction Date"] = pd.to_datetime(
                col,
                errors="coerce"
            ).dt.date

        df.rename(
            columns={
                "Account Type": "account_type",
                "Account Number": "account_number",
                "Transaction Date": "transaction_date",
                "Cheque Number": "cheque_number",
                "Description 1": "description_1",
                "Description 2": "description_2",
                "CAD$": "cad_amount",
                "USD$": "usd_amount",
            },
            inplace=True,
        )

        for c in ["cad_amount", "usd_amount"]:
            df[c] = pd.to_numeric(df[c], errors="coerce")

        df.dropna(how="all", inplace=True)
        print(df['account_type'][0])

        inserted = 0
        for _, row in df.iterrows():
            data = row.to_dict()
            if not isinstance(data.get("transaction_date"), str) and pd.notna(data.get("transaction_date")):
                data["transaction_date"] = str(data["transaction_date"])

            insert_transaction(data)
            inserted += 1

        print(f" Inserted {inserted} rows successfully.")
        return jsonify({"message": f"Uploaded {inserted} transactions successfully!"}), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(port=5001, debug=True)
