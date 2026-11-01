from unittest.mock import MagicMock, patch

import pytest
from uuid import uuid4

class TestRoot:
    def test_root_returns_ok(self, api_client):
        response = api_client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "message" in data


class TestRestaurants:
    def test_get_restaurants_success(self, api_client, mock_get_db):
        conn, cursor = mock_get_db
        cursor.fetchall.return_value = [
            {"id": 1, "name": "Pizza Place", "category": "pizza"},
            {"id": 2, "name": "Burger Joint", "category": "burger"},
        ]

        response = api_client.get("/restaurants?limit=10&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 10
        assert data["offset"] == 0
        assert len(data["data"]) == 2

    def test_get_restaurant_details_not_found(self, api_client, mock_get_db):
        conn, cursor = mock_get_db
        cursor.fetchone.return_value = None

        response = api_client.get("/restaurants/99999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_restaurant_details_success(self, api_client, mock_get_db):
        conn, cursor = mock_get_db
        cursor.fetchone.return_value = {"id": 1, "name": "Pizza Place"}
        cursor.fetchall.return_value = [
            {"id": 10, "name": "Margherita", "price": 9.99}
        ]

        response = api_client.get("/restaurants/1")
        assert response.status_code == 200
        data = response.json()
        assert "restaurant" in data
        assert "menu" in data
        assert len(data["menu"]) == 1


class TestRegister:
    def test_register_missing_username(self, api_client):
        response = api_client.post(
            "/auth/register",
            params={"username": "", "email": "a@b.com", "password": "secret123"}
        )
        assert response.status_code == 400
        assert "username" in response.json()["detail"].lower()

    def test_register_missing_email(self, api_client):
        response = api_client.post(
            "/auth/register",
            params={"username": "user1", "email": "", "password": "secret123"}
        )
        assert response.status_code == 400
        assert "email" in response.json()["detail"].lower()

    def test_register_short_password(self, api_client):
        response = api_client.post(
            "/auth/register",
            params={"username": "user1", "email": "a@b.com", "password": "123"}
        )
        assert response.status_code == 400
        assert "6 characters" in response.json()["detail"]

    def test_register_duplicate_username(self, api_client, mock_get_db):
        conn, cursor = mock_get_db
        cursor.fetchone.return_value = {"id": 1}

        response = api_client.post(
            "/auth/register",
            params={"username": "existing", "email": "new@b.com", "password": "secret123"}
        )
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]

    def test_register_success(self, api_client, mock_get_db):
        conn, cursor = mock_get_db
        cursor.fetchone.side_effect = [
            None,  
            None,  
            {"id": 5, "username": "newuser", "email": "new@b.com", "name": ""},
        ]

        response = api_client.post(
            "/auth/register",
            params={"username": "newuser", "email": "new@b.com", "password": "secret123"}
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Registration successful"


class TestLogin:
    def test_login_missing_fields(self, api_client):
        response = api_client.post(
            "/auth/login",
            params={"username": "", "password": ""}
        )
        assert response.status_code == 400

    def test_login_user_not_found(self, api_client, mock_get_db):
        conn, cursor = mock_get_db
        cursor.fetchone.return_value = None

        response = api_client.post(
            "/auth/login",
            params={"username": "ghost", "password": "secret123"}
        )
        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()

    def test_login_wrong_password(self, api_client, mock_get_db):
        from backend.main import hash_password
        conn, cursor = mock_get_db
        cursor.fetchone.return_value = {
            "id": 1,
            "username": "user1",
            "email": "a@b.com",
            "password_hash": hash_password("correct"),
            "name": "",
            "created_at": "2026-01-01",
        }

        response = api_client.post(
            "/auth/login",
            params={"username": "user1", "password": "wrong"}
        )
        assert response.status_code == 401

    def test_login_success(self, api_client, mock_get_db):
        from backend.main import hash_password
        conn, cursor = mock_get_db
        cursor.fetchone.return_value = {
            "id": 1,
            "username": "user1",
            "email": "a@b.com",
            "password_hash": hash_password("secret123"),
            "name": "Test",
            "created_at": "2026-01-01",
        }

        response = api_client.post(
            "/auth/login",
            params={"username": "user1", "password": "secret123"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Login successful"
        assert data["user"]["username"] == "user1"
        assert "password_hash" not in data["user"]  # не утекает



from uuid import uuid4


class TestCreateOrder:
    def test_create_order_requires_authentication(self, api_client):
        payload = {
            "restaurant_id": 1,
            "delivery_address": "123 Main St",
            "items": [{"dish_id": 1, "quantity": 1}],
            "idempotency_key": str(uuid4()),
        }

        response = api_client.post("/orders", json=payload)

        assert response.status_code == 401

    def test_create_order_missing_idempotency_key(
        self, authenticated_api_client
    ):
        payload = {
            "restaurant_id": 1,
            "delivery_address": "123 Main St",
            "items": [{"dish_id": 1, "quantity": 1}],
        }

        response = authenticated_api_client.post("/orders", json=payload)

        assert response.status_code == 422

    def test_create_order_empty_items(self, authenticated_api_client):
        payload = {
            "restaurant_id": 1,
            "delivery_address": "123 Main St",
            "items": [],
            "idempotency_key": str(uuid4()),
        }

        response = authenticated_api_client.post("/orders", json=payload)

        assert response.status_code == 400
        assert "at least one item" in response.json()["detail"].lower()

    def test_create_order_empty_address(self, authenticated_api_client):
        payload = {
            "restaurant_id": 1,
            "delivery_address": "   ",
            "items": [{"dish_id": 1, "quantity": 1}],
            "idempotency_key": str(uuid4()),
        }

        response = authenticated_api_client.post("/orders", json=payload)

        assert response.status_code == 400
        assert "address" in response.json()["detail"].lower()

    
    def test_create_order_invalid_quantity(self, authenticated_api_client):
        payload = {
            "restaurant_id": 1,
            "delivery_address": "123 Main St",
            "items": [{"dish_id": 1, "quantity": 0}],
            "idempotency_key": str(uuid4()),
        }

        response = authenticated_api_client.post("/orders", json=payload)

        assert response.status_code == 422


    def test_create_order_user_not_found(
        self, authenticated_api_client, mock_get_db
    ):
        conn, cursor = mock_get_db
        cursor.fetchone.return_value = None

        payload = {
            "restaurant_id": 1,
            "delivery_address": "123 Main St",
            "items": [{"dish_id": 1, "quantity": 1}],
            "idempotency_key": str(uuid4()),
        }

        response = authenticated_api_client.post("/orders", json=payload)

        assert response.status_code == 404
        assert "user" in response.json()["detail"].lower()
        conn.rollback.assert_called_once()

    def test_create_order_calculates_money_correctly(
        self, authenticated_api_client, mock_get_db
    ):
        from decimal import Decimal
        from uuid import uuid4

        conn, cursor = mock_get_db

        cursor.fetchone.side_effect = [
            {"id": 1},  
            None,       
            {"id": 1},  
            {
                "id": 10,
                "restaurant_id": 1,
                "price": Decimal("10.25"),
                "is_available": True,
            },
            {
                "id": 11,
                "restaurant_id": 1,
                "price": Decimal("3.40"),
                "is_available": True,
            },
            {
                "id": 100,
                "user_id": 1,
                "restaurant_id": 1,
                "status": "pending",
                "subtotal": Decimal("27.30"),
                "delivery_fee": Decimal("2.99"),
                "discount": Decimal("0.00"),
                "total_amount": Decimal("30.29"),
                "delivery_address": "123 Main St",
                "created_at": "2026-10-18T10:00:00",
            },
        ]

        payload = {
            "restaurant_id": 1,
            "delivery_address": "123 Main St",
            "items": [
                {"dish_id": 10, "quantity": 2},
                {"dish_id": 11, "quantity": 2},
            ],
            "idempotency_key": str(uuid4()),
        }

        response = authenticated_api_client.post("/orders", json=payload)

        assert response.status_code == 200, response.text

        from decimal import Decimal

        order_insert = next(
            call for call in cursor.execute.call_args_list
            if "INSERT INTO public.orders" in call.args[0]
        )
        order_params = order_insert.args[1]

        assert order_params[3] == Decimal("27.30")  
        assert order_params[4] == Decimal("2.99")   
        assert order_params[5] == Decimal("0.00")   
        assert order_params[6] == Decimal("30.29")  

       
        item_inserts = [
            call for call in cursor.execute.call_args_list
            if "INSERT INTO public.order_items" in call.args[0]
        ]

        assert len(item_inserts) == 2

        assert item_inserts[0].args[1] == (
            100, 10, 2, Decimal("10.25"), Decimal("20.50")
        )
        assert item_inserts[1].args[1] == (
            100, 11, 2, Decimal("3.40"), Decimal("6.80")
        )
        data = response.json()
        order = data["order"]

        assert float(order["subtotal"]) == 27.30
        assert float(order["delivery_fee"]) == 2.99
        assert float(order["discount"]) == 0.00
        assert float(order["total_amount"]) == 30.29

        assert len(data["items"]) == 2
        assert float(data["items"][0]["unit_price"]) == 10.25
        assert float(data["items"][0]["subtotal"]) == 20.50
        assert float(data["items"][1]["unit_price"]) == 3.40
        assert float(data["items"][1]["subtotal"]) == 6.80

        conn.commit.assert_called_once()

    
    def test_duplicate_order_returns_existing_order(
        self, authenticated_api_client, mock_get_db
    ):
        import hashlib
        import json
        from uuid import uuid4

        conn, cursor = mock_get_db
        key = str(uuid4())

        payload = {
            "restaurant_id": 1,
            "delivery_address": "123 Main St",
            "items": [{"dish_id": 10, "quantity": 2}],
            "idempotency_key": key,
        }

        request_payload = {
            "restaurant_id": 1,
            "delivery_address": "123 Main St",
            "items": [{"dish_id": 10, "quantity": 2}],
        }
        request_hash = hashlib.sha256(
            json.dumps(
                request_payload,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()

        existing_order = {
            "id": 42,
            "user_id": 1,
            "restaurant_id": 1,
            "status": "pending",
            "subtotal": 20.0,
            "delivery_fee": 2.99,
            "discount": 0,
            "total_amount": 22.99,
            "delivery_address": "123 Main St",
            "created_at": "2026-10-18T10:00:00",
            "request_hash": request_hash,
        }

        cursor.fetchone.side_effect = [
            {"id": 1},       # Пользователь существует
            existing_order,  # Заказ с таким ключом уже есть
        ]
        cursor.fetchall.return_value = [
            {
                "dish_id": 10,
                "quantity": 2,
                "unit_price": 10.0,
                "subtotal": 20.0,
            }
        ]

        response = authenticated_api_client.post("/orders", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Order already exists"
        assert data["order"]["id"] == 42
        assert len(data["items"]) == 1
        conn.commit.assert_called_once()
        assert not any(
            "INSERT INTO public.orders" in str(call)
            for call in cursor.execute.call_args_list
        )

    def test_idempotency_key_with_different_payload_returns_409(
        self, authenticated_api_client, mock_get_db
    ):
        import hashlib
        import json
        from uuid import uuid4

        conn, cursor = mock_get_db
        key = str(uuid4())

        original_payload = {
            "restaurant_id": 1,
            "delivery_address": "123 Main St",
            "items": [{"dish_id": 10, "quantity": 1}],
        }
        request_hash = hashlib.sha256(
            json.dumps(
                original_payload,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()

        cursor.fetchone.side_effect = [
            {"id": 1},
            {
                "id": 42,
                "user_id": 1,
                "restaurant_id": 1,
                "status": "pending",
                "subtotal": 10.0,
                "delivery_fee": 2.99,
                "discount": 0,
                "total_amount": 12.99,
                "delivery_address": "123 Main St",
                "created_at": "2026-10-18T10:00:00",
                "request_hash": request_hash,
            },
        ]

        changed_payload = {
            "restaurant_id": 1,
            "delivery_address": "Different Address",
            "items": [{"dish_id": 10, "quantity": 1}],
            "idempotency_key": key,
        }

        response = authenticated_api_client.post(
            "/orders", json=changed_payload
        )

        assert response.status_code == 409
        assert "idempotency key" in response.json()["detail"].lower()
        conn.rollback.assert_called_once()
        conn.commit.assert_not_called()

    
    def test_create_order_rejects_client_supplied_user_id(
        self, authenticated_api_client
    ):
        payload = {
            "user_id": 999,
            "restaurant_id": 1,
            "delivery_address": "123 Main St",
            "items": [{"dish_id": 1, "quantity": 1}],
            "idempotency_key": str(uuid4()),
        }

        response = authenticated_api_client.post("/orders", json=payload)

        assert response.status_code == 422

    def test_create_order_rejects_client_supplied_price(
        self, authenticated_api_client
    ):
        payload = {
            "restaurant_id": 1,
            "delivery_address": "123 Main St",
            "items": [
                {
                    "dish_id": 1,
                    "quantity": 1,
                    "unit_price": 0.01,
                }
            ],
            "idempotency_key": str(uuid4()),
        }

        response = authenticated_api_client.post("/orders", json=payload)

        assert response.status_code == 422




class TestGetUserOrders:
    def test_user_orders_requires_authentication(self, api_client):
        response = api_client.get("/users/1/orders")

        assert response.status_code == 401

    def test_user_cannot_access_another_users_orders(
        self, authenticated_api_client
    ):
        response = authenticated_api_client.get("/users/999/orders")

        assert response.status_code == 403
        assert "access denied" in response.json()["detail"].lower()

    def test_user_not_found(self, authenticated_api_client, mock_get_db):
        conn, cursor = mock_get_db
        cursor.fetchone.return_value = None

        response = authenticated_api_client.get("/users/1/orders")

        assert response.status_code == 404
        assert "user not found" in response.json()["detail"].lower()

    def test_user_with_no_orders(
        self, authenticated_api_client, mock_get_db
    ):
        conn, cursor = mock_get_db
        cursor.fetchone.return_value = {
            "id": 1,
            "username": "user1",
            "email": "user1@example.com",
            "name": "User One",
        }
        cursor.fetchall.return_value = []

        response = authenticated_api_client.get("/users/1/orders")

        assert response.status_code == 200
        assert response.json()["orders"] == []
        assert response.json()["user"]["id"] == 1


class TestRecommendations:
    def test_recommendations_user_not_found(self, api_client, mock_get_db):
        conn, cursor = mock_get_db
        cursor.fetchone.return_value = None

        response = api_client.get("/users/999/recommendations")
        assert response.status_code == 404
        assert "user not found" in response.json()["detail"].lower()

    def test_recommendations_success(self, api_client, mock_get_db):
        conn, cursor = mock_get_db
        cursor.fetchone.return_value = {"id": 1}
        cursor.fetchall.return_value = [
            {"dish_id": 10, "dish_name": "Pizza", "score": 0.95, "rank": 1},
            {"dish_id": 11, "dish_name": "Cola", "score": 0.87, "rank": 2},
        ]

        response = api_client.get("/users/1/recommendations?limit=5")
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == 1
        assert len(data["recommendations"]) == 2