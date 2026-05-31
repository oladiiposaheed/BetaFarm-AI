"""
FILE: exception/custom_exception.py
PURPOSE: Simple exception that tells you WHERE the error happened

HOW TO USE:
    try:
        something()
    except Exception as e:
        raise BetaFarmException("Something failed", e)

WHAT YOU SEE:
    Error in [myfile.py] at line [42] | Message: Something failed
    Traceback: (full details)
"""

import sys
import traceback


class BetaFarmException(Exception):
    """
    One simple exception for all your errors.
    Tells you file name, line number, and shows full traceback.
    """
    
    def __init__(self, message="An error occurred", original_error=None):
        """
        Create exception with location info.
        
        Args:
            message: What went wrong (default: "An error occurred")
            original_error: The original exception (optional)
        """
        
        # Save the message
        self.message = str(message)
        
        # Default values (in case we can't find location)
        self.file = "<unknown>"
        self.line = -1
        self.trace = ""
        
        # Get the original error details
        if original_error is None:
            # No error provided - use current one
            error_type, error_value, error_trace = sys.exc_info()
        else:
            # Use the error they gave us
            error_type = type(original_error)
            error_value = original_error
            error_trace = original_error.__traceback__
        
        # Find where the error happened (walk to the last frame)
        if error_trace:
            # Go to the last traceback frame
            last = error_trace
            while last and last.tb_next:
                last = last.tb_next
            
            # Get file name and line number
            self.file = last.tb_frame.f_code.co_filename
            self.line = last.tb_lineno
            
            # Get full traceback for debugging
            self.trace = ''.join(traceback.format_exception(error_type, error_value, error_trace))
        
        # Call parent constructor
        super().__init__(self.message)
    
    def __str__(self):
        """What you see when you print the exception."""
        result = f"Error in [{self.file}] at line [{self.line}] | Message: {self.message}"
        
        if self.trace:
            result = f"{result}\nTraceback:\n{self.trace}"
        
        return result


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("TESTING THE EXCEPTION")
    print("=" * 60)
    
    # Test 1: Simple exception (no original error)
    print("\n1. Simple exception (no traceback):")
    try:
        raise BetaFarmException("Database connection failed")
    except BetaFarmException as e:
        print(e)
    
    # Test 2: Exception with default message
    print("\n2. Exception with default message:")
    try:
        raise BetaFarmException()
    except BetaFarmException as e:
        print(e)
    
    # Test 3: Exception caught from another error (HAS traceback)
    print("\n3. Exception from division by zero (HAS traceback):")
    try:
        x = 1 / 0
    except ZeroDivisionError as e:
        try:
            raise BetaFarmException("Cannot divide by zero", e)
        except BetaFarmException as e2:
            print(e2)