import os
from datetime import datetime

from cosmos import DbtDag, ProjectConfig, ProfileConfig, ExecutionConfig
from cosmos.profiles import SnowflakeUserPasswordProfileMapping

WORKSPACE_NAME='dbt_sales'
AIRFLOW_FOLDER_NAME='dbt_dag'
DAGS_FOLDER_NAME='dags'
DBT_FOLDER_NAME='dbt_sales'
DOCKER_VENV_NAME='dbt_venv'

DBT_DB_NAME='dbt_db'
DBT_SCHEMA_NAME='dbt_schema'


profile_config = ProfileConfig(
    profile_name="default",
    target_name="dev",
    profile_mapping=SnowflakeUserPasswordProfileMapping(
        conn_id="snowflake_conn", 
        profile_args={"database": DBT_DB_NAME, "schema": DBT_SCHEMA_NAME},
    )
)

dbt_snowflake_dag = DbtDag(
    project_config=ProjectConfig(f"/usr/local/airflow/dags/dbt/{DBT_FOLDER_NAME}",),
    operator_args={"install_deps": True},
    profile_config=profile_config,
    execution_config=ExecutionConfig(dbt_executable_path=f"{os.environ['AIRFLOW_HOME']}/{DOCKER_VENV_NAME}/bin/dbt",),
    schedule_interval="@daily",
    start_date=datetime(2023, 9, 10),
    catchup=False,
    dag_id=AIRFLOW_FOLDER_NAME,
)