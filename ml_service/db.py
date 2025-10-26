import psycopg
from psycopg.rows import dict_row
from config import DB_CONFIG


def get_connection():
    return psycopg.connect(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        dbname=DB_CONFIG["database"]
    )


def init_db():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                        CREATE TABLE IF NOT EXISTS transactions (
                                                                    id SERIAL PRIMARY KEY,
                                                                    account_type TEXT,
                                                                    account_number TEXT,
                                                                    transaction_date DATE,
                                                                    cheque_number TEXT,
                                                                    description_1 TEXT,
                                                                    description_2 TEXT,
                                                                    cad_amount NUMERIC,
                                                                    usd_amount NUMERIC,
                                                                    category TEXT
                        );
                        """)
    print("✅ Database initialized")


def insert_transaction(data):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                        INSERT INTO transactions (
                            account_type, account_number, transaction_date,
                            cheque_number, description_1, description_2,
                            cad_amount, usd_amount, category
                        )
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s);
                        """, (
                            data.get("Account Type"),
                            data.get("Account Number"),
                            data.get("Transaction Date"),
                            data.get("Cheque Number"),
                            data.get("Description 1"),
                            data.get("Description 2"),
                            data.get("CAD$"),
                            data.get("USD$"),
                            data.get("category")
                        ))

def fetch_training_data():
    with psycopg.connect(
            host=DB_CONFIG["host"],
            port=DB_CONFIG["port"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            dbname=DB_CONFIG["database"],
            row_factory=dict_row
    ) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                        SELECT description_1, description_2, cad_amount, category
                        FROM transactions
                        WHERE category IS NOT NULL;
                        """)
            return cur.fetchall()
