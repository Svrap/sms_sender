import logging


def get_logger(module: str,
               log_format: str='%(asctime)s %(levelname)s %(name)s %(funcName)s [PID:%(process)d TID:%(thread)d] %(message)s',
               log_level=logging.INFO,
               formatter=logging.Formatter) -> logging.Logger:
    """
    Creates a logger
    :param module: Name of module
    :param log_format: Logging format
    :param log_level: Logging level
    :param formatter: Formatter class
    :return: logger object
    """

    logger = logging.getLogger(module)
    logger.setLevel(log_level)
    ch = logging.StreamHandler()
    ch.setLevel(log_level)
    ch.setFormatter(formatter(log_format))
    logger.addHandler(ch)
    return logger

