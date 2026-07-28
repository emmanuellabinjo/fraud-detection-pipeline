from fastapi import FastAPI
from pydantic import BaseModel
import joblib
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
import uuid
import os

app = FastAPI(title="Fraud Detection API")

model = joblib.load("fraud_model.joblib")
scaler = joblib.load("fraud_scaler.joblib")
engine = create_engine(os.environ.get("DATABASE_URL", "postgresql://postgres:password@localhost:5432/fraud_detection"))

class Transaction(BaseModel):
    Time: float
    Amount: float
    V1: float; V2: float; V3: float; V4: float; V5: float
    V6: float; V7: float; V8: float; V9: float; V10: float
    V11: float; V12: float; V13: float; V14: float; V15: float
    V16: float; V17: float; V18: float; V19: float; V20: float
    V21: float; V22: float; V23: float; V24: float; V25: float
    V26: float; V27: float; V28: float

@app.post("/score")
def score_transaction(transaction: Transaction):
    features = pd.DataFrame([transaction.dict()])
    features[["Amount", "Time"]] = scaler.transform(features[["Amount", "Time"]])
    
    fraud_prob = float(model.predict_proba(features)[0][1])
    flagged = fraud_prob > 0.5
    transaction_id = str(uuid.uuid4())[:8]
    
    with engine.connect() as conn:
        conn.execute(text("""
            INSERT INTO fraud_predictions 
            (transaction_id, amount, time_seconds, fraud_probability, prediction, flagged_as_fraud)
            VALUES (:tid, :amount, :time, :prob, :pred, :flagged)
        """), {
            "tid": transaction_id,
            "amount": transaction.Amount,
            "time": transaction.Time,
            "prob": fraud_prob,
            "pred": int(flagged),
            "flagged": bool(flagged)
        })
        conn.commit()
    
    return {
        "transaction_id": transaction_id,
        "fraud_probability": round(fraud_prob, 4),
        "flagged_as_fraud": flagged,
        "decision": "BLOCK" if flagged else "APPROVE"
    }

@app.get("/alerts")
def get_alerts():
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT transaction_id, amount, fraud_probability, created_at
            FROM fraud_predictions
            WHERE flagged_as_fraud = TRUE
            ORDER BY fraud_probability DESC
            LIMIT 20
        """))
        alerts = [dict(row._mapping) for row in result]
    return {"total_alerts": len(alerts), "alerts": alerts}

@app.get("/stats")
def get_stats():
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN flagged_as_fraud THEN 1 ELSE 0 END) as flagged,
                ROUND(AVG(fraud_probability)::numeric, 4) as avg_probability
            FROM fraud_predictions
        """))
        stats = dict(result.fetchone()._mapping)
    return stats