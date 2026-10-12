import os
import sys
import pytest
from datetime import datetime
from unittest.mock import patch
from datetime import datetime
from airflow.utils.timezone import convert_to_utc 

sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "dags")
))


@pytest.fixture(scope="module")
def dagbag():
    from airflow.models import DagBag
    dags_folder = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "dags")
    )
    with patch("telegram_alerts.send_telegram_failure_alert"):
        return DagBag(dag_folder=dags_folder, include_examples=False)


class TestDagBag:
    def test_no_import_errors(self, dagbag):
        assert len(dagbag.import_errors) == 0, f"Errors: {dagbag.import_errors}"

    def test_rfm_dag_exists(self, dagbag):
        assert "rfm_segmentation_daily" in dagbag.dags


class TestRFMDag:
    @pytest.fixture
    def dag(self, dagbag):
        return dagbag.dags["rfm_segmentation_daily"]

    def test_dag_id(self, dag):
        assert dag.dag_id == "rfm_segmentation_daily"

    def test_schedule(self, dag):
        assert dag.schedule_interval == "0 2 * * *"  
        assert dag.timetable.summary == "0 2 * * *"

    def test_start_date(self, dag):
        assert dag.start_date.date().isoformat() == "2026-01-01"

    def test_catchup_disabled(self, dag):
        assert dag.catchup is False

    def test_tags(self, dag):
        for tag in ("pyspark", "minio", "rfm", "postgres"):
            assert tag in dag.tags

    def test_owner(self, dag):
        assert dag.default_args["owner"] == "data_engineer"

    def test_retries(self, dag):
        assert dag.default_args["retries"] == 1
        assert dag.default_args["retry_delay"].total_seconds() == 300

    def test_failure_callback(self, dag):
        assert callable(dag.default_args["on_failure_callback"])

    def test_depends_on_past(self, dag):
        assert dag.default_args["depends_on_past"] is False

    def test_email_notifications_disabled(self, dag):
        assert dag.default_args["email_on_failure"] is False
        assert dag.default_args["email_on_retry"] is False


class TestRFMDagTasks:
    @pytest.fixture
    def dag(self, dagbag):
        return dagbag.dags["rfm_segmentation_daily"]

    def test_task_count(self, dag):
        assert len(dag.tasks) == 1

    def test_task_id(self, dag):
        assert "run_rfm_analysis_pyspark" in [t.task_id for t in dag.tasks]

    def test_task_type(self, dag):
        from airflow.operators.bash import BashOperator
        task = dag.get_task("run_rfm_analysis_pyspark")
        assert isinstance(task, BashOperator)

    def test_bash_command_contains_spark_submit(self, dag):
        task = dag.get_task("run_rfm_analysis_pyspark")
        assert "spark-submit" in task.bash_command

    def test_bash_command_contains_script(self, dag):
        task = dag.get_task("run_rfm_analysis_pyspark")
        assert "rfm_analysis.py" in task.bash_command

    def test_bash_command_contains_master(self, dag):
        task = dag.get_task("run_rfm_analysis_pyspark")
        assert "spark://spark-master:7077" in task.bash_command

    def test_bash_command_contains_jars(self, dag):
        task = dag.get_task("run_rfm_analysis_pyspark")
        assert "postgresql-42.6.0.jar" in task.bash_command
        assert "hadoop-aws" in task.bash_command

    def test_bash_command_uses_docker(self, dag):
        task = dag.get_task("run_rfm_analysis_pyspark")
        assert "docker exec" in task.bash_command
        assert "spark-master" in task.bash_command

    def test_no_dependencies(self, dag):
        task = dag.get_task("run_rfm_analysis_pyspark")
        assert len(task.upstream_task_ids) == 0
        assert len(task.downstream_task_ids) == 0

    