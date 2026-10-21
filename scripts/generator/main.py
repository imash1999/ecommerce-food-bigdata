
import html
import json
import os
import random
import time
import uuid
from contextlib import closing
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP

import boto3
import psycopg2
from kafka import KafkaProducer


KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "order-events")
KAFKA_EVENTS_TOPIC = os.getenv("KAFKA_EVENTS_TOPIC", "ecommerce-events")

POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgres")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "postgres")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "root")

S3_ENDPOINT_URL = os.getenv("S3_ENDPOINT_URL", "http://seaweedfs:9000")
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY", "seaweedfs")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY", "seaweedfs")
S3_BUCKET = os.getenv("S3_BUCKET", "raw-events")

CENT = Decimal("0.01")
_bucket_creation_attempted = False


def get_db_connection():
    return psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        database=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        connect_timeout=10,
    )


s3_client = boto3.client(
    "s3",
    endpoint_url=S3_ENDPOINT_URL,
    aws_access_key_id=S3_ACCESS_KEY,
    aws_secret_access_key=S3_SECRET_KEY,
)


def send_to_minio(event_data, folder="orders"):
    global _bucket_creation_attempted

    try:
        if not _bucket_creation_attempted:
            _bucket_creation_attempted = True
            try:
                s3_client.create_bucket(Bucket=S3_BUCKET)
            except Exception as exc:
                print(f"Bucket initialization notice: {exc}")

        now = datetime.now(timezone.utc)
        file_path = (
            f"{folder}/{now.strftime('%Y-%m-%d')}/"
            f"event_{now.strftime('%H%M%S_%f')}_{uuid.uuid4().hex}.json"
        )

        body = json.dumps(
            event_data,
            ensure_ascii=False,
        ).encode("utf-8")

        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=file_path,
            Body=body,
            ContentType="application/json",
        )

    except Exception as exc:
        print(f"Object storage error ({folder}): {exc}")


def generate_order_event():
    with closing(get_db_connection()) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id FROM public.users ORDER BY random() LIMIT 1;"
            )
            user_row = cur.fetchone()

            if not user_row:
                raise RuntimeError(
                    "Cannot generate order: public.users is empty"
                )

            user_id = user_row[0]

            cur.execute("""
                SELECT r.id
                FROM public.restaurants AS r
                JOIN public.dishes AS d ON d.restaurant_id = r.id
                WHERE d.price > 0
                GROUP BY r.id
                ORDER BY random()
                LIMIT 1;
            """)
            restaurant_row = cur.fetchone()

            if not restaurant_row:
                raise RuntimeError(
                    "Cannot generate order: no restaurant has dishes "
                    "with a positive price"
                )

            restaurant_id = restaurant_row[0]

            cur.execute("""
                SELECT id, name, price
                FROM public.dishes
                WHERE restaurant_id = %s AND price > 0
                ORDER BY random()
                LIMIT %s;
            """, (restaurant_id, random.randint(1, 3)))

            dishes = cur.fetchall()

            if not dishes:
                raise RuntimeError(
                    f"Cannot generate order: no eligible dishes "
                    f"for restaurant {restaurant_id}"
                )

            items = []
            total_amount = Decimal("0.00")

            for dish in dishes:
                quantity = random.randint(1, 3)
                price = Decimal(str(dish[2])).quantize(
                    CENT,
                    rounding=ROUND_HALF_UP,
                )
                line_total = price * quantity
                total_amount += line_total

                items.append({
                    "dish_id": dish[0],
                    "name": html.unescape(dish[1]) if dish[1] else "Dish",
                    "quantity": quantity,
                    "unit_price": float(price),
                })

    return {
        "event_id": str(uuid.uuid4()),
        "event_type": "order_created",
        "user_id": user_id,
        "restaurant_id": restaurant_id,
        "items": items,
        "total_amount": float(
            total_amount.quantize(CENT, rounding=ROUND_HALF_UP)
        ),
        "status": "created",
        "timestamp": datetime.now(timezone.utc).strftime(
            "%Y-%m-%d %H:%M:%S"
        ),
    }


def generate_ecommerce_event():
    with closing(get_db_connection()) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id FROM public.users ORDER BY random() LIMIT 1;"
            )
            user_row = cur.fetchone()

            if not user_row:
                raise RuntimeError(
                    "Cannot generate ecommerce event: public.users is empty"
                )

            user_id = str(user_row[0])

            cur.execute("""
                SELECT id, price
                FROM public.dishes
                WHERE price > 0
                ORDER BY random()
                LIMIT 1;
            """)
            dish_row = cur.fetchone()

            if not dish_row:
                return None

            item_id = str(dish_row[0])
            price = Decimal(str(dish_row[1])).quantize(
                CENT,
                rounding=ROUND_HALF_UP,
            )

    action = random.choices(
        ["view", "add_to_cart", "buy"],
        weights=[70, 20, 10],
        k=1,
    )[0]

    return {
        "event_id": str(uuid.uuid4()),
        "user_id": user_id,
        "item_id": item_id,
        "category": "dishes",
        "action": action,
        "price": float(price) if action == "buy" else 0.0,
        "timestamp": datetime.now(timezone.utc).strftime(
            "%Y-%m-%d %H:%M:%S"
        ),
    }


def main():
    print("Starting extended generator...")
    print(f"Connecting to Kafka: {KAFKA_BOOTSTRAP_SERVERS}")

    producer = None

    while producer is None:
        try:
            producer = KafkaProducer(
                bootstrap_servers=[KAFKA_BOOTSTRAP_SERVERS],
                value_serializer=lambda value: json.dumps(
                    value,
                    ensure_ascii=False,
                ).encode("utf-8"),
            )
            print("Kafka connected")
        except Exception as exc:
            print(f"Kafka waiting: {exc}")
            time.sleep(3)

    try:
        while True:
            try:
                ecommerce_event = generate_ecommerce_event()

                if ecommerce_event is not None:
                    producer.send(
                        KAFKA_EVENTS_TOPIC,
                        value=ecommerce_event,
                    ).get(timeout=120)

                    send_to_minio(ecommerce_event, folder="events")

                    print(
                        "Ecommerce event | "
                        f"action={ecommerce_event['action']} | "
                        f"item={ecommerce_event['item_id']}"
                    )

                order = generate_order_event()

                producer.send(
                    KAFKA_TOPIC,
                    value=order,
                ).get(timeout=120)

                send_to_minio(order, folder="orders")

                print(
                    "Order created | "
                    f"user={order['user_id']} | "
                    f"amount={order['total_amount']:.2f}"
                )

                time.sleep(random.uniform(0.5, 1.5))

            except Exception as exc:
                print(f"Generator error: {exc}")
                time.sleep(3)

    except KeyboardInterrupt:
        print("Stopping generator...")

    finally:
        try:
            producer.flush(timeout=30)
        except Exception as exc:
            print(f"Kafka flush error: {exc}")

        producer.close(timeout=30)
        print("Generator stopped")


if __name__ == "__main__":
    main()
