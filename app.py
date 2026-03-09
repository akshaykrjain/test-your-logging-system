import logging
import random
import time
import os

logging.basicConfig(
    level=os.getenv('LOG_LEVEL', 'DEBUG'),
    format='%(asctime)s - %(levelname)s - %(message)s'
)

messages = [
    "Processing user request",
    "Database connection established",
    "Cache hit for key",
    "API response received",
    "Configuration loaded",
    "Health check passed",
    "Memory usage normal",
    "Task completed successfully",
    "Retrying failed operation",
    "Connection timeout occurred",
    "Invalid input detected",
    "Service unavailable",
    "Authentication successful",
    "Rate limit approaching",
    "Backup completed"
]

levels = [logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL]

while True:
    level = random.choice(levels)
    message = random.choice(messages)
    logging.log(level, message)
    time.sleep(random.randint(10, 15))
