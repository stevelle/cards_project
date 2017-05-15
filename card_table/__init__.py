import logging

# PoC: debug logging
log_level = logging.DEBUG

logging.basicConfig(
    format='[%(asctime)s] [%(process)d] [%(name)s] [%(levelname)s] '
           '%(message)s',
    datefmt='%Y-%m-%d %H:%M:%S +0000', level=log_level)
