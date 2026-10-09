import os
import hashlib
import hmac
import secrets
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
from psycopg2.extras import RealDictCursor


app = FastAPI(title="Food Delivery & Analytics API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3080"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
DB_HOST = os.getenv("POSTGRES_HOST", "postgres")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "postgres")
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "root")

def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            cursor_factory=RealDictCursor
        )
        conn.autocommit = True
        conn.set_client_encoding('UTF8')
        return conn
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection error: {str(e)}")

def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        310000
    )

    return (
        "pbkdf2_sha256$310000$"
        + salt.hex()
        + "$"
        + password_hash.hex()
    )

def verify_password(password: str, stored_hash: str) -> bool:
    try:
        algorithm, iterations, salt_hex, hash_hex = stored_hash.split("$")

        if algorithm != "pbkdf2_sha256":
            return False

        salt = bytes.fromhex(salt_hex)

        calculated_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            int(iterations)
        )

        return hmac.compare_digest(
            calculated_hash.hex(),
            hash_hex
        )

    except (ValueError, TypeError):
        return False

@app.get("/")
def root():
    return {"status": "ok", "message": "Food Delivery API is running"}
@app.get("/restaurants")
def get_restaurants(limit: int = 20, offset: int = 0):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT id, source_id, name, category, price_range, rating, rating_count, address, zip_code, image_url
            FROM public.restaurants
            ORDER BY id
            LIMIT %s OFFSET %s;
        """, (limit, offset))
        restaurants = cursor.fetchall()
        return {"limit": limit, "offset": offset, "data": restaurants}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query error: {str(e)}")
    finally:
        cursor.close()
        conn.close()

@app.get("/restaurants/{restaurant_id}")
def get_restaurant_details(restaurant_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM public.restaurants WHERE id = %s;", (restaurant_id,))
        restaurant = cursor.fetchone()
        if not restaurant:
            raise HTTPException(status_code=404, detail="Restaurant not found")
            
        cursor.execute("SELECT * FROM public.dishes WHERE restaurant_id = %s;", (restaurant_id,))
        dishes = cursor.fetchall()
        
        return {
            "restaurant": restaurant,
            "menu": dishes
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query error: {str(e)}")
    finally:
        cursor.close()
        conn.close()

@app.get("/users")
def get_users(limit: int = 50):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM public.users LIMIT %s;", (limit,))
        users = cursor.fetchall()
        return {"users": users}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query error: {str(e)}")
    finally:
        cursor.close()
        conn.close()


@app.post("/auth/register")
def register_user(
    username: str,
    email: str,
    password: str,
    name: str = ""
):
    username = username.strip()
    email = email.strip().lower()
    name = name.strip()

    if not username:
        raise HTTPException(
            status_code=400,
            detail="Username is required"
        )

    if not email:
        raise HTTPException(
            status_code=400,
            detail="Email is required"
        )

    if len(password) < 6:
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 6 characters"
        )

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT id
            FROM public.users
            WHERE username = %s;
            """,
            (username,)
        )

        if cursor.fetchone():
            raise HTTPException(
                status_code=409,
                detail="Username already exists"
            )

        cursor.execute(
            """
            SELECT id
            FROM public.users
            WHERE LOWER(email) = LOWER(%s);
            """,
            (email,)
        )

        if cursor.fetchone():
            raise HTTPException(
                status_code=409,
                detail="Email already exists"
            )

        password_hash = hash_password(password)

        cursor.execute(
            """
            INSERT INTO public.users
                (username, email, password_hash, name)
            VALUES
                (%s, %s, %s, %s)
            RETURNING id, username, email, name, created_at;
            """,
            (
                username,
                email,
                password_hash,
                name
            )
        )

        user = cursor.fetchone()

        return {
            "message": "Registration successful",
            "user": user
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Registration error: {str(e)}"
        )

    finally:
        cursor.close()
        conn.close()

