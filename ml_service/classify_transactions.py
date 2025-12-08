import psycopg
import requests
import json
import os
import re
import subprocess
import time
from time import sleep
from config import DB_CONFIG, OLLAMA_CONFIG

CACHE_FILE = "category_cache.json"
OLLAMA_START_GRACE_SECONDS = 5
ollama_started = False


def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    return {}


def save_cache(cache):
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2)


def ensure_ollama_running():
    """Verify Ollama is reachable; if not, try to start it locally once."""
    global ollama_started
    url = OLLAMA_CONFIG["url"].rstrip("/") + "/tags"
    try:
        requests.get(url, timeout=2)
        return True
    except Exception:
        pass

    if ollama_started:
        return False

    try:
        print("Starting Ollama server...")
        subprocess.Popen(
            ["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        ollama_started = True
        time.sleep(OLLAMA_START_GRACE_SECONDS)
        requests.get(url, timeout=5)
        print("Ollama is reachable.")
        return True
    except Exception as e:
        print("Could not start or reach Ollama:", e)
        return False


def classify_with_ollama(description: str) -> str:
    prompt = f"""
    Classify this transaction into one of these categories:
    Income, Transfers, Food & Drink, Groceries, Shopping, Transport,
    Bills & Utilities, Entertainment, Travel, or Other.
    Transaction: {description}
    Respond with ONLY the category name (exactly as listed) — no reasoning or explanation.
    """

    try:
        if not ensure_ollama_running():
            return "Other"

        res = requests.post(
            OLLAMA_CONFIG["url"],
            json={
                "model": OLLAMA_CONFIG["model"],
                "prompt": prompt.strip(),
                "stream": False,
            },
            timeout=90,
        )
        res.raise_for_status()
        category = res.json().get("response", "").strip()

        category = category.split("\n")[0].strip(" '\"")
        category = category.title()

        valid_categories = {
            "Income",
            "Transfers",
            "Food & Drink",
            "Groceries",
            "Shopping",
            "Transport",
            "Bills & Utilities",
            "Entertainment",
            "Travel",
            "Other",
        }

        if category not in valid_categories or len(category) > 18:
            category = "Other"

        return category

    except Exception as e:
        print("Ollama error:", e)
        return "Other"


def clean_merchant_name(desc: str) -> str:
    desc = (desc or "").lower()
    desc = re.sub(r"[^a-z\s]", "", desc)
    words = desc.split()
    return " ".join(words[:2]) if words else "unknown"


def update_transaction_category(txn_id: int, category: str, conn):
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE transactions SET category = %s WHERE id = %s;",
            (category, txn_id),
        )
    conn.commit()


# ---------------- MAIN ----------------


def main():
    print("Connecting to Postgres...")
    conn = psycopg.connect(**DB_CONFIG)
    cache = load_cache()

    with conn.cursor() as cur:
        cur.execute(
            """
                    SELECT id, description_1, description_2
                    FROM transactions
                    WHERE category IS NULL
                    ORDER BY id;
                    """
        )
        rows = cur.fetchall()

    print(f"Found {len(rows)} unclassified transactions.")
    for txn_id, desc1, desc2 in rows:
        text = f"{desc1 or ''} {desc2 or ''}".strip()
        merchant_key = clean_merchant_name(desc1 or desc2 or "")
        print(f"\nID {txn_id} | Merchant: {merchant_key}")

        if merchant_key in cache:
            category = cache[merchant_key]
            print(f"Using cached category: {category}")
        else:
            category = classify_with_ollama(text)
            cache[merchant_key] = category
            print(f"LLM classified as: {category}")
            save_cache(cache)
            sleep(1.5)

        update_transaction_category(txn_id, category, conn)

    print("\nDone. Cache saved and database updated.")
    conn.close()


if __name__ == "__main__":
    main()
