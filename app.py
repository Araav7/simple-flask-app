from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
import logging
from logging.handlers import RotatingFileHandler
from pythonjsonlogger import jsonlogger
from dotenv import load_dotenv
import os
import asyncio
import aiohttp
import httpx
import time
import random
from concurrent.futures import ThreadPoolExecutor

load_dotenv()
# ---------------- ddtrace setup ----------------
from ddtrace import patch_all, patch, tracer


patch_all()           # Auto-instruments Flask, SQLAlchemy, httpx, aiohttp, etc.
patch(logging=True)     # Injects trace_id and span_id into logs
# ------------------------------------------------

app = Flask(__name__)

# PostgreSQL config
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://@localhost/flaskdemo'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ---------------- JSON Logging Setup ----------------
if not os.path.exists('logs'):
    os.mkdir('logs')

log_file = '/Users/araavind.senthil/flaskapp/logs/app.log'
handler = RotatingFileHandler(log_file, maxBytes=10240, backupCount=5)

json_formatter = jsonlogger.JsonFormatter(
    fmt='%(asctime)s %(levelname)s %(module)s %(message)s %(dd.trace_id)s %(dd.span_id)s',
    rename_fields={
        'asctime': 'timestamp',
        'levelname': 'level',
        'module': 'module',
        'message': 'message'
    }
)

handler.setFormatter(json_formatter)
handler.setLevel(logging.INFO)

app.logger.setLevel(logging.INFO)
app.logger.addHandler(handler)
app.logger.info('Application startup')
# ----------------------------------------------------

# ---------------------- Models ----------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
# ----------------------------------------------------

# ---------------------- Routes ----------------------
@app.route('/')
def index():
    app.logger.info("Accessed homepage '/'")
    return render_template('index.html')

@app.route('/welcome', methods=['GET', 'POST'])
def welcome():
    if request.method == 'POST':
        name = request.form.get('name')
        if name:
            new_user = User(name=name)
            db.session.add(new_user)
            db.session.commit()
            app.logger.info(f"New user added: {name}")
            return render_template('welcome.html', name=name)
        else:
            app.logger.warning("POST to /welcome without a name")
    return redirect(url_for('index'))

@app.route('/users')
def users():
    all_users = User.query.all()
    app.logger.info(f"Fetched {len(all_users)} users")
    return render_template('users.html', users=all_users)

@app.route('/async-test')
def async_test():
    app.logger.info("Accessed async test dashboard")
    return render_template('async_test.html')

@app.route('/delete/<int:id>', methods=['POST'])
def delete_user(id):
    user = User.query.get_or_404(id)
    db.session.delete(user)
    db.session.commit()
    app.logger.info(f"Deleted user with ID {id}")
    return redirect(url_for('users'))

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_user(id):
    user = User.query.get_or_404(id)
    if request.method == 'POST':
        new_name = request.form.get('name')
        app.logger.info(f"Edited user {id}: name changed from '{user.name}' to '{new_name}'")
        user.name = new_name
        db.session.commit()
        return redirect(url_for('users'))
    return render_template('edit.html', user=user)

@app.route('/favicon.ico')
def favicon():
    return '', 204

# -------------------- Simple Async Example --------------------
@app.route('/async-example')
async def async_example():
    """
    A simple async route that demonstrates parallel API calls.
    This is great for beginners to understand async operations!
    """
    
    # Log that we're starting the async operation
    app.logger.info("Starting simple async example")
    
    # Create a trace span for Datadog to track this operation
    with tracer.trace("async_example.main"):
        
        # Define two async tasks that will run IN PARALLEL
        # This is the power of async - both tasks run at the same time!
        task1 = fetch_github_zen()  # This will take ~1 second
        task2 = fetch_random_quote()  # This will also take ~1 second
        
        # await asyncio.gather() runs both tasks SIMULTANEOUSLY
        # Without async, these would take 2 seconds total (1+1)
        # With async, they take only ~1 second total (running in parallel)
        start_time = time.time()
        results = await asyncio.gather(task1, task2)
        end_time = time.time()
        
        # Calculate how long it took
        duration = end_time - start_time
        
        app.logger.info(f"Completed async operations in {duration:.2f} seconds")
        
        # Return the results as JSON
        return jsonify({
            "github_message": results[0],
            "quote": results[1],
            "total_time_seconds": round(duration, 2),
            "note": "Both API calls ran in parallel, so total time is ~1 second, not 2!"
        })

async def fetch_github_zen():
    """
    Async function to fetch a zen message from GitHub.
    The 'async' keyword means this function can be paused and resumed.
    """
    
    # Create a trace span for this specific operation
    with tracer.trace("fetch.github_zen"):
        
        # Use httpx for async HTTP requests
        async with httpx.AsyncClient() as client:
            try:
                # The 'await' keyword pauses here until the request completes
                # While waiting, other async tasks can run!
                response = await client.get("https://api.github.com/zen")
                
                # Simulate some processing time
                await asyncio.sleep(1)  # Wait 1 second (async)
                
                return response.text
                
            except Exception as e:
                app.logger.error(f"Error fetching GitHub zen: {e}")
                return f"Error: {str(e)}"

async def fetch_random_quote():
    """
    Another async function that simulates fetching a quote.
    This runs at the SAME TIME as fetch_github_zen()!
    """
    
    # Create a trace span for this operation
    with tracer.trace("fetch.random_quote"):
        
        # Simulate an API call with a 1-second delay
        await asyncio.sleep(1)  # This runs WHILE fetch_github_zen is also running
        
        # Return a random quote
        quotes = [
            "The only way to do great work is to love what you do. - Steve Jobs",
            "Code is poetry. - WordPress",
            "First, solve the problem. Then, write the code. - John Johnson",
            "Programs must be written for people to read. - Harold Abelson"
        ]
        
        return random.choice(quotes)

# ----------------------------------------------------

# ---------------------- Main ------------------------
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=8004)
# ----------------------------------------------------