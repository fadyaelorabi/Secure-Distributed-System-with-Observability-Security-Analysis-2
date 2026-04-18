# Secure Distributed System – Design, Security, Flow, and Testing Strategy
## 1. System Design
<img width="1024" height="1536" alt="Distributed system architecture flowchart" src="https://github.com/user-attachments/assets/c47fbe7e-e1a4-4417-96cb-af9801467976" />

The system follows a layered distributed architecture:

Client
→ Nginx (Gateway)
→ API Cluster (api1, api2, api3)
→ RabbitMQ
→ Worker
→ PostgreSQL


### Design Decisions

- **Nginx as Gateway**
  - Central entry point
  - Handles load balancing, HTTPS, and rate limiting
  - Reduces complexity in API services

- **Multiple API Instances**
  - Horizontal scaling
  - Fault tolerance
  - Load distribution

- **RabbitMQ (Message Broker)**
  - Decouples API from processing
  - Enables asynchronous execution
  - Prevents blocking under load

- **Worker Service**
  - Handles background processing
  - Ensures separation of concerns

- **PostgreSQL Database**
  - Stores audit logs
  - Tracks request lifecycle
  - Enables observability

---

## 2. Security Measures

### 2.1 HTTPS (Transport Security)

- TLS 1.2 / 1.3 enforced in Nginx
- Encrypts all client-server communication
- Prevents MITM attacks

Proof:
- HTTP → token visible
- HTTPS → encrypted traffic (Wireshark)

---

### 2.2 JWT Authentication

- Every request must include a valid JWT
- Token contains:
  - service identity
  - expiration time

Validation:
- Missing token → 403
- Invalid token → 403

---

### 2.3 Rate Limiting

Configured in Nginx:


limit_req_zone $binary_remote_addr rate=5r/s


- Applied per client IP
- Protects against abuse and DoS attacks
- Excess requests → HTTP 429

---

### 2.4 Service Validation (Worker)

Worker verifies:


if data["service"] != "api" → reject


Prevents:
- Unauthorized message injection
- Fake task execution

---

### 2.5 Secret Management

- Secrets stored in `.env`
- Not hardcoded in source code
- Injected via Docker

---

## 3. Request Flow

Each request follows a strict lifecycle:

### Step 1 – Client Request

- Client sends HTTPS request
- Includes JWT token

---

### Step 2 – Nginx

- Terminates TLS
- Applies rate limiting
- Forwards request to API cluster

---

### Step 3 – API

- Validates JWT
- Generates `request_id` (UUID)
- Logs:
  - RECEIVED
  - AUTHENTICATED

- Sends message to RabbitMQ
- Logs:
  - QUEUED

---

### Step 4 – RabbitMQ

- Stores message in queue
- Delivers to worker

---

### Step 5 – Worker

- Consumes message
- Logs:
  - CONSUMED

- Validates service identity
- Processes task
- Logs:
  - PROCESSED or FAILED

---

### Step 6 – Database

Each event is stored with:

- timestamp
- service
- request_id
- action
- status
- source

---

## 4. Request Tracking

Each request has a unique `request_id`.

This ID:

- Is generated at API level
- Travels across all services
- Links all logs together

### Example lifecycle:


RECEIVED
AUTHENTICATED
QUEUED
CONSUMED
PROCESSED


This enables:

- Full traceability
- Debugging
- Audit compliance

---

## 5. MITM Attack Demonstration

### HTTP Mode

- Traffic captured using Wireshark
- Observations:
  - Authorization header visible
  - Payload readable

Conclusion:
- Vulnerable to interception

---

### HTTPS Mode

- Traffic encrypted using TLS
- Observations:
  - Only TLS packets visible
  - No readable data

Conclusion:
- Secure against MITM

---

## 6. Testing Strategy

Testing is automated using scripts to ensure repeatability.

### Why scripts are used

Manual testing is unreliable.

Scripts ensure:

- Consistent results
- Reproducible scenarios
- Accurate measurement of system behavior

---

### Scripts Overview

#### test_normal.sh

- Sends single request
- Verifies system availability

---

#### test_load.sh

- Sends multiple requests
- Verifies load balancing

---

#### test_rate_limit.sh

- Sends parallel requests
- Verifies rate limiting

---

#### test_unauthorized.sh

- Sends request without token
- Verifies authentication enforcement

---

#### generate_token.py

- Generates valid JWT tokens
- Ensures correct authentication testing

---

## 7. Key Observations

- Rate limiting is time-based, not count-based
- Parallel requests are required to trigger limits
- Rejected requests are faster than successful ones
- Logs provide a complete story of each request

---

## 8. Conclusion

The system demonstrates:

- Secure communication using HTTPS
- Scalable architecture with load balancing
- Protection against abuse via rate limiting
- Full observability through audit logging
- Real-world security validation via MITM simulation
