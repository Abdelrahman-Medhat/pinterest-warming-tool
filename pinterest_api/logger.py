import logging
import os
import json
from datetime import datetime
from typing import Optional, Any, Dict
import requests

class PinterestLogger:
    """Logger class for Pinterest API operations."""
    
    def __init__(self, email: str):
        """Initialize logger for a specific account.
        
        Args:
            email (str): Account email for identifying log files
        """
        self.email = email
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        """Set up the logger with file handler.
        
        Returns:
            logging.Logger: Configured logger instance
        """
        # Create logs directory if it doesn't exist
        os.makedirs("logs", exist_ok=True)
        
        # Create a subdirectory for today's date
        today = datetime.now().strftime("%Y-%m-%d")
        date_dir = os.path.join("logs", today)
        os.makedirs(date_dir, exist_ok=True)
        
        # Create email-specific directory
        clean_email = self.email.replace('@', '_at_').replace('.', '_')
        email_dir = os.path.join(date_dir, clean_email)
        os.makedirs(email_dir, exist_ok=True)
        
        # Create a unique log file for this run
        timestamp = datetime.now().strftime("%H%M%S")
        log_file = os.path.join(email_dir, f"pinterest_{timestamp}.log")
        
        # Create logger
        logger = logging.getLogger(f"pinterest_api_{clean_email}")
        logger.setLevel(logging.DEBUG)
        
        # Prevent duplicate handlers
        if not logger.handlers:
            # Create file handler
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.DEBUG)
            
            # Create inline formatter
            formatter = logging.Formatter(
                '%(asctime)s [%(levelname)s] %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(formatter)
            
            # Add handler to logger
            logger.addHandler(file_handler)
        
        return logger
    
    def _format_dict(self, data: Dict[str, Any]) -> str:
        """Format dictionary for inline logging."""
        try:
            return json.dumps(data, separators=(',', ':'))
        except:
            return str(data)
    
    def log_request(self, method: str, url: str, headers: Dict[str, str], data: Any = None, params: Any = None):
        """Log request information inline."""
        req_info = f">>> {method} {url}"
        if params:
            req_info += f" | Params: {self._format_dict(params)}"
        if data:
            req_info += f" | Body: {self._format_dict(data)}"
        req_info += f" | Headers: {self._format_dict(headers)}"
        
        self.debug(f"REQUEST {req_info}")
    
    def log_response(self, response: requests.Response):
        """Log response information inline."""
        resp_info = f"<<< Status: {response.status_code}"
        resp_info += f" | Headers: {self._format_dict(dict(response.headers))}"
        
        # Try to parse response as JSON
        try:
            json_response = response.json()
            resp_info += f" | Body: {self._format_dict(json_response)}"
        except:
            # If not JSON, log raw text (truncated if too long)
            content = response.text[:500]
            if len(response.text) > 500:
                content += "..."
            resp_info += f" | Body: {content}"
        
        self.debug(f"RESPONSE {resp_info}")
    
    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self._log(logging.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message."""
        self._log(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message."""
        self._log(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, error: Optional[Exception] = None, **kwargs):
        """Log error message with optional exception details."""
        if error:
            message = f"{message} (Error: {str(error)})"
        self._log(logging.ERROR, message, **kwargs)
    
    def _log(self, level: int, message: str, **kwargs):
        """Internal method to handle logging with additional context.
        
        Args:
            level: Logging level
            message: Log message
            **kwargs: Additional context to add to log message
        """
        if kwargs:
            context = self._format_dict(kwargs)
            message = f"{message} | Context: {context}"
        self.logger.log(level, message) 