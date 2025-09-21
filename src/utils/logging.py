"""
Logging and monitoring utilities for the AI Timetable Generator.
"""

import logging
import logging.handlers
import os
import json
from datetime import datetime
from flask import request, current_app
from flask_login import current_user
from functools import wraps
import traceback

class DatabaseLogHandler(logging.Handler):
    """Custom log handler that writes to database."""
    
    def emit(self, record):
        """Emit log record to database."""
        try:
            from models.database import SystemLog, db
            
            # Extract user info if available
            user_id = None
            ip_address = None
            user_agent = None
            
            if request:
                ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR'))
                user_agent = request.headers.get('User-Agent')
                
                if current_user and current_user.is_authenticated:
                    user_id = current_user.id
            
            # Prepare additional data
            additional_data = {
                'filename': record.filename,
                'lineno': record.lineno,
                'funcName': record.funcName,
                'thread': record.thread,
                'threadName': record.threadName,
            }
            
            if hasattr(record, 'extra_data'):
                additional_data.update(record.extra_data)
            
            # Create log entry
            log_entry = SystemLog(
                level=record.levelname,
                message=record.getMessage(),
                module=record.module if hasattr(record, 'module') else None,
                function=record.funcName,
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                additional_data=additional_data
            )
            
            db.session.add(log_entry)
            db.session.commit()
            
        except Exception as e:
            # Don't let logging errors crash the app
            print(f"Database logging error: {e}")

