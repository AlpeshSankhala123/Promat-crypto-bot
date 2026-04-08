import logging
from datetime import datetime
from config import LOG_FILE

def setup_logger():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def log_trade(signal, entry, sl, tp, confidence, reason):
    logger = setup_logger()
    logger.info(f"TRADE | Signal: {signal} | Entry: {entry} | SL: {sl} | TP: {tp} | Confidence: {confidence}% | Reason: {reason}")