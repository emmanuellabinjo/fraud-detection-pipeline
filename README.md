# 🔍 Real-Time Fraud Detection Pipeline

> A streaming machine learning pipeline that scores credit card transactions in real time, logs every prediction to PostgreSQL, and serves fraud alerts via a FastAPI REST API — simulating production fraud detection at a financial institution.

[![Python](https://img.shields.io/badge/Python-3.x-blue?logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-Live-green?logo=fastapi)](http://localhost:8000/docs)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Database-blue?logo=postgresql)](https://postgresql.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green)](LICENSE)

**[Notebook](fraud_detection.ipynb)** · **[API](api.py)**

---

## Table of contents

- [Project overview](#project-overview)
- [Key results](#key-results)
- [Architecture](#architecture)
- [Dataset](#dataset)
- [Project structure](#project-structure)
- [Methodology](#methodology)
- [API endpoints](#api-endpoints)
- [How to run locally](#how-to-run-locally)
- [Limitations and future work](#limitations-and-future-work)
- [Acknowledgements](#acknowledgements)

---

## Project overview

Most fraud detection portfolios stop at a trained model in a notebook. This project goes further — simulating how fraud detection actually works in production: transactions stream in continuously, each one is scored in real time, predictions are logged to a PostgreSQL database with a full audit trail, and a FastAPI REST API serves live fraud alerts and statistics.

The pipeline demonstrates systems thinking that separates production-aware data scientists from notebook-bound ones.

---

## Key results

| Metric | Value |
|---|---|
| Dataset | 284,807 real credit card transactions |
| Fraud cases | 492 (0.17% — severely imbalanced) |
| Model | XGBoost with SMOTE oversampling |
| AUC-ROC | 0.9760 |
| Recall (fraud class) | 0.87 |
| F1 (fraud class) | 0.49 |
| Fraud caught in test set | 85 of 98 cases |
| Fraud missed | 13 cases |
| False positives | 161 genuine transactions flagged |

> Recall of 0.87 means the model catches 87% of all actual fraud. AUC-ROC of 0.976 reflects strong discrimination ability across all decision thresholds. F1 of 0.49 reflects the precision-recall trade-off inherent in severely imbalanced fraud detection — optimising for recall necessarily reduces precision.

---

## Architecture

```
Streaming Transaction Source (simulated)
             ↓
    score_transaction()
             ↓
    XGBoost Model (fraud_model.joblib)
             ↓
    Fraud Probability Score
             ↓
    PostgreSQL — fraud_predictions table
             ↓
    FastAPI REST API
        ├── POST /score     — score a new transaction
        ├── GET  /alerts    — retrieve flagged transactions
        └── GET  /stats     — summary statistics
```

> In a production environment, the streaming source would be replaced with Apache Kafka consuming from a payment processing system. The simulation demonstrates the same scoring and logging logic.

---

## Dataset

| Dataset | Source | Rows | Fraud cases | Licence |
|---|---|---|---|---|
| Credit Card Fraud Detection | [Kaggle — ULB Machine Learning Group](https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud) | 284,807 | 492 (0.17%) | Public |

Features V1–V28 are PCA-transformed for privacy. `Time`, `Amount`, and `Class` are the only raw columns.

The dataset is excluded from this repository. Download `creditcard.csv` from Kaggle and place it in the project root.

---

## Project structure

```
fraud-detection-pipeline/
│
├── fraud_detection.ipynb   # Model training, evaluation, streaming simulation
├── api.py                  # FastAPI REST API with PostgreSQL integration
├── .env                    # Database credentials (excluded from Git)
├── .gitignore
└── README.md
```

> The trained model files (`fraud_model.joblib`, `fraud_scaler.joblib`) and dataset (`creditcard.csv`) are excluded from the repository. Run the notebook to generate them locally.

---

## Methodology

### 1. Class imbalance — SMOTE oversampling

With only 492 fraud cases out of 284,807 transactions (0.17%), a naive model predicting "genuine" for every transaction would achieve 99.83% accuracy while being completely useless. Two strategies were applied:

- **SMOTE (Synthetic Minority Oversampling Technique)**: generates synthetic fraud samples by interpolating between existing minority class examples, applied only to the training set to prevent data leakage
- **Business-relevant metrics**: F1, precision, recall, and AUC-ROC used instead of accuracy — recall on the fraud class is the primary optimisation target since false negatives (missed fraud) are more costly than false positives (unnecessary customer friction)

### 2. Model training

An 80/20 stratified train/test split was applied before SMOTE to prevent synthetic samples contaminating the test set. StandardScaler was applied to `Amount` and `Time` — fit on training data only, then applied to test data.

XGBoost was selected over Random Forest for its superior handling of imbalanced data and faster inference speed, which matters in a real-time scoring context.

### 3. Streaming pipeline

The streaming simulation processes transactions sequentially with a configurable delay, calling `score_transaction()` for each. Each call:
1. Scales the incoming transaction features
2. Computes a fraud probability using the trained model
3. Applies a 0.5 decision threshold (configurable)
4. Logs the result to PostgreSQL via SQLAlchemy

### 4. PostgreSQL audit trail

Every scored transaction is logged to the `fraud_predictions` table with full metadata: transaction ID, amount, fraud probability, binary prediction, flag status, and timestamp. This creates a complete audit trail — a regulatory requirement in real financial services.

### 5. FastAPI REST API

Three endpoints expose the pipeline's outputs:
- `POST /score` — accepts a transaction JSON payload, scores it, logs to database, returns decision
- `GET /alerts` — returns the top 20 highest-probability flagged transactions
- `GET /stats` — returns aggregate statistics across all scored transactions

Interactive documentation is auto-generated at `http://localhost:8000/docs`.

---

## API endpoints

### POST /score
Score a new transaction and receive an instant fraud decision.

```json
// Request body
{
  "Time": 12345.0,
  "Amount": 49.99,
  "V1": -1.36, "V2": -0.07, ...
}

// Response
{
  "transaction_id": "a3f2b1c4",
  "fraud_probability": 0.0023,
  "flagged_as_fraud": false,
  "decision": "APPROVE"
}
```

### GET /alerts
```json
{
  "total_alerts": 9,
  "alerts": [
    {
      "transaction_id": "TXN_0023",
      "amount": 0.89,
      "fraud_probability": 0.9871,
      "created_at": "2025-07-01T14:23:11"
    }
  ]
}
```

### GET /stats
```json
{
  "total": 101,
  "flagged": 9,
  "avg_probability": 0.0901
}
```

---

## How to run locally

### Prerequisites

- Python 3.10+
- Anaconda recommended
- PostgreSQL installed and running

### 1. Clone the repo

```bash
git clone https://github.com/emmanuellabinjo/fraud-detection-pipeline.git
cd fraud-detection-pipeline
```

### 2. Install dependencies

```bash
pip install fastapi uvicorn sqlalchemy psycopg2-binary kafka-python imbalanced-learn xgboost scikit-learn pandas numpy matplotlib seaborn joblib
```

### 3. Download the dataset

Go to [Kaggle Credit Card Fraud Detection](https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud) and download `creditcard.csv`. Place it in the project root.

### 4. Set up PostgreSQL

Create the database and table:

```sql
CREATE DATABASE fraud_detection;

\c fraud_detection

CREATE TABLE fraud_predictions (
    id SERIAL PRIMARY KEY,
    transaction_id VARCHAR(50),
    amount FLOAT,
    time_seconds FLOAT,
    fraud_probability FLOAT,
    prediction INTEGER,
    flagged_as_fraud BOOLEAN,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 5. Configure environment

Create a `.env` file in the project root:

```
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/fraud_detection
```

### 6. Run the notebook

Open `fraud_detection.ipynb` and run all cells to train the model and generate `fraud_model.joblib` and `fraud_scaler.joblib`.

### 7. Start the API

```bash
uvicorn api:app --reload
```

Open `http://localhost:8000/docs` for interactive API documentation.

---

## Limitations and future work

### Current limitations

- **Simulated streaming**: The pipeline simulates real-time transaction ingestion using Python threading. A production deployment would use Apache Kafka for distributed, fault-tolerant message queuing.
- **Decision threshold fixed at 0.5**: In production, this threshold would be a business decision calibrated against the cost of false negatives vs false positives, likely set lower than 0.5 to prioritise recall.
- **No model monitoring**: There is no drift detection or automated retraining trigger. In production, transaction patterns change over time as fraudsters adapt — the model would need regular retraining.
- **Anonymised features**: V1–V28 are PCA-transformed, making feature interpretation and domain-specific feature engineering impossible on this dataset.

### Planned improvements

- [ ] Replace streaming simulation with Apache Kafka via Docker Compose
- [ ] Add a Streamlit dashboard showing real-time fraud alerts and statistics
- [ ] Implement model drift monitoring using Evidently AI
- [ ] Add a threshold calibration endpoint allowing the decision boundary to be adjusted at runtime
- [ ] Containerise the full stack with Docker Compose (API + PostgreSQL)
- [ ] Add automated quarterly retraining pipeline

---

## Acknowledgements

- [ULB Machine Learning Group](https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud) for the Credit Card Fraud Detection dataset
- [FastAPI](https://fastapi.tiangolo.com/) for the REST API framework
- [imbalanced-learn](https://imbalanced-learn.org/) for the SMOTE implementation
- [XGBoost](https://xgboost.readthedocs.io/) for the gradient boosting model

---

## Licence

This project is licensed under the MIT Licence.

---

*Built as part of a data science portfolio. Questions or suggestions? Open an issue or connect on [LinkedIn](https://linkedin.com/in/emmanuel-labinjo).*