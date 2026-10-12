from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
from telegram_alerts import send_telegram_failure_alert

default_args = {
    'owner': 'data_engineer',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
    'on_failure_callback': send_telegram_failure_alert,
}

with DAG(
    dag_id='rfm_segmentation_daily',
    default_args=default_args,
    description='每日从 SeaweedFS 数据湖（S3）进行 RFM 用户细分计算。',
    schedule='0 2 * * *',
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=['pyspark', 'seaweedfs', 'rfm', 'postgres', 's3'],
) as dag:

    run_rfm_spark_job = BashOperator(
        task_id='run_rfm_analysis_pyspark',
        bash_command='''
        export DOCKER_API_VERSION=1.44 && \
        docker exec -u 0 \
          -e S3_ENDPOINT=http://seaweedfs:9000 \
          -e S3_ACCESS_KEY=seaweedfs \
          -e S3_SECRET_KEY=seaweedfs \
          -e S3_BUCKET=raw-events \
          -e S3_PREFIX=orders/ \
          spark-master /opt/spark/bin/spark-submit \
          --master spark://spark-master:7077 \
          --jars /opt/spark-apps/hadoop-aws-3.3.4.jar,/opt/spark-apps/aws-java-sdk-bundle-1.12.262.jar,/opt/spark-apps/postgresql-42.6.0.jar \
          /opt/spark-apps/rfm_analysis.py
        ''',
    )

    run_rfm_spark_job