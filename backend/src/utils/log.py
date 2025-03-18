import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask
from flask import current_app as app
from .env import Config

# Configure logging
def setup_logging():
    # if not ./log directory, create it
    
    if not os.path.exists(Config.LOG_DIR, "./log"):
        os.makedirs(Config.LOG_DIR, "./log"))
    log_dir =  os.path.join(Config.LOG_DIR, "./log")
    os.makedirs(log_dir, exist_ok=True)  # Create directory if it doesn’t exist
    
    # Create a rotating file handler (limits file size, rotates logs)
    log_file = os.path.join(log_dir, "app.log")
    handler = RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB per file
        backupCount=5  # Keep 5 backup files
    )
    
    # Set log format
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    
    # Set log level
    handler.setLevel(logging.INFO)
    
    # Add handler to the app logger
    app.logger.handlers.clear()  # Clear default handlers (console)
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)
    
    # Log startup
    app.logger.info("Flask app started")