"""
Train intent classifier for kirana shop customer bot.
Uses TF-IDF with character n-grams (handles spelling mistakes) + Logistic Regression.

Run AFTER generating dataset:
    python -m backend.ml.generate_dataset
    python -m backend.ml.train
"""
import os, csv, pickle, sys
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report

# Force UTF-8 output on Windows
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = os.path.dirname(__file__)
DATASET_PATH = os.path.join(BASE_DIR, "dataset.csv")
MODEL_PATH   = os.path.join(BASE_DIR, "intent_model.pkl")


def load_dataset():
    texts, labels = [], []
    with open(DATASET_PATH, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            texts.append(row["text"])
            labels.append(row["intent"])
    return texts, labels


def build_pipeline():
    """
    TF-IDF with character n-grams:
    - char_wb (2-5): handles spelling mistakes, Tanglish, partial words
    Logistic Regression with balanced class weights.
    """
    vectorizer = TfidfVectorizer(
        analyzer="char_wb",          # character n-grams within word boundaries
        ngram_range=(2, 5),          # 2 to 5 character n-grams
        min_df=1,
        max_features=50_000,
        sublinear_tf=True,           # log(tf) smoothing
        strip_accents="unicode",
        lowercase=True,
    )
    clf = LogisticRegression(
        max_iter=1000,
        C=5.0,
        class_weight="balanced",     # handles class imbalance
        solver="lbfgs",
    )
    return Pipeline([("tfidf", vectorizer), ("clf", clf)])


def train():
    print("Loading dataset...")
    texts, labels = load_dataset()
    print(f"  Total examples: {len(texts)}")

    # Split
    X_train, X_test, y_train, y_test = train_test_split(
        texts, labels, test_size=0.15, random_state=42, stratify=labels
    )

    print(f"  Train: {len(X_train)}  Test: {len(X_test)}")

    # Build + train
    print("\nTraining pipeline (TF-IDF char n-grams + Logistic Regression)...")
    pipe = build_pipeline()
    pipe.fit(X_train, y_train)

    # Evaluate
    y_pred = pipe.predict(X_test)
    acc = (np.array(y_pred) == np.array(y_test)).mean()
    print(f"\n[PASS] Test Accuracy: {acc*100:.1f}%")

    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))

    # Cross-validation on full dataset
    print("5-fold Cross-Validation:")
    scores = cross_val_score(pipe, texts, labels, cv=5, scoring="accuracy")
    print(f"  CV Accuracy: {scores.mean()*100:.1f}% +/- {scores.std()*100:.1f}%")

    # Save model
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(pipe, f)
    print(f"\n[SAVED] Model saved to: {MODEL_PATH}")

    # Quick sanity check
    print("\n--- Sanity Check (spelling + Tanglish) ---")
    test_cases = [
        ("brinjal iruka",              "AVAILABILITY_CHECK"),
        ("do u hav tamoto",            "AVAILABILITY_CHECK"),
        ("pottato avilable",           "AVAILABILITY_CHECK"),
        ("miilk price enna",           "PRICE_ENQUIRY"),
        ("oneon evlo",                 "PRICE_ENQUIRY"),
        ("wht is prise of riice",      "PRICE_ENQUIRY"),
        ("vanakkam anna",              "GREETING"),
        ("hiii",                       "GREETING"),
        ("nandri sir",                 "THANKS"),
        ("ok thnx",                    "THANKS"),
        ("milk mosam sir",             "COMPLAINT"),
        ("paal kedaichiruku",          "COMPLAINT"),
        ("shop timing",                "OUT_OF_SCOPE"),
        ("delivery pannuveenga",       "OUT_OF_SCOPE"),
        ("5kg rice vennum",            "BULK_ORDER"),
        ("2 litr milk tharuveenga",    "BULK_ORDER"),
        ("milk and bread iruka",       "MULTIPLE_ITEMS"),
        ("tometo and onioin available","MULTIPLE_ITEMS"),
    ]
    correct = 0
    for text, expected in test_cases:
        pred = pipe.predict([text])[0]
        prob = pipe.predict_proba([text]).max()
        ok = "PASS" if pred == expected else "FAIL"
        if pred == expected:
            correct += 1
        print(f"  [{ok}] [{prob:.2f}] '{text}' -> {pred}  (expected: {expected})")

    print(f"\nSanity: {correct}/{len(test_cases)} correct")


if __name__ == "__main__":
    train()
