import pika
import json
import time
import psycopg2
import datetime

# =========================
# Database Logging
# =========================
def log_event(service, request_id, action, status, source):
    try:
        conn = psycopg2.connect(
            host="db",
            database="logsdb",
            user="admin",
            password="admin"
        )
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO logs (timestamp, service, request_id, action, status, source)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            datetime.datetime.now(),
            service,
            request_id,
            action,
            status,
            source
        ))

        conn.commit()
        cur.close()
        conn.close()

    except Exception as e:
        print(f"[DB ERROR] {e}")


# =========================
# RabbitMQ Connection (retry safe)
# =========================
def connect():
    while True:
        try:
            connection = pika.BlockingConnection(
                pika.ConnectionParameters('rabbitmq')
            )
            print("Connected to RabbitMQ")
            return connection
        except pika.exceptions.AMQPConnectionError:
            print("Waiting for RabbitMQ...")
            time.sleep(5)


# =========================
# Message Processing
# =========================
def callback(ch, method, properties, body):
    try:
        data = json.loads(body)
    except:
        print("[AUDIT] Invalid JSON")
        ch.basic_nack(delivery_tag=method.delivery_tag)
        return

    request_id = data.get("request_id")

    # STATE 4: CONSUMED
    log_event("worker", request_id, "CONSUMED", "success", "worker")

    # Weak validation (acceptable for assignment)
    if data.get("service") != "api":
        log_event("worker", request_id, "FAILED", "failure", "worker")
        ch.basic_nack(delivery_tag=method.delivery_tag)
        return

    try:
        print("Processing task from:", data.get("from"))

        # Simulate processing
        time.sleep(1)

        # STATE 5: PROCESSED
        log_event("worker", request_id, "PROCESSED", "success", "worker")

        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        log_event("worker", request_id, "FAILED", "failure", "worker")
        ch.basic_nack(delivery_tag=method.delivery_tag)


# =========================
# Start Worker
# =========================
connection = connect()
channel = connection.channel()

channel.queue_declare(queue='tasks')

channel.basic_consume(
    queue='tasks',
    on_message_callback=callback,
    auto_ack=False
)

print("Worker started...")
channel.start_consuming()