import importlib.util
import os
from unittest.mock import MagicMock, patch

import pytest

GENERATOR_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "scripts", "generator", "main.py"
)


@pytest.fixture(scope="module")
def generator_module():
    with patch("kafka.KafkaProducer") as mock_producer, \
         patch("boto3.client") as mock_boto, \
         patch("psycopg2.connect") as mock_pg:

        mock_producer.return_value = MagicMock()
        mock_boto.return_value = MagicMock()
        mock_pg.return_value = MagicMock()

        spec = importlib.util.spec_from_file_location(
            "generator_main", GENERATOR_PATH
        )
        module = importlib.util.module_from_spec(spec)

        module.__name__ = "generator_main"
        spec.loader.exec_module(module)

        yield module


class TestGenerateEcommerceEvent:
    def test_event_structure(self, generator_module):
        with patch.object(generator_module, "get_db_connection") as mock_db:
            cursor = MagicMock()
            cursor.fetchone.side_effect = [
                (1,),          
                (10, "Pizza", 9.99),
            ]
            mock_db.return_value.cursor.return_value = cursor

            event = generator_module.generate_ecommerce_event()

            assert event is not None
            assert "event_id" in event
            assert "user_id" in event
            assert "item_id" in event
            assert "action" in event
            assert event["action"] in ("view", "add_to_cart", "buy")
            assert "timestamp" in event

    def test_buy_event_has_price(self, generator_module):
        with patch.object(generator_module, "get_db_connection") as mock_db, \
             patch("random.choices", return_value=["buy"]):
            cursor = MagicMock()
            cursor.fetchone.side_effect = [
                (1,),
                (10, "Pizza", 9.99),
            ]
            mock_db.return_value.cursor.return_value = cursor

            event = generator_module.generate_ecommerce_event()
            assert event["action"] == "buy"
            assert event["price"] == 9.99

    def test_view_event_has_zero_price(self, generator_module):
        with patch.object(generator_module, "get_db_connection") as mock_db, \
             patch("random.choices", return_value=["view"]):
            cursor = MagicMock()
            cursor.fetchone.side_effect = [
                (1,),
                (10, "Pizza", 9.99),
            ]
            mock_db.return_value.cursor.return_value = cursor

            event = generator_module.generate_ecommerce_event()
            assert event["action"] == "view"
            assert event["price"] == 0.0


class TestGenerateOrderEvent:
    def test_order_structure(self, generator_module):
        with patch.object(generator_module, "get_db_connection") as mock_db:
            cursor = MagicMock()
            cursor.fetchone.side_effect = [
                (1,),  
                (2,),   
            ]
            cursor.fetchall.return_value = [
                (10, "Pizza", 9.99),
                (11, "Cola", 2.50),
            ]
            mock_db.return_value.cursor.return_value = cursor

            order = generator_module.generate_order_event()

            assert order["event_type"] == "order_created"
            assert order["status"] == "created"
            assert order["total_amount"] > 0
            assert len(order["items"]) == 2
            for item in order["items"]:
                assert "dish_id" in item
                assert "quantity" in item
                assert item["quantity"] >= 1

    def test_order_total_amount_calculation(self, generator_module):
        with patch.object(generator_module, "get_db_connection") as mock_db, \
             patch("random.randint", return_value=2):
            cursor = MagicMock()
            cursor.fetchone.side_effect = [
                (1,),
                (2,),
            ]
            cursor.fetchall.return_value = [
                (10, "Pizza", 10.00),
            ]
            mock_db.return_value.cursor.return_value = cursor

            order = generator_module.generate_order_event()
            assert order["total_amount"] == 20.00