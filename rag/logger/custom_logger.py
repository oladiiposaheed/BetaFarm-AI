"""
FILE: logger/custom_logger.py
PURPOSE: Simple logger for BetaFarm AI

Logs to both file and console with timestamps.
"""

import sys
import logging
from datetime import datetime
import os


class CustomLogger:
    """Simple logger that writes to both file and console."""
    
    def __init__(self, name='betafarm_rag', log_dir='logs'):
        """
        Initialize the logger.
        
        ARGS:
            name: Name of the logger (appears in logs)
            log_dir: Directory to store log files
        """
        # Store name and log_dir FIRST (this was missing!)
        self.name = name
        self.log_dir = log_dir
        
        # Create logs directory if it doesn't exist
        try:
            os.makedirs(log_dir, exist_ok=True)
        except Exception:
            # If can't create directory, use current directory
            self.log_dir = '.'
        
        # Create log file name with date
        date_str = datetime.now().strftime('%Y-%m-%d')
        self.log_file = os.path.join(self.log_dir, f'{date_str}.log')
        
        # Set up the logger
        self.logger = self._setup_logger()
    
    def _setup_logger(self):
        """Set up the logger with file and console handlers."""
        
        # Create logger
        logger = logging.getLogger(self.name)
        logger.setLevel(logging.DEBUG)
        
        # Clear any existing handlers (avoid duplicates)
        if logger.hasHandlers():
            logger.handlers.clear()
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # File handler (saves to disk)
        try:
            file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception:
            pass  # Skip file logging if it fails
        
        # Console handler (prints to terminal)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        return logger


# Function to get a logger
def get_logger(name=None):
    """Get a logger instance."""
    if name is None:
        name = 'betafarm_rag'
    return CustomLogger(name)


# Default logger instance
logger = get_logger()


if __name__ == "__main__":
    print("=" * 60)
    print("TESTING SIMPLE LOGGER")
    print("=" * 60)
    
    # Create a test logger
    test_logger = get_logger("test")
    
    # Test 1: Info log
    print("\n1. INFO log:")
    test_logger.logger.info("Application started")
    
    # Test 2: Info with extra fields
    print("\n2. INFO with extra fields:")
    test_logger.logger.info("User request - user_id=07012345678, language=yo")
    
    # Test 7: Show log file
    print("\n7. Log file location:")
    print(f"   {test_logger.log_file}")
    
    print("\n" + "=" * 60)
    print("✅ LOGGER TEST COMPLETE")
    print("=" * 60)