-- Databricks notebook source
SELECT * 
FROM workspace.bronze.transactions 

-- COMMAND ----------

--1. Transaction types 
SELECT type, COUNT(*) AS rows 
FROM workspace.bronze.transactions 
GROUP BY type 
ORDER BY rows DESC;

-- COMMAND ----------

-- 2. Bad amounts (expect 0)
SELECT COUNT(*) AS non_positive FROM workspace.bronze.transactions WHERE CAST(amount AS DOUBLE) <= 0;

-- COMMAND ----------

-- 3. Where fraud lives + overall rate
SELECT type, COUNT(*) AS rows, 
SUM(CAST(isFraud AS INT)) AS frauds,
       ROUND(100.0*SUM(CAST(isFraud AS INT))/COUNT(*),3) AS fraud_pct
FROM workspace.bronze.transactions GROUP BY type ORDER BY frauds DESC;

-- COMMAND ----------

-- 4. Does the old rule engine work? (isFlaggedFraud vs isFraud)
SELECT isFraud, isFlaggedFraud, COUNT(*) FROM workspace.bronze.transactions
GROUP BY isFraud, isFlaggedFraud;

-- COMMAND ----------

-- 5. THE BIG ONE: do sender balances reconcile?
SELECT type,
  COUNT(*) AS rows,
  SUM(CASE WHEN ABS(CAST(oldbalanceOrg AS DOUBLE) - CAST(amount AS DOUBLE)
                   - CAST(newbalanceOrig AS DOUBLE)) > 0.01 THEN 1 ELSE 0 END) AS broken
FROM workspace.bronze.transactions GROUP BY type;

-- COMMAND ----------

-- 6. The fraud signature: was the account drained to zero?
SELECT isFraud, COUNT(*) AS rows,
  SUM(CASE WHEN CAST(newbalanceOrig AS DOUBLE) = 0
            AND CAST(oldbalanceOrg AS DOUBLE) > 0 THEN 1 ELSE 0 END) AS emptied
FROM workspace.bronze.transactions GROUP BY isFraud;

-- COMMAND ----------

-- 7. Nulls anywhere?
SELECT COUNT(*) - COUNT(amount) AS null_amount,
       COUNT(*) - COUNT(type) AS null_type,
       COUNT(*) - COUNT(nameOrig) AS null_sender
FROM workspace.bronze.transactions;

-- COMMAND ----------

