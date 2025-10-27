import math

from flask import Flask, request, jsonify
from flask_cors import CORS
from db import init_db, insert_transaction, get_connection
import threading
from classify_transactions import main as classify_transactions_main
import pandas as pd

app = Flask(__name__)
CORS(app)

def setup_db_once():
    if not getattr(app, "_db_initialized", False):
        init_db()
        app._db_initialized = True
        print("✅ Database initialized")

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
        print("First account type:", df['account_type'].iloc[0])

        inserted = 0
        for _, row in df.iterrows():
            data = row.to_dict()
            if not isinstance(data.get("transaction_date"), str) and pd.notna(data.get("transaction_date")):
                data["transaction_date"] = str(data["transaction_date"])
            insert_transaction(data)
            inserted += 1

        print(f"✅ Inserted {inserted} rows successfully.")

        # Start background classification
        threading.Thread(target=classify_transactions_main, daemon=True).start()

        return jsonify({"message": f"Uploaded {inserted} transactions successfully!"}), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/stats", methods=["GET"])
def get_stats():
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                # Overall totals
                cur.execute("""
                            SELECT
                                COUNT(*) AS total_transactions,
                                COALESCE(SUM(cad_amount), 0) AS total_cad,
                                COALESCE(SUM(usd_amount), 0) AS total_usd
                            FROM transactions;
                            """)
                total_row = cur.fetchone()

                # Per-category breakdown
                cur.execute("""
                            SELECT
                                COALESCE(category, 'Uncategorized') AS category,
                                COUNT(*) AS count,
                                ROUND(COALESCE(SUM(cad_amount), 0), 2) AS total_cad
                            FROM transactions
                            GROUP BY category
                            ORDER BY total_cad DESC;
                            """)
                category_rows = cur.fetchall()

        def safe_num(val):
            if val is None or (isinstance(val, float) and math.isnan(val)):
                return 0.0
            return round(val, 2)

        stats = {
            "total_transactions": total_row[0],
            "total_cad": safe_num(float(total_row[1] or 0)),
            "total_usd": safe_num(float(total_row[2] or 0)),
            "categories": [
                {"category": row[0], "count": row[1], "total_cad": float(row[2])}
                for row in category_rows
            ],
        }

        print("📊 Stats generated:", stats)
        return jsonify(stats)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    setup_db_once()
    app.run(port=5001, debug=True)
