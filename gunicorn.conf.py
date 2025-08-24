# Gunicorn configuration for ODIADEV Nigerian TTS
# Optimized for Render deployment

import os

# Server socket
bind = f"0.0.0.0:{os.environ.get('PORT', 5000)}"
backlog = 2048

# Worker processes
workers = 1  # Single worker for free tier to save memory
worker_class = "sync"
worker_connections = 1000
timeout = 120  # Increased for TTS generation
keepalive = 2

# Memory optimization
max_requests = 1000  # Restart workers after 1000 requests to prevent memory leaks
max_requests_jitter = 50
preload_app = False  # Don't preload to save startup memory

# Logging
accesslog = "-"  # Log to stdout
errorlog = "-"   # Log to stderr
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Process naming
proc_name = "odiadev-tts"

# Restart workers gracefully
graceful_timeout = 30