import psycopg
from psycopg.rows import dict_row
from config import DB_CONFIG

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


def get_connection():
    cfg = DB_CONFIG.copy()
    cfg["dbname"] = cfg.get("dbname") or cfg.get("database")

    return psycopg.connect(
        host=cfg["host"],
        port=cfg["port"],
        user=cfg["user"],
        password=cfg["password"],
        dbname=cfg["dbname"],
    )

def insert_transaction(data):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                        INSERT INTO transactions (
                            account_type, account_number, transaction_date,
                            cheque_number, description_1, description_2,
                            cad_amount, usd_amount, category
                        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s);
                        """, (
                            data.get("account_type"),
                            data.get("account_number"),
                            data.get("transaction_date"),
                            data.get("cheque_number"),
                            data.get("description_1"),
                            data.get("description_2"),
                            data.get("cad_amount"),
                            data.get("usd_amount"),
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
