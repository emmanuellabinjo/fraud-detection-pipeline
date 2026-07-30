-- ============================================
-- Fraud Detection Pipeline — SQL Queries
-- ============================================

-- 1. Create the predictions audit trail table
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

-- 2. Log a scored transaction (parameterised in Python via SQLAlchemy)
INSERT INTO fraud_predictions 
    (transaction_id, amount, time_seconds, fraud_probability, prediction, flagged_as_fraud)
VALUES 
    (:tid, :amount, :time, :prob, :pred, :flagged);

-- 3. Verify connection and total row count
SELECT COUNT(*) FROM fraud_predictions;

-- 4. Retrieve top 20 fraud alerts ordered by probability
SELECT 
    transaction_id,
    ROUND(amount::numeric, 2) AS amount,
    ROUND(fraud_probability::numeric, 4) AS fraud_probability,
    created_at
FROM fraud_predictions
WHERE flagged_as_fraud = TRUE
ORDER BY fraud_probability DESC
LIMIT 20;

-- 5. Aggregate summary statistics (powers the /stats API endpoint)
SELECT 
    COUNT(*) AS total_transactions,
    SUM(CASE WHEN flagged_as_fraud THEN 1 ELSE 0 END) AS total_flagged,
    ROUND(AVG(fraud_probability)::numeric, 4) AS avg_fraud_probability
FROM fraud_predictions;

-- 6. Manual fraud alert review query for analysts
SELECT 
    transaction_id,
    ROUND(amount::numeric, 2) AS amount,
    ROUND(fraud_probability::numeric, 4) AS fraud_probability,
    created_at
FROM fraud_predictions
WHERE flagged_as_fraud = TRUE
ORDER BY fraud_probability DESC;

-- 7. Fraud rate over time (hourly breakdown)
SELECT 
    DATE_TRUNC('hour', created_at) AS hour,
    COUNT(*) AS total_scored,
    SUM(CASE WHEN flagged_as_fraud THEN 1 ELSE 0 END) AS flagged,
    ROUND(AVG(fraud_probability)::numeric, 4) AS avg_probability
FROM fraud_predictions
GROUP BY DATE_TRUNC('hour', created_at)
ORDER BY hour ASC;