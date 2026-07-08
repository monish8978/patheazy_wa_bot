# Patheazy Labs Chatbot System

A production-grade, highly scalable REST API Chatbot and administrative simulation dashboard built for **Patheazy Labs**. 

The application utilizes **FastAPI** for asynchronous high-performance REST endpoints, **Redis** for dialogue state tracking and session management, and **MySQL** for durable transaction auditing and conversation message logging.

---

## 🛠️ Architecture Stack

- **Backend REST API Engine**: FastAPI (Asynchronous Python 3.11)
- **State Machine / Session Store**: Redis Key-Value Cache
- **Database Engine**: MySQL 8.0 (Relational persistent storage for logs and audits)
- **Container Orchestration**: Docker & Docker Compose
- **Visual Validation Suite**: Glassmorphism interactive mobile simulator and dashboard panel.

---

## 🚀 Running the Project

### Prerequisites
Make sure you have [Docker](https://www.docker.com/) and [Docker Compose](https://docs.docker.com/compose/) installed on your machine.

### Spin up the Application Cluster
To build the application image and run all services (FastAPI, Redis, MySQL) in the background:

```bash
docker-compose up --build -d
```

### Accessing the Web Services
- **Control Center & Interactive Simulator**: [http://localhost:9103](http://localhost:9103)
- **FastAPI OpenAPI Documentation**: [http://localhost:9103/docs](http://localhost:9103/docs)
- **Health Check Probe**: [http://localhost:9103/health](http://localhost:9103/health)

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
```

### 3. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the FastAPI Application
```bash
uvicorn app.main:app --reload --port 9103
```

---

## 📱 Conversational Flow Coverages

The chatbot implements Patheazy Labs' digital assistant flows:
1. **Book a Lab Test**:
   - **Home Collection (Doorstep Visit)**: Sequentially collects user name, mobile number, gender, age, pincode, full address, requested laboratory test names, and preferred date/time.
   - **Walk-in (Nearest Centre)**: Sequentially collects user name, mobile number, gender, and age to register the appointment.
2. **Connect with a Live Agent**: Instantly clears active session state and routes the user to a live support executive queue.
3. **Audit Logging**: Saves all user messages, bot replies, and payloads in MySQL for complete conversational history auditing.

---

## 📡 REST API & cURL Reference

You can interact with the chatbot engine, retrieve logs, and reset sessions using the following endpoints:

### 1. Process Dialogue / Dialogue Simulator
This endpoint simulates sending user messages or button clicks to the state machine engine:

```bash
curl -X POST "http://localhost:9103/api/simulate" \
     -H "Content-Type: application/json" \
     -d '{
       "sessionid": "PATHEAZY-USER-99",
       "query": "FLOW_BOOK_LAB"
     }'
```

### 2. Fetch Conversation Audit Logs
Retrieve the complete conversation message stream for a specific session:

```bash
curl -X GET "http://localhost:9103/api/logs/PATHEAZY-USER-99"
```

### 3. Reset User Session State
Clears active Redis session states and deletes transactional message logs for clean validation tests:

```bash
curl -X POST "http://localhost:9103/api/reset/PATHEAZY-USER-99"
```
