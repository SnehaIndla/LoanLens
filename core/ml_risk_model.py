import os
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
import shap

BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_PATH = BASE_DIR / "core" / "models" / "credit_risk_model.pkl"

_MODEL_CACHE = None
_EXPLAINER_CACHE = None

def load_model_bundle():
    """
    Lazy load and cache the 5-feature model bundle and SHAP explainer.
    """
    global _MODEL_CACHE, _EXPLAINER_CACHE
    if _MODEL_CACHE is not None:
        return _MODEL_CACHE, _EXPLAINER_CACHE

    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Credit risk model artifact not found at {MODEL_PATH}. "
            f"Please run 'python scripts/train_model.py' first to train and export the model."
        )

    bundle = joblib.load(MODEL_PATH)
    _MODEL_CACHE = bundle

    model = bundle["model"]
    model_name = bundle.get("model_name", "")
    
    if model_name in ["RandomForest", "XGBoost", "LightGBM"]:
        _EXPLAINER_CACHE = shap.TreeExplainer(model)
    elif model_name == "LogisticRegression":
        _EXPLAINER_CACHE = shap.LinearExplainer(model)
    else:
        _EXPLAINER_CACHE = shap.Explainer(model)

    return _MODEL_CACHE, _EXPLAINER_CACHE


def preprocess_applicant_features(applicant_features: dict, feature_names: list, scaler):
    """
    Preprocess 5 kept features: income_annum, loan_amount, loan_term, cibil_score, bank_asset_value.
    Receives verified/reconciled features post verification.py.
    """
    feat = applicant_features.copy() if applicant_features else {}

    # Map common aliases
    if "income_annum" not in feat and "annual_income" in feat:
        feat["income_annum"] = feat["annual_income"]
    if "bank_asset_value" not in feat and "bank_assets" in feat:
        feat["bank_asset_value"] = feat["bank_assets"]

    row = {
        "income_annum": float(feat.get("income_annum", 5000000.0)),
        "loan_amount": float(feat.get("loan_amount", 15000000.0)),
        "loan_term": float(feat.get("loan_term", 10.0)),
        "cibil_score": float(feat.get("cibil_score", 650.0)),
        "bank_asset_value": float(feat.get("bank_asset_value", 0.0)),
    }

    df = pd.DataFrame([row])[feature_names]
    df_scaled = pd.DataFrame(scaler.transform(df), columns=feature_names)
    return df_scaled


def predict_approval(applicant_features: dict) -> dict:
    """
    Predict loan approval on the 5-feature schema, returns approval probability,
    inverted risk score (0-100), decision policy recommendation, and top SHAP feature drivers.
    """
    bundle, explainer = load_model_bundle()
    
    model = bundle["model"]
    scaler = bundle["scaler"]
    feature_names = bundle["feature_names"]

    df_proc = preprocess_applicant_features(applicant_features, feature_names, scaler)

    if hasattr(model, "predict_proba"):
        prob_approved = float(model.predict_proba(df_proc)[0, 1])
    else:
        prob_approved = float(model.predict(df_proc)[0])

    # Risk score direction: 0 = safest (highest approval probability), 100 = highest default risk
    risk_score = round((1.0 - prob_approved) * 100.0, 2)
    prob_approved_pct = round(prob_approved * 100.0, 2)

    # Decision Policy Thresholds
    if prob_approved >= 0.75:
        decision = "APPROVE"
    elif prob_approved <= 0.35:
        decision = "REJECT"
    else:
        decision = "MANUAL_REVIEW"

    # Compute SHAP feature drivers
    top_factors = []
    try:
        shap_vals = explainer(df_proc)
        if hasattr(shap_vals, "values"):
            vals = shap_vals.values[0]
            if len(vals.shape) > 1:
                vals = vals[:, 1]
        else:
            vals = np.array(shap_vals)[0]

        impacts = []
        for name, val in zip(feature_names, vals):
            impact_val = float(val)
            direction = "decreases_risk" if impact_val > 0 else "increases_risk"
            impacts.append({
                "feature": name,
                "shap_impact": round(impact_val, 4),
                "abs_impact": abs(impact_val),
                "direction": direction,
                "description": f"{name} {'increases approval chance' if impact_val > 0 else 'increases risk'}"
            })

        impacts.sort(key=lambda x: x["abs_impact"], reverse=True)
        top_factors = impacts
    except Exception as e:
        top_factors = [{"feature": "n/a", "shap_impact": 0.0, "direction": "unknown", "description": f"SHAP error: {e}"}]

    return {
        "decision": decision,
        "approval_probability": prob_approved,
        "approval_probability_pct": prob_approved_pct,
        "risk_score": risk_score,
        "model_name": bundle.get("model_name", "LightGBM"),
        "top_factors": top_factors
    }


if __name__ == "__main__":
    sample = {
        "income_annum": 8200000,
        "loan_amount": 30700000,
        "cibil_score": 467,
        "bank_asset_value": 7900000,
        "loan_term": 8
    }
    res = predict_approval(sample)
    print("\n========== 5-FEATURE ML PREDICTION PREVIEW ==========")
    print(f"Model: {res['model_name']}")
    print(f"Decision: {res['decision']}")
    print(f"Approval Probability: {res['approval_probability_pct']}%")
    print(f"Inverted Risk Score: {res['risk_score']} / 100")
    print("Top SHAP Factors:")
    for f in res["top_factors"]:
        print(f" - {f['feature']}: {f['shap_impact']} ({f['direction']})")
if __name__ == "__main__":
    sample = {
        "income_annum": 1890000,
        "loan_amount": 72000000,
        "cibil_score": 612,
        "bank_asset_value": 940000,
        "loan_term": 20
    }
    res = predict_approval(sample)
    print("\n========== 5-FEATURE ML PREDICTION PREVIEW ==========")
    print(f"Model: {res['model_name']}")
    print(f"Decision: {res['decision']}")
    print(f"Approval Probability: {res['approval_probability_pct']}%")
    print(f"Inverted Risk Score: {res['risk_score']} / 100")
    print("Top SHAP Factors:")
    for f in res["top_factors"]:
        print(f" - {f['feature']} ({f['val']}): {f['shap_impact']} ({f['direction']})")
