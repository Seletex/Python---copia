
# Gunicorn configuration file
import multiprocessing

bind = "0.0.0.0:8000"
workers = 2  # Adjust based on available resources
threads = 4
timeout = 120
worker_class = "gthread"
loglevel = "info"
accesslog = "-"  # Log to stdout
errorlog = "-"   # Log to stderr
