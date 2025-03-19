import logging
from logging.handlers import RotatingFileHandler
import os

from .env import Config

def setup_logging():
    log_dir = os.path.join("./log")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "app.log")
    # use config to get hostname unless it is not set use os
    hostname = Config.get("HOSTNAME") or os.uname().nodename
    
    handler = RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5)

    if Config.get("MODE") == "debug":
        loglevel = logging.DEBUG
    else:
        loglevel = logging.INFO
    
    logging.basicConfig(
        level=loglevel,
        format=f'%(asctime)s {hostname} %(name)s[%(process)d]: %(levelname)s %(message)s',
        datefmt='%b %d %H:%M:%S',
        handlers=[handler]
    )