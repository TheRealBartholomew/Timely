"""Input validation utilities (Objective 14)"""
import re
from datetime import time, date

def validate_task_name(name):
    """Validate task name is 1-100 characters"""
    if not isinstance(name, str):
        return False, "Task name must be a string"
    
    name = name.strip()
    if len(name) < 1 or len(name) > 100:
        return False, "Task name must be 1-100 characters"
    
    return True, name

def validate_scale(value, field_name, min_val=1, max_val=10):
    """Validate integer is within scale (1-10)"""
    try:
        value = int(value)
    except (ValueError, TypeError):
        return False, f"{field_name} must be a number"
    
    if value < min_val or value > max_val:
        return False, f"{field_name} must be between {min_val}-{max_val}"
    
    return True, value

def validate_length(length):
    """Validate task length is positive number"""
    try:
        length = float(length)
    except (ValueError, TypeError):
        return False, "Length must be a number"
    
    if length <= 0:
        return False, "Length must be positive"
    
    if length > 24:
        return False, "Length cannot exceed 24 hours"
    
    return True, length

def validate_email(email):
    """Validate email format"""
    if not isinstance(email, str):
        return False, "Email must be a string"
    
    email = email.strip().lower()
    
    # Basic email regex
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        return False, "Invalid email format"
    
    return True, email

def validate_time(time_str):
    """Validate time string format (HH:MM)"""
    try:
        parts = time_str.split(':')
        if len(parts) != 2:
            return False, "Time must be in HH:MM format"
        
        hour = int(parts[0])
        minute = int(parts[1])
        
        if hour < 0 or hour > 23:
            return False, "Hour must be 0-23"
        if minute < 0 or minute > 59:
            return False, "Minute must be 0-59"
        
        return True, time(hour, minute)
    
    except (ValueError, AttributeError):
        return False, "Invalid time format"

def validate_date(date_str):
    """Validate date string format (YYYY-MM-DD)"""
    try:
        parts = date_str.split('-')
        if len(parts) != 3:
            return False, "Date must be in YYYY-MM-DD format"
        
        year = int(parts[0])
        month = int(parts[1])
        day = int(parts[2])
        
        return True, date(year, month, day)
    
    except (ValueError, AttributeError):
        return False, "Invalid date format"