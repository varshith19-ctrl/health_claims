# """
# Apache Airflow DAG Template — Health Claims ETL Pipeline
# Schedule: Daily at 2:00 AM UTC

# To use:
# 1. Install Airflow: pip install apache-airflow
# 2. Copy this file to your Airflow dags/ directory
# 3. Set PYTHONPATH to include the project root
# 4. Configure .env or Airflow Variables for API keys

# DAG: health_claims_daily
# Tasks: bronze -> silver -> gold -> train_ml -> build_rag_index
# """

# from datetime import datetime, timedelta
# from airflow import DAG
# from airflow.operators.python import PythonOperator

# # Default arguments for all tasks
# default_args = {
#     "owner": "claimshield",
#     "depends_on_past": False,
#     "email_on_failure": False,
#     "email_on_retry": False,
#     "retries": 2,
#     "retry_delay": timedelta(minutes=5),
# }

# dag = DAG(
#     dag_id="health_claims_daily",
#     default_args=default_args,
#     description="Daily ETL pipeline: Bronze -> Silver -> Gold -> ML Training -> RAG Indexing",
#     schedule_interval="0 2 * * *",  # 2 AM UTC daily
#     start_date=datetime(2026, 1, 1),
#     catchup=False,
#     tags=["health_claims", "etl", "ml"],
# )


# # ── Task callables ─────────────────────────────────────────────
# # These import from the project's pipeline module.
# # Ensure PYTHONPATH includes the project root.

# def _run_bronze(**kwargs):
#     from data_engineering.pipeline import run_bronze
#     result = run_bronze()
#     kwargs["ti"].xcom_push(key="bronze_result", value=result)


# def _run_silver(**kwargs):
#     from data_engineering.pipeline import run_silver
#     result = run_silver()
#     kwargs["ti"].xcom_push(key="silver_result", value=result)


# def _run_gold(**kwargs):
#     from data_engineering.pipeline import run_gold
#     result = run_gold()
#     kwargs["ti"].xcom_push(key="gold_result", value=result)


# def _run_ml_training(**kwargs):
#     from data_engineering.pipeline import run_ml_training
#     result = run_ml_training()
#     kwargs["ti"].xcom_push(key="ml_result", value=result)


# def _run_rag_indexing(**kwargs):
#     from data_engineering.pipeline import run_rag_indexing
#     result = run_rag_indexing()
#     kwargs["ti"].xcom_push(key="rag_result", value=result)


# # ── Task definitions ──────────────────────────────────────────

# t_bronze = PythonOperator(
#     task_id="ingest_bronze",
#     python_callable=_run_bronze,
#     dag=dag,
# )

# t_silver = PythonOperator(
#     task_id="build_silver",
#     python_callable=_run_silver,
#     dag=dag,
# )

# t_gold = PythonOperator(
#     task_id="build_gold",
#     python_callable=_run_gold,
#     dag=dag,
# )

# t_ml = PythonOperator(
#     task_id="train_ml_models",
#     python_callable=_run_ml_training,
#     dag=dag,
# )

# t_rag = PythonOperator(
#     task_id="build_rag_index",
#     python_callable=_run_rag_indexing,
#     dag=dag,
# )

# # ── Task dependencies ─────────────────────────────────────────
# # bronze -> silver -> gold -> [train_ml, build_rag_index]

# t_bronze >> t_silver >> t_gold >> [t_ml, t_rag]
