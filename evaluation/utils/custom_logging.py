import logging

# formatter, color output
class CustomFormatter(logging.Formatter):
    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    #format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)"
    format = "%(asctime)s - %(name)s - %(levelname)s - %(threadName)s - (%(filename)s:%(lineno)d):%(message)s"

    FORMATS = {
        logging.DEBUG: grey + format + reset,
        logging.INFO: grey + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)
    
def _add_console_handler(logger, level):
    logging_console_handler = logging.StreamHandler()
    logging_console_handler.setLevel(level)
    logging_console_handler.setFormatter(CustomFormatter())
    logger.addHandler(logging_console_handler)

def _add_file_handler(logger, level, log_file_path = "main.log"):
    logging_file_handler = logging.FileHandler(log_file_path)
    logging_file_handler.setLevel(level)
    logging_file_handler.setFormatter(logging.Formatter(
        # "[%(asctime)s::%(name)-8s::%(levelname)-8s::%(threadName)-15s]: %(message)s"
        "%(asctime)s - %(name)s - %(levelname)s - %(threadName)s - (%(filename)s:%(lineno)d):%(message)s"
    ))
    logger.addHandler(logging_file_handler)

def setup_logging(console_output=True, log_level_console=logging.INFO, file_output=False, log_file_path='main.log', log_level_file=logging.INFO):
    # Create a default logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)  # Set the logger level to the lowest level, handlers will filter from here

    # When setting the propagate attribute to False,
    # log messages won't be passed to the handlers of higher-level (ancestor) loggers.
    # This is generally okay if you are configuring the root logger,
    # but be aware of this if you have multiple loggers in your application.
    # logger.propagate= False
    if console_output:
        _add_console_handler(logger, log_level_console)
    if file_output:
        _add_file_handler(logger, log_level_file, log_file_path)
