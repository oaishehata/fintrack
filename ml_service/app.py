import math

from flask import Flask, request, jsonify
from flask_cors import CORS
from db import init_db, insert_transaction, get_connection
import threading
from classify_transactions import main as classify_transactions_main
import pandas as pd

app = Flask(__name__)
CORS(app)
classification_lock = threading.Lock()
classification_running = False


def setup_db_once():
    if not getattr(app, "_db_initialized", False):
        init_db()
        app._db_initialized = True
        print("Database initialized")


def run_classification_background():
    global classification_running
    if classification_lock.locked() or classification_running:
        print("ℹ️ Classification already running; skipping duplicate start.")
        return

    def _runner():
        global classification_running
        with classification_lock:
            classification_running = True
            try:
                classify_transactions_main()
            finally:
                classification_running = False

    threading.Thread(target=_runner, daemon=True).start()


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

        col = df["Transaction Date"]
        if pd.api.types.is_numeric_dtype(col):
            df["Transaction Date"] = pd.to_datetime(
                col, origin="1899-12-30", unit="D", errors="coerce"
            ).dt.date
        else:
            df["Transaction Date"] = pd.to_datetime(col, errors="coerce").dt.date

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
        print("First account type:", df["account_type"].iloc[0])

        inserted = 0
        for _, row in df.iterrows():
            data = row.to_dict()
            if not isinstance(data.get("transaction_date"), str) and pd.notna(
                data.get("transaction_date")
            ):
                data["transaction_date"] = str(data["transaction_date"])
            insert_transaction(data)
            inserted += 1

        print(f"Inserted {inserted} rows successfully.")

        # Start background classification
        run_classification_background()

        return (
            jsonify({"message": f"Uploaded {inserted} transactions successfully!"}),
            200,
        )

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
                cur.execute(
                    """
                            SELECT
                                COUNT(*) AS total_transactions,
                                COALESCE(SUM(cad_amount), 0) AS total_cad,
                                COALESCE(SUM(usd_amount), 0) AS total_usd
                            FROM transactions;
                            """
                )
                total_row = cur.fetchone()

                # Per-category breakdown
                cur.execute(
                    """
                            SELECT
                                COALESCE(category, 'Uncategorized') AS category,
                                COUNT(*) AS count,
                                ROUND(COALESCE(SUM(cad_amount), 0), 2) AS total_cad
                            FROM transactions
                            GROUP BY category
                            ORDER BY total_cad DESC;
                            """
                )
                category_rows = cur.fetchall()

                # Duplicate transaction detection by matching on key identifying fields
                cur.execute(
                    """
                            WITH dupes AS (
                                SELECT COUNT(*) AS cnt
                                FROM transactions
                                GROUP BY
                                    account_number,
                                    transaction_date,
                                    cheque_number,
                                    description_1,
                                    description_2,
                                    cad_amount,
                                    usd_amount
                                HAVING COUNT(*) > 1
                            )
                            SELECT
                                COALESCE(SUM(cnt - 1), 0) AS duplicate_transactions,
                                COUNT(*) AS duplicate_groups
                            FROM dupes;
                            """
                )
                dupes_row = cur.fetchone()

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
            "duplicate_transactions": int(dupes_row[0] or 0),
            "duplicate_groups": int(dupes_row[1] or 0),
        }

        print("Stats generated:", stats)
        return jsonify(stats)

    except Exception as e:
        import traceback

        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/classification_progress", methods=["GET"])
def classification_progress():
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM transactions;")
                total = cur.fetchone()[0]
                cur.execute("SELECT COUNT(*) FROM transactions WHERE category IS NULL;")
                unclassified = cur.fetchone()[0]

        classified = max(total - unclassified, 0)
        percent = round((classified / total) * 100, 1) if total else 0.0

        return jsonify(
            {
                "running": classification_running,
                "total": total,
                "unclassified": unclassified,
                "classified": classified,
                "percent": percent,
            }
        )
    except Exception as e:
        import traceback

        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/reset", methods=["POST"])
def reset_db():
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("TRUNCATE TABLE transactions;")
        print("Transactions table truncated.")
        return jsonify({"message": "Database reset: all transactions removed."})
    except Exception as e:
        import traceback

        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/classify", methods=["POST"])
def classify_now():
    try:
        if classification_lock.locked() or classification_running:
            return jsonify({"message": "Classification already running."})

        run_classification_background()
        return jsonify({"message": "Classification started in background."})
    except Exception as e:
        import traceback

        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    setup_db_once()
    app.run(port=5001, debug=True)
