from ml_service import classify_transactions


def test_clean_merchant_name_basic():
    assert (
        classify_transactions.clean_merchant_name("STARBUCKS #123 YUL")
        == "starbucks yul"
    )
    assert classify_transactions.clean_merchant_name("Netflix CA*12345") == "netflix ca"
    assert classify_transactions.clean_merchant_name("") == "unknown"
    assert classify_transactions.clean_merchant_name(None) == "unknown"  # type: ignore[arg-type]


def test_classify_with_ollama_mocked(monkeypatch):
    payload = {"response": "groceries"}

    def fake_post(url, json=None, timeout=90):
        class Resp:
            def raise_for_status(self):  # pragma: no cover - happy path
                return None

            def json(self):
                return payload

        return Resp()

    monkeypatch.setattr(
        classify_transactions,
        "requests",
        type("R", (), {"post": fake_post, "get": lambda *a, **k: None}),
    )
    monkeypatch.setattr(classify_transactions, "ensure_ollama_running", lambda: True)

    category = classify_transactions.classify_with_ollama("Grocery Store - Milk")
    assert category == "Groceries"
