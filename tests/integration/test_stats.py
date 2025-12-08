import os
import pytest
import requests

API_URL = os.getenv("API_URL", "http://127.0.0.1:5001")


def api_available() -> bool:
    try:
        res = requests.get(f"{API_URL}/stats", timeout=5)
        return res.status_code == 200
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not api_available(), reason="API not reachable at API_URL"
)


def test_stats_shape():
    res = requests.get(f"{API_URL}/stats", timeout=10)
    assert res.status_code == 200
    data = res.json()

    expected_keys = {
        "total_transactions",
        "total_cad",
        "total_usd",
        "categories",
        "duplicate_transactions",
        "duplicate_groups",
        "recent_30d_count",
        "recent_30d_total_cad",
        "avg_daily_30d",
        "monthly_trend",
        "recurring_merchants",
    }
    missing = expected_keys - set(data.keys())
    assert not missing, f"Missing keys in /stats: {missing}"


def test_classification_progress_endpoint():
    res = requests.get(f"{API_URL}/classification_progress", timeout=10)
    assert res.status_code == 200
    data = res.json()
    for key in ["running", "total", "unclassified", "classified", "percent"]:
        assert key in data


def test_stats_categories_is_list():
    res = requests.get(f"{API_URL}/stats", timeout=10)
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data.get("categories"), list)
    if data["categories"]:
        first = data["categories"][0]
        assert "category" in first and "count" in first and "total_cad" in first