@app.post("/auth/login")
def login_user(
    username: str,
    password: str
):
    username = username.strip()

    if not username or not password:
        raise HTTPException(
            status_code=400,
            detail="Username and password are required"
        )

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT id, username, email, password_hash, name, created_at
            FROM public.users
            WHERE username = %s;
            """,
            (username,)
        )

        user = cursor.fetchone()

        if not user:
            raise HTTPException(
                status_code=401,
                detail="Invalid username or password"
            )

        if not user["password_hash"]:
            raise HTTPException(
                status_code=401,
                detail="This account does not have a usable password"
            )

        if not verify_password(
            password,
            user["password_hash"]
        ):
            raise HTTPException(
                status_code=401,
                detail="Invalid username or password"
            )

        return {
            "message": "Login successful",
            "user": {
                "id": user["id"],
                "username": user["username"],
                "email": user["email"],
                "name": user["name"],
                "created_at": user["created_at"]
            }
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Login error: {str(e)}"
        )

    finally:
        cursor.close()
        conn.close()

        
@app.get("/users/{user_id}/orders")
def get_user_orders(user_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Check user
        cursor.execute(
            """
            SELECT id, username, email, name
            FROM public.users
            WHERE id = %s;
            """,
            (user_id,)
        )

        user = cursor.fetchone()

        if not user:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )

        cursor.execute(
            """
            SELECT
                o.id,
                o.user_id,
                o.restaurant_id,
                r.name AS restaurant_name,
                r.address AS restaurant_address,
                o.status,
                o.subtotal,
                o.delivery_fee,
                o.discount,
                o.total_amount,
                o.delivery_address,
                o.created_at,
                o.updated_at
            FROM public.orders o
            JOIN public.restaurants r
                ON r.id = o.restaurant_id
            WHERE o.user_id = %s
            ORDER BY o.created_at DESC;
            """,
            (user_id,)
        )

        orders = cursor.fetchall()

        for order in orders:
            cursor.execute(
                """
                SELECT
                    oi.dish_id,
                    d.name AS dish_name,
                    oi.quantity,
                    oi.unit_price,
                    oi.subtotal
                FROM public.order_items oi
                JOIN public.dishes d
                    ON d.id = oi.dish_id
                WHERE oi.order_id = %s
                ORDER BY oi.id;
                """,
                (order["id"],)
            )

            order["items"] = cursor.fetchall()

        return {
            "user": user,
            "orders": orders
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load orders: {str(e)}"
        )

    finally:
        cursor.close()
        conn.close()


class OrderItemRequest(BaseModel):
    dish_id: int
    quantity: int


class OrderRequest(BaseModel):
    user_id: int
    restaurant_id: int
    delivery_address: str
    items: list[OrderItemRequest]

@app.post("/orders")
def create_order(order_request: OrderRequest):
    user_id = order_request.user_id
    restaurant_id = order_request.restaurant_id
    delivery_address = order_request.delivery_address
    items = order_request.items
    
    if not delivery_address.strip():
        raise HTTPException(
            status_code=400,
            detail="Delivery address is required"
        )

    if not items:
        raise HTTPException(
            status_code=400,
            detail="Order must contain at least one item"
        )

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT id
            FROM public.users
            WHERE id = %s;
            """,
            (user_id,)
        )

        if not cursor.fetchone():
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )

        cursor.execute(
            """
            SELECT id
            FROM public.restaurants
            WHERE id = %s AND is_active = true;
            """,
            (restaurant_id,)
        )

        if not cursor.fetchone():
            raise HTTPException(
                status_code=404,
                detail="Restaurant not found"
            )

        subtotal = 0
        prepared_items = []

        for item in items:
            dish_id = item.dish_id
            quantity = item.quantity

            if quantity <= 0:
                raise HTTPException(
                    
                    status_code=400,
                    detail="Quantity must be greater than 0"
                )

            cursor.execute(
                """
                SELECT id, restaurant_id, price, is_available
                FROM public.dishes
                WHERE id = %s;
                """,
                (dish_id,)
            )

            dish = cursor.fetchone()

            if not dish:
                raise HTTPException(
                    status_code=404,
                    detail=f"Dish {dish_id} not found"
                )

            if dish["restaurant_id"] != restaurant_id:
                raise HTTPException(
                    status_code=400,
                    detail=f"Dish {dish_id} does not belong to this restaurant"
                )

            if not dish["is_available"]:
                raise HTTPException(
                    status_code=400,
                    detail=f"Dish {dish_id} is not available"
                )

            unit_price = float(dish["price"])
            item_subtotal = unit_price * quantity

            subtotal += item_subtotal

            prepared_items.append({
                "dish_id": dish_id,
                "quantity": quantity,
                "unit_price": unit_price,
                "subtotal": item_subtotal
            })

        delivery_fee = 2.99
        discount = 0
        total_amount = subtotal + delivery_fee - discount

        cursor.execute(
            """
            INSERT INTO public.orders
                (
                    user_id,
                    restaurant_id,
                    status,
                    subtotal,
                    delivery_fee,
                    discount,
                    total_amount,
                    delivery_address
                )
            VALUES
                (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING
                id,
                user_id,
                restaurant_id,
                status,
                subtotal,
                delivery_fee,
                discount,
                total_amount,
                delivery_address,
                created_at;
            """,
            (
                user_id,
                restaurant_id,
                "pending",
                subtotal,
                delivery_fee,
                discount,
                total_amount,
                delivery_address.strip()
            )
        )

        order = cursor.fetchone()
        for item in prepared_items:
            cursor.execute(
                """
                INSERT INTO public.order_items
                    (
                        order_id,
                        dish_id,
                        quantity,
                        unit_price,
                        subtotal
                    )
                VALUES
                    (%s, %s, %s, %s, %s);
                """,
                (
                    order["id"],
                    item["dish_id"],
                    item["quantity"],
                    item["unit_price"],
                    item["subtotal"]
                )
            )

        return {
            "message": "Order created successfully",
            "order": order,
            "items": prepared_items
        }

    except HTTPException:
        conn.rollback()
        raise

    except Exception as e:
        conn.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Order creation error: {str(e)}"
        )

    finally:
        cursor.close()
        conn.close()