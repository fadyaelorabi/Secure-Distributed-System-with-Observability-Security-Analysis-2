from fastapi import FastAPI, Request, HTTPException
import jwt
import pika
import json
import socket
import uuid
import psycopg2
import datetime

app = FastAPI()

import os
SECRET = os.getenv("SECRET_KEY")

if not SECRET:
    raise ValueError("SECRET_KEY not set")
# =========================
# JWT Verification
# =========================
def verify_token(request: Request, request_id):

    auth = request.headers.get("Authorization")

    if not auth:
        log_event("api", request_id, "AUTH_FAILED", "failure", "client")
        raise HTTPException(status_code=403, detail="Missing token")

    token = auth.split(" ")[1]

    try:
        payload = jwt.decode(token, SECRET, algorithms=["HS256"])
        return payload

    except:
        log_event("api", request_id, "AUTH_FAILED", "failure", "client")
        raise HTTPException(status_code=403, detail="Invalid token")


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
def connect_rabbitmq():
    import time
    while True:
        try:
            connection = pika.BlockingConnection(
                pika.ConnectionParameters('rabbitmq')
            )
            return connection
        except:
            print("Waiting for RabbitMQ...")
            time.sleep(5)


# =========================
# API Endpoint
# =========================
@app.get("/task")
def task(request: Request):

    # Generate Request ID
    request_id = str(uuid.uuid4())

    # STATE 1: RECEIVED
    log_event("api", request_id, "RECEIVED", "success", "client")

    # JWT Validation
    payload = verify_token(request, request_id)
    # STATE 2: AUTHENTICATED
    log_event("api", request_id, "AUTHENTICATED", "success", "api")

    hostname = socket.gethostname()

    # Connect to RabbitMQ
    connection = connect_rabbitmq()
    channel = connection.channel()

    channel.queue_declare(queue='tasks')

    # Prepare message
    message = {
        "request_id": request_id,
        "service": payload["service"],
        "from": hostname
    }

    # Send message
    channel.basic_publish(
        exchange='',
        routing_key='tasks',
        body=json.dumps(message)
    )

    connection.close()

    # STATE 3: QUEUED
    log_event("api", request_id, "QUEUED", "success", "api")

    return {
        "status": "task sent",
        "handled_by": hostname,
        "request_id": request_id
    }