import os
import sys
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "dags")
))


@pytest.fixture
def mock_context():
    task_instance = MagicMock()
    task_instance.dag_id = "rfm_segmentation_daily"
    task_instance.task_id = "run_rfm_analysis_pyspark"

    context = {
        "task_instance": task_instance,
        "execution_date": __import__("datetime").datetime(2026, 1, 1, 2, 0, 0),
        "exception": Exception("Test error"),
    }
    return context


class TestTelegramAlert:
    def test_send_alert_success(self, mock_context):
        with patch("urllib.request.urlopen") as mock_urlopen, \
             patch("urllib.request.Request") as mock_request:
            mock_urlopen.return_value = MagicMock()
            mock_request.return_value = MagicMock()

            from telegram_alerts import send_telegram_failure_alert
            send_telegram_failure_alert(mock_context)

            assert mock_urlopen.called

    def test_send_alert_handles_network_error(self, mock_context):
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.side_effect = Exception("Network error")

            from telegram_alerts import send_telegram_failure_alert
            send_telegram_failure_alert(mock_context)  # не падает

    def _get_payload(self, mock_context):
        with patch("urllib.request.urlopen") as mock_urlopen, \
             patch("urllib.request.Request") as mock_request:
            mock_urlopen.return_value = MagicMock()
            mock_request.return_value = MagicMock()

            from telegram_alerts import send_telegram_failure_alert
            send_telegram_failure_alert(mock_context)

            assert mock_request.called
            call_args = mock_request.call_args
            return call_args.kwargs.get("data")

    def test_message_contains_dag_id(self, mock_context):
        payload = self._get_payload(mock_context)
        assert payload is not None
        assert b"rfm_segmentation_daily" in payload

    def test_message_contains_task_id(self, mock_context):
        payload = self._get_payload(mock_context)
        assert b"run_rfm_analysis_pyspark" in payload

    def test_message_contains_error(self, mock_context):
        payload = self._get_payload(mock_context)
        assert b"Test error" in payload