def setup_logging(app):
    """Setup application logging."""
    
    # Create logs directory if it doesn't exist
    logs_dir = os.path.join(app.root_path, '..', 'logs')
    os.makedirs(logs_dir, exist_ok=True)
    
    # Configure root logger
    logging.basicConfig(level=logging.INFO)
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s - [%(filename)s:%(lineno)d]'
    )
    
    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # File handler for general logs
    file_handler = logging.handlers.RotatingFileHandler(
        os.path.join(logs_dir, 'app.log'),
        maxBytes=10485760,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(detailed_formatter)
    file_handler.setLevel(logging.INFO)
    
    # File handler for errors
    error_handler = logging.handlers.RotatingFileHandler(
        os.path.join(logs_dir, 'errors.log'),
        maxBytes=10485760,  # 10MB
        backupCount=5
    )
    error_handler.setFormatter(detailed_formatter)
    error_handler.setLevel(logging.ERROR)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(simple_formatter)
    console_handler.setLevel(logging.INFO)
    
    # Database handler
    db_handler = DatabaseLogHandler()
    db_handler.setLevel(logging.WARNING)  # Only log warnings and above to DB
    
    # Add handlers to app logger
    app.logger.addHandler(file_handler)
    app.logger.addHandler(error_handler)
    app.logger.addHandler(console_handler)
    app.logger.addHandler(db_handler)
    app.logger.setLevel(logging.INFO)
    
    # Log startup
    app.logger.info(f"Application started - Environment: {app.config.get('ENV', 'unknown')}")

def log_performance(func):
    """Decorator to log function performance."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = datetime.utcnow()
        try:
            result = func(*args, **kwargs)
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            current_app.logger.info(
                f"Performance: {func.__name__} executed in {duration:.3f}s",
                extra={'extra_data': {
                    'function': func.__name__,
                    'duration_seconds': duration,
                    'args_count': len(args),
                    'kwargs_count': len(kwargs)
                }}
            )
            return result
        except Exception as e:
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            current_app.logger.error(
                f"Performance Error: {func.__name__} failed after {duration:.3f}s - {str(e)}",
                extra={'extra_data': {
                    'function': func.__name__,
                    'duration_seconds': duration,
                    'error': str(e),
                    'traceback': traceback.format_exc()
                }}
            )
            raise
    return wrapper

def log_user_action(action_type, description, **kwargs):
    """Log user actions for audit trail."""
    try:
        user_id = None
        username = 'anonymous'
        
        if current_user and current_user.is_authenticated:
            user_id = current_user.id
            username = current_user.username
        
        extra_data = {
            'action_type': action_type,
            'username': username,
            'timestamp': datetime.utcnow().isoformat(),
            **kwargs
        }
        
        current_app.logger.info(
            f"User Action: {username} - {action_type} - {description}",
            extra={'extra_data': extra_data}
        )
    except Exception as e:
        current_app.logger.error(f"Failed to log user action: {e}")

def log_security_event(event_type, description, severity='INFO', **kwargs):
    """Log security-related events."""
    try:
        ip_address = None
        user_agent = None
        user_id = None
        
        if request:
            ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR'))
            user_agent = request.headers.get('User-Agent')
        
        if current_user and current_user.is_authenticated:
            user_id = current_user.id
        
        extra_data = {
            'event_type': event_type,
            'severity': severity,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'user_id': user_id,
            'timestamp': datetime.utcnow().isoformat(),
            **kwargs
        }
        
        log_method = getattr(current_app.logger, severity.lower(), current_app.logger.info)
        log_method(
            f"Security Event: {event_type} - {description}",
            extra={'extra_data': extra_data}
        )
    except Exception as e:
        current_app.logger.error(f"Failed to log security event: {e}")

def log_api_request(func):
    """Decorator to log API requests."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = datetime.utcnow()
        
        # Log request
        request_data = {
            'method': request.method,
            'url': request.url,
            'endpoint': request.endpoint,
            'remote_addr': request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR')),
            'user_agent': request.headers.get('User-Agent'),
            'user_id': current_user.id if current_user.is_authenticated else None
        }
        
        try:
            result = func(*args, **kwargs)
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            # Log successful response
            current_app.logger.info(
                f"API Request: {request.method} {request.endpoint} - {duration:.3f}s",
                extra={'extra_data': {
                    **request_data,
                    'duration_seconds': duration,
                    'status': 'success'
                }}
            )
            
            return result
            
        except Exception as e:
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            # Log error response
            current_app.logger.error(
                f"API Error: {request.method} {request.endpoint} - {str(e)} - {duration:.3f}s",
                extra={'extra_data': {
                    **request_data,
                    'duration_seconds': duration,
                    'status': 'error',
                    'error': str(e),
                    'traceback': traceback.format_exc()
                }}
            )
            
            raise
    return wrapper

class PerformanceMonitor:
    """Performance monitoring utility."""
    
    def __init__(self):
        self.metrics = {}
    
    def record_metric(self, name, value, tags=None):
        """Record a performance metric."""
        timestamp = datetime.utcnow()
        
        if name not in self.metrics:
            self.metrics[name] = []
        
        self.metrics[name].append({
            'value': value,
            'timestamp': timestamp,
            'tags': tags or {}
        })
        
        # Keep only last 1000 entries per metric
        if len(self.metrics[name]) > 1000:
            self.metrics[name] = self.metrics[name][-1000:]
    
    def get_metric_summary(self, name, minutes=60):
        """Get summary statistics for a metric."""
        if name not in self.metrics:
            return None
        
        # Filter recent entries
        cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)
        recent_entries = [
            entry for entry in self.metrics[name]
            if entry['timestamp'] > cutoff_time
        ]
        
        if not recent_entries:
            return None
        
        values = [entry['value'] for entry in recent_entries]
        
        return {
            'count': len(values),
            'min': min(values),
            'max': max(values),
            'avg': sum(values) / len(values),
            'latest': values[-1],
            'timestamp_range': {
                'start': recent_entries[0]['timestamp'].isoformat(),
                'end': recent_entries[-1]['timestamp'].isoformat()
            }
        }

# Global performance monitor instance
performance_monitor = PerformanceMonitor()

def monitor_timetable_generation(func):
    """Decorator to monitor timetable generation performance."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = datetime.utcnow()
        
        try:
            result = func(*args, **kwargs)
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            # Record metrics
            performance_monitor.record_metric('timetable_generation_duration', duration)
            performance_monitor.record_metric('timetable_generation_success', 1)
            
            # Log detailed performance
            entries_count = len(result.entries) if result and hasattr(result, 'entries') else 0
            conflicts_count = len(result.conflicts) if result and hasattr(result, 'conflicts') else 0
            
            current_app.logger.info(
                f"Timetable Generation: {duration:.3f}s - {entries_count} entries, {conflicts_count} conflicts",
                extra={'extra_data': {
                    'duration_seconds': duration,
                    'entries_count': entries_count,
                    'conflicts_count': conflicts_count,
                    'success': True
                }}
            )
            
            return result
            
        except Exception as e:
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            # Record failure metrics
            performance_monitor.record_metric('timetable_generation_failure', 1)
            
            current_app.logger.error(
                f"Timetable Generation Failed: {duration:.3f}s - {str(e)}",
                extra={'extra_data': {
                    'duration_seconds': duration,
                    'error': str(e),
                    'success': False
                }}
            )
            
            raise
    return wrapper