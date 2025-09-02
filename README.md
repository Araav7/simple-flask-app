# Flask App

A Flask application demonstrating CRUD and async operations with Datadog monitoring enabled

## Features

- ✅ Basic CRUD operations with PostgreSQL
- ✅ Async/await operations with parallel API calls
- ✅ Datadog APM integration for distributed tracing
- ✅ JSON structured logging with trace correlation
- ✅ Simple web interface for testing

## Prerequisites

- Python 3.12+
- PostgreSQL
- Datadog Agent (optional, for APM tracing)

## Installation

1. **Clone the repository** (or navigate to the project directory)

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up PostgreSQL**
   ```bash
   # On macOS with Homebrew
   brew install postgresql
   brew services start postgresql
   
   # Create the database
   createdb flaskdemo
   ```

## Running the Application

Simply run:
```bash
python3 app.py
```

The app will start on `http://localhost:8004`

## Main Endpoints

### Web Interface
- `/` - Homepage with user registration form
- `/users` - View all registered users
- `/async-test` - Interactive async operations test page

### API Endpoints
- `/async-example` - Demonstrates parallel async operations with tracing
- `/welcome` - User registration endpoint
- `/edit/<id>` - Edit user
- `/delete/<id>` - Delete user

## Datadog Integration

The application automatically instruments:
- Flask routes
- HTTP requests (httpx, aiohttp)
- Database queries (SQLAlchemy)
- Custom trace spans for async operations

### Setting up Datadog Agent (Optional)

To see traces in Datadog:

1. Install the Datadog Agent
2. Set your API key
3. Ensure the agent is running on port 8126
4. The Flask app will automatically send traces to the agent

## Key Technologies

- **Flask** - Web framework
- **SQLAlchemy** - ORM for PostgreSQL
- **httpx/aiohttp** - Async HTTP clients
- **ddtrace** - Datadog APM library
- **asyncio** - Python async/await support

## Async Example Explained

The `/async-example` endpoint demonstrates:
1. Two operations that would normally take 2 seconds sequentially
2. Using `asyncio.gather()` to run them in parallel
3. Total execution time of ~1 second (not 2!)
4. Full tracing visibility in Datadog APM