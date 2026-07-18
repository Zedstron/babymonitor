import sys
import logging
from colorlog import ColoredFormatter

formatter = ColoredFormatter(
    '%(log_color)s[%(levelname)s] %(asctime)s %(message)s%(reset)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    log_colors={
        'INFO': 'cyan',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'DEBUG': 'green',
    }
)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

console_handler = logging.StreamHandler(sys.stderr)
console_handler.setFormatter(formatter)

file_handler = logging.FileHandler("logs.txt", encoding="utf-8")
file_formatter = logging.Formatter(
    '[%(levelname)s] %(asctime)s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
file_handler.setFormatter(file_formatter)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

logger.addHandler(console_handler)
logger.addHandler(file_handler)