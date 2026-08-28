# Databricks notebook source
# MAGIC %md
# MAGIC # Ingest transactions.csv
# MAGIC - Read the file using Spark DataFrameReader API
# MAGIC - Add Metadata columns (source file, ingestion timestamp,batch_date)
# MAGIC - Write to bronze delta table

# COMMAND ----------

# MAGIC %md
# MAGIC # Using widgets we are gonna pass the input parameters as batch_date

# COMMAND ----------

dbutils.widgets.text("p_batch_date","")
v_batch_date = dbutils.widgets.get("p_batch_date")

# COMMAND ----------

# MAGIC %run ../00_common/01_environment_config

# COMMAND ----------

landing_folder_path

# COMMAND ----------

source_file=f"{landing_folder_path}/transactions.csv"

# COMMAND ----------

table_name = "workspace.bronze.transactions"

# COMMAND ----------

from pyspark.sql.types import StructType, StructField, StringType

transactions_schema = StructType([
    StructField("step",           StringType(), True),
    StructField("type",           StringType(), True),
    StructField("amount",         StringType(), True),
    StructField("nameOrig",       StringType(), True),
    StructField("oldbalanceOrg",  StringType(), True),
    StructField("newbalanceOrig", StringType(), True),
    StructField("nameDest",       StringType(), True),
    StructField("oldbalanceDest", StringType(), True),
    StructField("newbalanceDest", StringType(), True),
    StructField("isFraud",        StringType(), True),
    StructField("isFlaggedFraud", StringType(), True),
])

# COMMAND ----------

df = (
    spark.read
    .format("csv")
    .option("header", "true")
    .option("enforceSchema","false")
    .schema(transactions_schema)
    .load(source_file)
)

# COMMAND ----------

df.printSchema()

# COMMAND ----------

print("rows:", df.count())

# COMMAND ----------

from pyspark.sql import functions as F
bronze_df =(df
    .withColumn("source_file",F.col("_metadata.file_path"))
    .withColumn("ingest_timestamp",F.current_timestamp())
    .withColumn("batch_date",F.lit(v_batch_date).cast("date"))
)


# COMMAND ----------

display(bronze_df)

# COMMAND ----------

(
    bronze_df
    .write
    .format("delta")
    .mode("overwrite")
    .option("replaceWhere", f"batch_date='{v_batch_date}'")
    .saveAsTable(table_name)
)

# COMMAND ----------

display(spark.table(table_name))

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT batch_date, ingest_timestamp, COUNT(*)
# MAGIC FROM workspace.bronze.transactions
# MAGIC GROUP BY batch_date, ingest_timestamp

# COMMAND ----------

