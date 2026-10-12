from unittest.mock import MagicMock, patch

import pytest


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


class TestCreateOrder:
    def test_create_order_empty_items(self, api_client):
        payload = {
            "user_id": 1,
            "restaurant_id": 1,
            "delivery_address": "123 Main St",
            "items": [],
        }
        response = api_client.post("/orders", json=payload)
        assert response.status_code == 400
        assert "at least one item" in response.json()["detail"]

    def test_create_order_empty_address(self, api_client):
        payload = {
            "user_id": 1,
            "restaurant_id": 1,
            "delivery_address": "   ",
            "items": [{"dish_id": 1, "quantity": 1}],
        }
        response = api_client.post("/orders", json=payload)
        assert response.status_code == 400
        assert "address" in response.json()["detail"].lower()

    def test_create_order_user_not_found(self, api_client, mock_get_db):
        conn, cursor = mock_get_db
        cursor.fetchone.return_value = None

        payload = {
            "user_id": 999,
            "restaurant_id": 1,
            "delivery_address": "123 Main St",
            "items": [{"dish_id": 1, "quantity": 1}],
        }
        response = api_client.post("/orders", json=payload)
        assert response.status_code == 404
        assert "user" in response.json()["detail"].lower()

    def test_create_order_invalid_quantity(self, api_client, mock_get_db):
        conn, cursor = mock_get_db
        cursor.fetchone.side_effect = [
            {"id": 1}, 
            {"id": 1}, 
        ]

        payload = {
            "user_id": 1,
            "restaurant_id": 1,
            "delivery_address": "123 Main St",
            "items": [{"dish_id": 1, "quantity": 0}],
        }
        response = api_client.post("/orders", json=payload)
        assert response.status_code == 400
        assert "quantity" in response.json()["detail"].lower()


class TestGetUserOrders:
    def test_user_not_found(self, api_client, mock_get_db):
        conn, cursor = mock_get_db
        cursor.fetchone.return_value = None

        response = api_client.get("/users/999/orders")
        assert response.status_code == 404
        assert "user not found" in response.json()["detail"].lower()

    def test_user_with_no_orders(self, api_client, mock_get_db):
        conn, cursor = mock_get_db
        cursor.fetchone.return_value = {"id": 1, "username": "user1"}
        cursor.fetchall.return_value = []

        response = api_client.get("/users/1/orders")
        assert response.status_code == 200
        data = response.json()
        assert data["orders"] == []