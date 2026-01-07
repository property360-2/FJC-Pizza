"""
Gunicorn configuration file for FJC Pizza Sales & Inventory System
Optimized for production deployment on Render
"""

import multiprocessing
import os

# Server socket
bind = f"0.0.0.0:{os.environ.get('PORT', '8000')}"
backlog = 2048

# Worker processes
# On Render's free tier, limit to 2 workers to avoid memory issues
# On paid tiers, use CPU count
workers = int(os.environ.get('GUNICORN_WORKERS', '2'))
worker_class = 'sync'
worker_connections = 1000
max_requests = 1000  # Restart workers after 1000 requests to prevent memory leaks
max_requests_jitter = 50  # Add randomness to prevent all workers restarting at once
timeout = 120  # Increased from default 30s for complex forecasting operations
keepalive = 5

# Logging
accesslog = '-'  # Log to stdout
errorlog = '-'   # Log to stderr
loglevel = 'info'
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = 'fjc_pizza_gunicorn'

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL (if needed in future)
keyfile = None
certfile = None

# Performance tuning
preload_app = True  # Load application code before forking workers (saves memory)
