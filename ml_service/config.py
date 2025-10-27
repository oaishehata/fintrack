import os

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432"),
    "user": os.getenv("DB_USER", "omar"),
    "password": os.getenv("DB_PASSWORD", "postgres"),
    "dbname": os.getenv("DB_NAME", "expense_db"),
}


OLLAMA_CONFIG = {
    "url": "http://127.0.0.1:11434/api/generate",
    "model": "phi3:mini",
}
