import logging

def log(level, value):
    if level == 'info':
        logging.info(value)
    elif level == 'debug':
        logging.debug(value)
    elif level == 'warning':
        logging.warning(value)
    elif level == 'error':
        logging.error(value)
    elif level == 'critical':
        logging.critical(value)