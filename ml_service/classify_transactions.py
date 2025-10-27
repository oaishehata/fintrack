import psycopg
import requests
import json
import os
import re
from time import sleep
from config import DB_CONFIG, OLLAMA_CONFIG

CACHE_FILE = "category_cache.json"

# ---------------- CACHE UTILS ----------------

def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    return {}

def save_cache(cache):
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2)

# ---------------- OLLAMA CLASSIFIER ----------------

def classify_with_ollama(description: str) -> str:
    """Ask Ollama to categorize the transaction"""
    prompt = f"""
    Classify this transaction into one of these categories:
    Income, Transfers, Food & Drink, Groceries, Shopping, Transport,
    Bills & Utilities, Entertainment, Travel, or Other.
    Transaction: {description}
    Respond with only the category name.
    """
    try:
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
        return category or "Other"
    except Exception as e:
        print("❌ Ollama error:", e)
        return "Other"

# ---------------- HELPERS ----------------

def clean_merchant_name(desc: str) -> str:
    """
    Extract a simple merchant key for caching.
    Example: 'TIM HORTONS #2255' → 'tim hortons'
    """
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
    print("🚀 Connecting to Postgres...")
    conn = psycopg.connect(**DB_CONFIG)
    cache = load_cache()

    with conn.cursor() as cur:
        cur.execute("""
                    SELECT id, description_1, description_2
                    FROM transactions
                    WHERE category IS NULL
                    ORDER BY id;
                    """)
        rows = cur.fetchall()

    print(f"🔍 Found {len(rows)} unclassified transactions.")
    for (txn_id, desc1, desc2) in rows:
        text = f"{desc1 or ''} {desc2 or ''}".strip()
        merchant_key = clean_merchant_name(desc1 or desc2 or "")
        print(f"\n🧾 ID {txn_id} | Merchant: {merchant_key}")

        # --- cache hit ---
        if merchant_key in cache:
            category = cache[merchant_key]
            print(f"⚡ Using cached category: {category}")
        else:
            # --- new classification ---
            category = classify_with_ollama(text)
            cache[merchant_key] = category
            print(f"🤖 LLM classified as: {category}")
            save_cache(cache)  # save after each new classification
            sleep(1.5)  # prevent rapid API calls

        update_transaction_category(txn_id, category, conn)

    print("\n✅ Done. Cache saved and database updated.")
    conn.close()

if __name__ == "__main__":
    main()
