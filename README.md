# BOB Bank Chatbot System

A production-grade, highly scalable REST API Chatbot and administrative CRM system built for **Bank of Bhutan (BOB)**. 

The application utilizes **FastAPI** for asynchronous high-performance REST endpoints, **Redis** for state tracking and session management, **Celery** for offloading high-latency CRM tickets, and **MySQL** for durable transaction auditing and ticket storage.

---

## 🛠️ Architecture Stack

- **Backend REST API Engine**: FastAPI (Asynchronous Python 3.11)
- **State Machine / Session Store**: Redis Key-Value Cache
- **Database Engine**: MySQL 8.0 (Relational persistent storage)
- **Background Worker Engine**: Celery (Distributed task queues)
- **Container Orchestration**: Docker & Docker Compose
- **Visual Validation Suite**: Glassmorphism interactive mobile simulator and CRM dashboard panel.

---

## 🚀 Running the Project

### Prerequisites
Make sure you have [Docker](https://www.docker.com/) and [Docker Compose](https://docs.docker.com/compose/) installed on your machine.

### Spin up the Application Cluster
To build the application image and run all services (FastAPI, Redis, Celery, MySQL) in the background:

```bash
docker-compose up --build -d
```

### Accessing the Web Services
- **Control Center & Interactive Simulator**: [http://localhost:9101](http://localhost:9101)
- **FastAPI OpenAPI Documentation**: [http://localhost:9101/docs](http://localhost:9101/docs)
- **Health Check Probe**: [http://localhost:9101/health](http://localhost:9101/health)

---

## 💻 Local Development Setup (Without Docker)

If you prefer running services locally on your host machine:

### 1. Start MySQL & Redis
Ensure standard MySQL and Redis services are active locally.

### 2. Configure Environment Variables
Create a `.env` file in the root directory (based on `.env.example`):
```ini
DATABASE_URL=mysql+aiomysql://bob_user:bob_password@localhost:3306/bob_db
DATABASE_SYNC_URL=mysql+pymysql://bob_user:bob_password@localhost:3306/bob_db
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### 3. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the FastAPI Application
```bash
uvicorn app.main:app --reload
```

### 5. Launch Celery Worker Process (in a separate terminal)
```bash
celery -A app.celery_app.celery_app worker --loglevel=info
```

---

## 📱 Conversational Flow Coverages

The chatbot implements 100% of the bank's user scenarios:
1. **mBoB Mobile App Flows**: Accounts validation (Thumbprint vs Signature), simulated OTP verification loops, MPIN recovery flows, Device registration, limits, category shifts, and Transfer failures.
2. **Debit & Credit Cards**: Pin setups, activations, card blockages, fees, ATM limitations, and fraud controls.
3. **KYC Management**: Domestic branch visits vs Overseas scanning and email controls.
4. **GoBoB Wallet Support**: Signup workflows, forgot MPIN OTP overrides, lost device blocking.
5. **Automated Transfer System (ATS)**: Detailed FAQ matrices covering Minor accounts and limits.
6. **Accounts & Loan Apply**: Direct digital integrations using Bhutan NDI interfaces.
7. **CRM Ticketing routing**: Multi-step ticket registration state machines running background queues via Celery.

---

## 📡 REST API & cURL Reference

You can interact with the chatbot engine, retrieve ticket audits, and view conversation histories using the following endpoints:

### 1. Process Dialogue / Dialogue Simulator
This endpoint simulates sending user messages or button clicks to the state machine engine:

```bash
curl -X POST "http://localhost:9101/api/simulate" \
     -H "Content-Type: application/json" \
     -d '{
       "user_id": "BOB-USER-99",
       "message": "Signature Account",
       "payload": "MBOB_REG_SIG"
     }'
```

### 2. Fetch CRM Support Tickets
Fetches all tickets logged in the database by background Celery worker threads:

```bash
curl -X GET "http://localhost:9101/api/tickets"
```

### 3. Fetch Conversation Audit Logs
Retrieve the complete conversation message stream for a specific session:

```bash
curl -X GET "http://localhost:9101/api/logs/BOB-USER-99"
```

### 4. Reset User Session State
Clears active Redis session states and deletes transactional message logs for clean validation tests:

```bash
curl -X POST "http://localhost:9101/api/reset/BOB-USER-99"
```
