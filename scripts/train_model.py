import os
import sys
import json
import joblib
import pandas as pd
import numpy as np
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix
)
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
import shap

# ==========================================
# 1. PATHS & DIRECTORIES
# ==========================================
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "data" / "loan_dataset" / "loan_approval_dataset.csv"
MODEL_DIR = BASE_DIR / "core" / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

MODEL_FILE = MODEL_DIR / "credit_risk_model.pkl"
METRICS_FILE = MODEL_DIR / "model_metrics.json"

print(f"Loading dataset from: {DATA_PATH}")
df = pd.read_csv(DATA_PATH)

# ==========================================
# 2. EDA & 5-FEATURE PREPROCESSING
# ==========================================
df.columns = df.columns.str.strip()

for col in df.select_dtypes(include=["object"]).columns:
    df[col] = df[col].astype(str).str.strip()

print("\n" + "=" * 60)
print("EXPLORATORY DATA ANALYSIS (5-FEATURE REDUCED SET)")
print("=" * 60)
print(f"Dataset Shape: {df.shape[0]} rows, {df.shape[1]} columns")
print("\nTarget Class Distribution ('loan_status'):")
print(df["loan_status"].value_counts(normalize=True).round(4) * 100)

# Binary target encoding: Approved -> 1, Rejected -> 0
y = (df["loan_status"] == "Approved").astype(int)

# 5 Kept Features Selection
KEPT_FEATURES = [
    "income_annum",
    "loan_amount",
    "loan_term",
    "cibil_score",
    "bank_asset_value"
]

X = df[KEPT_FEATURES].copy()
print(f"\nTraining Feature Matrix ({X.shape[1]} features): {list(X.columns)}")

# ==========================================
# 3. TRAIN / TEST SPLIT & SCALING
# ==========================================
X_train_raw, X_test_raw, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

scaler = StandardScaler()
X_train = pd.DataFrame(scaler.fit_transform(X_train_raw), columns=KEPT_FEATURES)
X_test = pd.DataFrame(scaler.transform(X_test_raw), columns=KEPT_FEATURES)

# ==========================================
# 4. BENCHMARKING CANDIDATE MODELS
# ==========================================
print("\n" + "=" * 60)
print("BENCHMARKING MODELS ON 5-FEATURE SET")
print("=" * 60)

candidate_models = {
    "LogisticRegression": LogisticRegression(class_weight="balanced", random_state=42, max_iter=1000),
    "RandomForest": RandomForestClassifier(n_estimators=100, class_weight="balanced", random_state=42),
    "XGBoost": XGBClassifier(n_estimators=100, learning_rate=0.1, random_state=42, eval_metric="logloss"),
    "LightGBM": LGBMClassifier(n_estimators=100, learning_rate=0.1, random_state=42, verbose=-1)
}

results = {}
best_score = -1.0
best_model_name = None
best_model = None

for name, model in candidate_models.items():
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1] if hasattr(model, "predict_proba") else y_pred
    
    acc = float(accuracy_score(y_test, y_pred))
    prec = float(precision_score(y_test, y_pred))
    rec = float(recall_score(y_test, y_pred))
    f1 = float(f1_score(y_test, y_pred))
    roc_auc = float(roc_auc_score(y_test, y_proba))
    cm = confusion_matrix(y_test, y_pred).tolist()
    
    metrics = {
        "accuracy": round(acc, 4),
        "precision": round(prec, 4),
        "recall": round(rec, 4),
        "f1_score": round(f1, 4),
        "roc_auc": round(roc_auc, 4),
        "confusion_matrix": cm
    }
    results[name] = metrics
    
    print(f"\n--- {name} ---")
    print(f"Accuracy:  {acc:.4f}")
    print(f"Precision: {prec:.4f}")
    print(f"Recall:    {rec:.4f}")
    print(f"F1 Score:  {f1:.4f}")
    print(f"ROC-AUC:   {roc_auc:.4f}")
    print(f"Confusion Matrix: {cm}")
    
    score_metric = (roc_auc + f1) / 2.0
    if score_metric > best_score:
        best_score = score_metric
        best_model_name = name
        best_model = model

print(f"\n🏆 BEST MODEL SELECTED: {best_model_name} (Score: {best_score:.4f})")

# ==========================================
# 5. DYNAMIC SHAP EXPLAINER
# ==========================================
print("\nInitializing SHAP Explainer...")
if best_model_name in ["RandomForest", "XGBoost", "LightGBM"]:
    explainer_type = "TreeExplainer"
    explainer = shap.TreeExplainer(best_model)
elif best_model_name == "LogisticRegression":
    explainer_type = "LinearExplainer"
    explainer = shap.LinearExplainer(best_model, X_train)
else:
    explainer_type = "Explainer"
    explainer = shap.Explainer(best_model, X_train)

shap_values = explainer(X_test.iloc[:10])
print(f"SHAP Explainer ({explainer_type}) initialized successfully.")

# ==========================================
# 6. EXPORT MODEL BUNDLE & METRICS
# ==========================================
bundle = {
    "model": best_model,
    "scaler": scaler,
    "feature_names": KEPT_FEATURES,
    "numeric_cols": KEPT_FEATURES,
    "model_name": best_model_name,
    "explainer_type": explainer_type,
    "best_metrics": results[best_model_name]
}

joblib.dump(bundle, MODEL_FILE)
print(f"Saved model bundle to: {MODEL_FILE}")

with open(METRICS_FILE, "w") as f:
    json.dump({"best_model": best_model_name, "kept_features": KEPT_FEATURES, "results": results}, f, indent=2)

print(f"Saved evaluation metrics to: {METRICS_FILE}")
print("\n5-Feature Model Retraining Completed Successfully!")
