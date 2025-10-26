import os
import pandas as pd
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline, FeatureUnion
from sklearn.compose import ColumnTransformer
from xgboost import XGBClassifier
from config import MODEL_PATH
from db import fetch_training_data

def train_model():
    data = fetch_training_data()
    if not data:
        print("⚠️ No labeled training data found.")
        return

    df = pd.DataFrame(data)
    df["text"] = df["description_1"].fillna('') + " " + df["description_2"].fillna('')
    X_text = df["text"]
    X_num = df[["cad_amount"]]
    y = df["category"]

    # Combine TF-IDF and numeric features
    text_vectorizer = TfidfVectorizer(max_features=1000)
    scaler = StandardScaler()

    # Model pipeline
    model = Pipeline([
        ("features", FeatureUnion([
            ("text", Pipeline([("tfidf", text_vectorizer)])),
        ])),
        ("xgb", XGBClassifier(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            eval_metric="mlogloss",
            use_label_encoder=False
        ))
    ])

    model.fit(X_text, y)

    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    print(f"✅ Model trained and saved at {MODEL_PATH}")

def predict_category(transactions):
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError("Model not trained yet.")

    model = joblib.load(MODEL_PATH)
    df = pd.DataFrame(transactions)
    df["text"] = df["Description 1"].fillna('') + " " + df["Description 2"].fillna('')
    predictions = model.predict(df["text"])
    for t, p in zip(transactions, predictions):
        t["category"] = str(p)
    return transactions
