# app/date_utils.py
from datetime import datetime
import jdatetime

def gregorian_to_shamsi(gregorian_date):
    """
    Convert Gregorian date to Shamsi (Persian) date using jdatetime library.
    
    Args:
        gregorian_date: ISO format date string (YYYY-MM-DD or with time component)
        
    Returns:
        Shamsi date string in format YYYY/MM/DD
    """
    try:
        # Handle different date formats
        if isinstance(gregorian_date, str):
            if 'T' in gregorian_date:
                # Handle ISO format with time component
                gregorian_date = gregorian_date.split('T')[0]
            
            # Parse the date string
            date_obj = datetime.strptime(gregorian_date, "%Y-%m-%d")
        elif isinstance(gregorian_date, datetime):
            date_obj = gregorian_date
        else:
            return str(gregorian_date)
        
        # Convert to Jalali (Shamsi) date
        jalali_date = jdatetime.date.fromgregorian(date=date_obj.date())
        
        # Format as YYYY/MM/DD
        return jalali_date.strftime("%Y/%m/%d")
    except Exception as e:
        print(f"Error converting date: {e}")
        # Return the original date if conversion fails
        return str(gregorian_date)

def get_current_shamsi_date():
    """Get the current date in Shamsi format"""
    return jdatetime.datetime.now().strftime("%Y/%m/%d")

def format_date_shamsi(date_string):
    """
    Format a date string to Shamsi format using jdatetime.
    Handles ISO format strings and extracts the date part.
    
    Args:
        date_string: Date string in any format
        
    Returns:
        Formatted Shamsi date or original string if conversion fails
    """
    try:
        if isinstance(date_string, str):
            return gregorian_to_shamsi(date_string)
        else:
            return gregorian_to_shamsi(date_string)
    except Exception as e:
        print(f"Error formatting date: {e}")
        # Return original if there's an error
        return str(date_string)