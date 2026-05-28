import logging
from datetime import datetime

def setup_logger():
    # 1. Create a custom logger
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)  # Set overall threshold

    # 2. Create handlers (where logs go)
    c_handler = logging.StreamHandler()    # Console
    f_handler = logging.FileHandler('file.log') # File

    # 3. Create formatters and add them to handlers
    format_str = logging.Formatter('%(asctime)s | %(levelname)s | %(name)s | %(message)s',datefmt='%Y-%m-%d %H:%M:%S')
    c_handler.setFormatter(format_str)
    f_handler.setFormatter(format_str)

    # 4. Add handlers to the logger
    logger.addHandler(c_handler)
    logger.addHandler(f_handler)
    
    return logger

