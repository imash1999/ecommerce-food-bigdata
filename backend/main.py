import os
import hashlib
import hmac
import secrets
import base64
import json
import time
import urllib.request
import urllib.error
from fastapi import Depends, FastAPI, HTTPException, Request, Response
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

SESSION_COOKIE_NAME = "foodexpress_session"
SESSION_MAX_AGE = 8 * 60 * 60


def get_session_secret() -> str:
    secret = os.getenv("ADMIN_SESSION_SECRET", "")
    if len(secret) < 32:
        raise HTTPException(
            status_code=500,
            detail="Session secret is not configured correctly",
        )
    return secret


def create_session_token(user_id: int) -> str:
    payload = {
        "uid": int(user_id),
        "exp": int(time.time()) + SESSION_MAX_AGE,
    }
    encoded = base64.urlsafe_b64encode(
        json.dumps(payload, separators=(",", ":")).encode("utf-8")
    ).decode("ascii").rstrip("=")

    signature = hmac.new(
        get_session_secret().encode("utf-8"),
        encoded.encode("ascii"),
        hashlib.sha256,
    ).hexdigest()

    return f"{encoded}.{signature}"


def read_session_user_id(token: str) -> int | None:
    try:
        encoded, supplied_signature = token.split(".", 1)
        expected_signature = hmac.new(
            get_session_secret().encode("utf-8"),
            encoded.encode("ascii"),
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(expected_signature, supplied_signature):
            return None

        padded = encoded + "=" * (-len(encoded) % 4)
        payload = json.loads(
            base64.urlsafe_b64decode(padded).decode("utf-8")
        )

        user_id = int(payload["uid"])
        expires_at = int(payload["exp"])

        if user_id <= 0 or expires_at <= int(time.time()):
            return None

        return user_id
    except (ValueError, TypeError, KeyError, json.JSONDecodeError):
        return None
    except HTTPException:
        raise
    except Exception:
        return None


def require_admin(request: Request) -> dict:
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required")

    user_id = read_session_user_id(token)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid or expired session")

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT id, is_admin FROM public.users WHERE id = %s;",
            (user_id,),
        )
        user = cursor.fetchone()

        if not user:
            raise HTTPException(status_code=401, detail="User no longer exists")

        if user.get("is_admin") is not True:
            raise HTTPException(status_code=403, detail="Administrator access required")

        return {"id": user["id"]}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Authorization check failed")
    finally:
        cursor.close()
        conn.close()


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
            WHERE is_active = TRUE
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
        cursor.execute("SELECT * FROM public.restaurants WHERE id = %s AND is_active = TRUE;", (restaurant_id,))
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
    password: str,
    response: Response,
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

        response.set_cookie(
            key=SESSION_COOKIE_NAME,
            value=create_session_token(user["id"]),
            max_age=SESSION_MAX_AGE,
            httponly=True,
            secure=os.getenv("COOKIE_SECURE", "false").lower() == "true",
            samesite="lax",
            path="/",
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

        
@app.post("/auth/logout")
def logout_user(response: Response):
    response.delete_cookie(
        key=SESSION_COOKIE_NAME,
        path="/",
        httponly=True,
        secure=os.getenv("COOKIE_SECURE", "false").lower() == "true",
        samesite="lax",
    )
    return {"message": "Logout successful"}


@app.get("/auth/me")
def get_current_user(request: Request):
    token = request.cookies.get(SESSION_COOKIE_NAME)

    if not token:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
        )

    user_id = read_session_user_id(token)

    if user_id is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired session",
        )

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT id, username, email, name, is_admin
            FROM public.users
            WHERE id = %s;
            """,
            (user_id,),
        )

        user = cursor.fetchone()

        if not user:
            raise HTTPException(
                status_code=401,
                detail="User no longer exists",
            )

        return {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "name": user["name"],
            "is_admin": user["is_admin"] is True,
        }

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve current user",
        )

    finally:
        cursor.close()
        conn.close()


class RestaurantCreate(BaseModel):
    name: str
    description: str | None = None
    category: str | None = None
    price_range: str | None = None
    rating: float | None = None
    rating_count: int | None = None
    address: str | None = None
    zip_code: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    image_url: str | None = None


class RestaurantUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    category: str | None = None
    price_range: str | None = None
    rating: float | None = None
    rating_count: int | None = None
    address: str | None = None
    zip_code: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    image_url: str | None = None
    is_active: bool | None = None


class DishCreate(BaseModel):
    name: str
    price: float
    description: str | None = None
    category_id: int | None = None
    image_url: str | None = None


class DishUpdate(BaseModel):
    name: str | None = None
    price: float | None = None
    description: str | None = None
    category_id: int | None = None
    image_url: str | None = None
    is_available: bool | None = None


def admin_db(sql: str, params=(), fetch: str | None = None):
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(sql, params)
            if fetch == "one":
                return cursor.fetchone()
            if fetch == "all":
                return cursor.fetchall()
            return None
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Administrative database operation failed",
        )
    finally:
        if conn is not None:
            conn.close()


def validate_admin_category(restaurant_id: int, category_id: int | None):
    if category_id is None:
        return

    category = admin_db(
        """
        SELECT id
        FROM public.menu_categories
        WHERE id = %s AND restaurant_id = %s
        """,
        (category_id, restaurant_id),
        "one",
    )
    if not category:
        raise HTTPException(
            status_code=400,
            detail="Category does not belong to this restaurant",
        )


@app.post("/admin/airflow/dags/{dag_id}/runs")
def trigger_admin_dag(
    dag_id: str,
    admin: dict = Depends(require_admin),
):
    allowed_dags = {
        "recommendations_daily",
        "rfm_segmentation_daily",
    }

    if dag_id not in allowed_dags:
        raise HTTPException(
            status_code=404,
            detail="DAG not found",
        )

    airflow_url = os.getenv(
        "AIRFLOW_API_BASE_URL",
        "http://airflow-webserver:8080/api/v1",
    ).rstrip("/")

    username = os.getenv("AIRFLOW_API_USERNAME")
    password = os.getenv("AIRFLOW_API_PASSWORD")

    if not username or not password:
        raise HTTPException(
            status_code=503,
            detail="Airflow API credentials are not configured",
        )

    credentials = base64.b64encode(
        f"{username}:{password}".encode("utf-8")
    ).decode("ascii")

    dag_run_id = f"admin_panel__{secrets.token_hex(12)}"

    payload = json.dumps({
        "dag_run_id": dag_run_id,
        "conf": {"source": "admin_panel"},
    }).encode("utf-8")

    request = urllib.request.Request(
        f"{airflow_url}/dags/{dag_id}/dagRuns",
        data=payload,
        headers={
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            result = json.loads(response.read().decode("utf-8"))

        return {
            "message": "DAG run created",
            "dag_id": result.get("dag_id", dag_id),
            "dag_run_id": result.get("dag_run_id", dag_run_id),
            "state": result.get("state"),
        }

    except urllib.error.HTTPError as error:
        if error.code == 401:
            raise HTTPException(
                status_code=502,
                detail="Airflow API authentication failed",
            ) from None

        if error.code == 403:
            raise HTTPException(
                status_code=502,
                detail="Airflow API user lacks permission to trigger DAGs",
            ) from None

        raise HTTPException(
            status_code=502,
            detail=f"Airflow API rejected the request (HTTP {error.code})",
        ) from None

    except (urllib.error.URLError, TimeoutError):
        raise HTTPException(
            status_code=502,
            detail="Could not connect to Airflow API",
        ) from None

@app.get("/admin/restaurants")
def admin_list_restaurants(_admin: dict = Depends(require_admin)):
    return admin_db(
        "SELECT * FROM public.restaurants ORDER BY id",
        fetch="all",
    )


@app.post("/admin/restaurants", status_code=201)
def admin_create_restaurant(
    body: RestaurantCreate,
    _admin: dict = Depends(require_admin),
):
    data = body.dict()
    if not data["name"].strip():
        raise HTTPException(status_code=400, detail="Restaurant name is required")
    if data["rating"] is not None and not 0 <= data["rating"] <= 5:
        raise HTTPException(status_code=400, detail="Rating must be between 0 and 5")
    if data["rating_count"] is not None and data["rating_count"] < 0:
        raise HTTPException(status_code=400, detail="Rating count cannot be negative")

    columns = ["source_id", *data.keys()]
    values = [f"admin-{secrets.token_hex(12)}", *data.values()]
    placeholders = ", ".join(["%s"] * len(values))
    row = admin_db(
        f"""
        INSERT INTO public.restaurants ({", ".join(columns)})
        VALUES ({placeholders})
        RETURNING *
        """,
        tuple(values),
        "one",
    )
    return row


@app.patch("/admin/restaurants/{restaurant_id}")
def admin_update_restaurant(
    restaurant_id: int,
    body: RestaurantUpdate,
    _admin: dict = Depends(require_admin),
):
    data = body.dict(exclude_unset=True)
    if not data:
        raise HTTPException(status_code=400, detail="No fields supplied")
    if any(value is None for value in data.values() if False):
        raise HTTPException(status_code=400, detail="Invalid field value")
    if "name" in data and (data["name"] is None or not data["name"].strip()):
        raise HTTPException(status_code=400, detail="Restaurant name cannot be empty")
    if "is_active" in data and data["is_active"] is None:
        raise HTTPException(status_code=400, detail="is_active cannot be null")
    if data.get("rating") is not None and not 0 <= data["rating"] <= 5:
        raise HTTPException(status_code=400, detail="Rating must be between 0 and 5")
    if data.get("rating_count") is not None and data["rating_count"] < 0:
        raise HTTPException(status_code=400, detail="Rating count cannot be negative")

    assignments = ", ".join(f"{key} = %s" for key in data)
    row = admin_db(
        f"""
        UPDATE public.restaurants
        SET {assignments}, updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
        RETURNING *
        """,
        (*data.values(), restaurant_id),
        "one",
    )
    if not row:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    return row


@app.get("/admin/restaurants/{restaurant_id}/dishes")
def admin_list_dishes(
    restaurant_id: int,
    _admin: dict = Depends(require_admin),
):
    restaurant = admin_db(
        "SELECT id FROM public.restaurants WHERE id = %s",
        (restaurant_id,),
        "one",
    )
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    return admin_db(
        """
        SELECT * FROM public.dishes
        WHERE restaurant_id = %s
        ORDER BY id
        """,
        (restaurant_id,),
        "all",
    )


@app.post("/admin/restaurants/{restaurant_id}/dishes", status_code=201)
def admin_create_dish(
    restaurant_id: int,
    body: DishCreate,
    _admin: dict = Depends(require_admin),
):
    if not body.name.strip():
        raise HTTPException(status_code=400, detail="Dish name is required")
    if body.price <= 0:
        raise HTTPException(status_code=400, detail="Price must be greater than zero")

    restaurant = admin_db(
        "SELECT id FROM public.restaurants WHERE id = %s",
        (restaurant_id,),
        "one",
    )
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    validate_admin_category(restaurant_id, body.category_id)
    data = body.dict()
    columns = ["restaurant_id", *data.keys()]
    values = [restaurant_id, *data.values()]
    placeholders = ", ".join(["%s"] * len(values))

    return admin_db(
        f"""
        INSERT INTO public.dishes ({", ".join(columns)})
        VALUES ({placeholders})
        RETURNING *
        """,
        tuple(values),
        "one",
    )


@app.patch("/admin/dishes/{dish_id}")
def admin_update_dish(
    dish_id: int,
    body: DishUpdate,
    _admin: dict = Depends(require_admin),
):
    data = body.dict(exclude_unset=True)
    if not data:
        raise HTTPException(status_code=400, detail="No fields supplied")
    if "name" in data and (data["name"] is None or not data["name"].strip()):
        raise HTTPException(status_code=400, detail="Dish name cannot be empty")
    if "price" in data and (
        data["price"] is None or data["price"] <= 0
    ):
        raise HTTPException(status_code=400, detail="Price must be greater than zero")
    if "is_available" in data and data["is_available"] is None:
        raise HTTPException(status_code=400, detail="is_available cannot be null")

    dish = admin_db(
        "SELECT id, restaurant_id FROM public.dishes WHERE id = %s",
        (dish_id,),
        "one",
    )
    if not dish:
        raise HTTPException(status_code=404, detail="Dish not found")

    if "category_id" in data:
        validate_admin_category(dish["restaurant_id"], data["category_id"])

    assignments = ", ".join(f"{key} = %s" for key in data)
    return admin_db(
        f"""
        UPDATE public.dishes
        SET {assignments}, updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
        RETURNING *
        """,
        (*data.values(), dish_id),
        "one",
    )


@app.post("/admin/restaurants/{restaurant_id}/disable")
def admin_disable_restaurant(
    restaurant_id: int,
    _admin: dict = Depends(require_admin),
):
    row = admin_db(
        """
        UPDATE public.restaurants
        SET is_active = FALSE, updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
        RETURNING id, is_active
        """,
        (restaurant_id,),
        "one",
    )
    if not row:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    return row


@app.post("/admin/dishes/{dish_id}/disable")
def admin_disable_dish(
    dish_id: int,
    _admin: dict = Depends(require_admin),
):
    row = admin_db(
        """
        UPDATE public.dishes
        SET is_available = FALSE, updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
        RETURNING id, is_available
        """,
        (dish_id,),
        "one",
    )
    if not row:
        raise HTTPException(status_code=404, detail="Dish not found")
    return row



@app.get("/users/{user_id}/orders")
def get_user_orders(
    user_id: int,
    current_user: dict = Depends(get_current_user)
):
    if user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
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
    restaurant_id: int
    delivery_address: str
    items: list[OrderItemRequest]

@app.post("/orders")
def create_order(
    order_request: OrderRequest,
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user["id"]
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
    conn.autocommit = False
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
        conn.commit()

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

@app.get("/users/{user_id}/recommendations")
def get_user_recommendations(user_id: int, limit: int = 5):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT id FROM public.users WHERE id = %s;",
            (user_id,)
        )
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="User not found")

        cursor.execute("""
            SELECT dish_id, dish_name, image_url, score, rank
            FROM public.user_recommendations
            WHERE user_id = %s
            ORDER BY rank
            LIMIT %s;
        """, (user_id, limit))

        recommendations = cursor.fetchall()

        cursor.execute("""
            SELECT
                d.id AS dish_id,
                d.name AS dish_name,
                d.image_url,
                COUNT(oi.id)::float AS score,
                0 AS rank
            FROM public.dishes d
            LEFT JOIN public.order_items oi ON oi.dish_id = d.id
            GROUP BY d.id, d.name, d.image_url
            ORDER BY score DESC, d.id
            LIMIT %s;
        """, (limit,))

        return {
            "user_id": user_id,
            "recommendations": recommendations
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query error: {str(e)}")
    finally:
        cursor.close()
        conn.close()