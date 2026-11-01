import json
import os
import signal
import time
from datetime import datetime, timezone

import boto3
from botocore.exceptions import ClientError
from kafka import KafkaConsumer


KAFKA_BOOTSTRAP_SERVERS = os.getenv(
    "KAFKA_BOOTSTRAP_SERVERS", "kafka:29092"
)
CONSUMER_GROUP = os.getenv(
    "KAFKA_CONSUMER_GROUP", "seaweedfs-archiver-group"
)
S3_ENDPOINT_URL = os.getenv(
    "S3_ENDPOINT_URL", "http://seaweedfs:9000"
)
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY", "seaweedfs")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY", "seaweedfs")
S3_BUCKET = os.getenv("S3_BUCKET", "raw-events")

S3_PREFIX = os.getenv("S3_PREFIX", "test-archiver").strip("/")

TOPIC_FOLDERS = {
    "order-events": "orders",
    "ecommerce-events": "events",
}

running = True


def stop_handler(signum, frame):
    global running
    running = False


signal.signal(signal.SIGTERM, stop_handler)
signal.signal(signal.SIGINT, stop_handler)


s3 = boto3.client(
    "s3",
    endpoint_url=S3_ENDPOINT_URL,
    aws_access_key_id=S3_ACCESS_KEY,
    aws_secret_access_key=S3_SECRET_KEY,
)


def ensure_bucket():
    try:
        s3.head_bucket(Bucket=S3_BUCKET)
    except ClientError as exc:
        code = str(exc.response.get("Error", {}).get("Code", ""))
        if code in ("404", "NoSuchBucket", "NotFound"):
            s3.create_bucket(Bucket=S3_BUCKET)
        else:
            raise


def archive_message(topic, partition, offset, event):
    folder = TOPIC_FOLDERS[topic]

    event_id = event.get("event_id")
    if not event_id:
        event_id = f"{topic}-{partition}-{offset}"

    timestamp = event.get("timestamp")
    date_part = None

    if timestamp:
        try:
            date_part = datetime.fromisoformat(
                str(timestamp).replace("Z", "+00:00")
            ).date().isoformat()
        except ValueError:
            pass

    if not date_part:
        date_part = datetime.now(timezone.utc).date().isoformat()

    key_prefix = f"{S3_PREFIX}/{folder}" if S3_PREFIX else folder
    key = f"{key_prefix}/{date_part}/{event_id}.json"

    body = json.dumps(
        event, ensure_ascii=False
    ).encode("utf-8")

    s3.put_object(
        Bucket=S3_BUCKET,
        Key=key,
        Body=body,
        ContentType="application/json",
    )

    print(
        f"Archived topic={topic} partition={partition} "
        f"offset={offset} key={key}",
        flush=True,
    )


def main():
    ensure_bucket()

    consumer = KafkaConsumer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS.split(","),
        group_id=CONSUMER_GROUP,
        enable_auto_commit=False,
        auto_offset_reset="latest",
        value_deserializer=lambda value: json.loads(
            value.decode("utf-8")
        ),
    )

    consumer.subscribe(list(TOPIC_FOLDERS.keys()))

    print(
        f"Consumer started; group={CONSUMER_GROUP}; "
        f"prefix={S3_PREFIX}; topics={list(TOPIC_FOLDERS.keys())}",
        flush=True,
    )

    try:
        while running:
            records = consumer.poll(timeout_ms=1000)

            for topic_partition, messages in records.items():
                for message in messages:
                    archive_message(
                        message.topic,
                        message.partition,
                        message.offset,
                        message.value,
                    )

                    consumer.commit()
    finally:
        consumer.close()
        print("Consumer stopped", flush=True)


if __name__ == "__main__":
    while True:
        try:
            main()
            break
        except Exception as exc:
            if not running:
                break
            print(
                f"Consumer error: {exc}. Retrying in 5 seconds.",
                flush=True,
            )
            time.sleep(5)