"""Train a build-failure predictor and save it to ml/model.pkl."""
import pickle

import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, roc_auc_score
from sklearn.model_selection import train_test_split

FEATURES = ["files_changed", "lines_changed", "touched_core", "dep_change",
            "test_changed", "hour", "prev_failed"]

df = pd.read_csv("ml/build_history.csv")
X_train, X_test, y_train, y_test = train_test_split(
    df[FEATURES], df["failed"], test_size=0.25, random_state=7, stratify=df["failed"])

model = LogisticRegression(max_iter=1000, class_weight="balanced")
model.fit(X_train, y_train)

pred = model.predict(X_test)
proba = model.predict_proba(X_test)[:, 1]
print(f"accuracy: {accuracy_score(y_test, pred):.3f}")
print(f"roc_auc : {roc_auc_score(y_test, proba):.3f}")
print(classification_report(y_test, pred, digits=3))
print("coefficients:")
for name, coef in sorted(zip(FEATURES, model.coef_[0]), key=lambda t: -abs(t[1])):
    print(f"  {name:<14} {coef:+.3f}")

with open("ml/model.pkl", "wb") as f:
    pickle.dump({"model": model, "features": FEATURES}, f)
