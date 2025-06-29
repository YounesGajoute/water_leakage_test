"""
Input validation utilities
"""
import re
from typing import Tuple, Any, Dict, Optional

class ValidationUtils:
    """Utility class for input validation"""
    
    # Validation ranges
    RANGES = {
        'position': {'min': 65, 'max': 200, 'unit': 'mm'},
        'pressure': {'min': 0, 'max': 4.5, 'unit': 'bar'},
        'time': {'min': 0, 'max': 120, 'unit': 'min'},
        'frequency': {'min': 1, 'max': 50, 'unit': 'Hz'}
    }
    
    @staticmethod
    def validate_reference_id(ref_id: str) -> Tuple[bool, str]:
        """
        Validate reference ID format
        
        Args:
            ref_id: Reference ID to validate
            
        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        if not ref_id or not isinstance(ref_id, str):
            return False, "Reference ID cannot be empty"
        
        # Remove whitespace
        ref_id = ref_id.strip()
        
        if len(ref_id) < 1:
            return False, "Reference ID cannot be empty"
        
        if len(ref_id) > 20:
            return False, "Reference ID must be 20 characters or less"
        
        # Check for valid characters (alphanumeric and underscore)
        if not re.match(r'^[a-zA-Z0-9_]+$', ref_id):
            return False, "Reference ID can only contain letters, numbers, and underscores"
        
        return True, ""
    
    @staticmethod
    def validate_numeric_input(value: Any, param_type: str) -> Tuple[bool, str, Optional[float]]:
        """
        Validate numeric input with range checking
        
        Args:
            value: Input value to validate
            param_type: Type of parameter ('position', 'pressure', 'time', 'frequency')
            
        Returns:
            Tuple[bool, str, float]: (is_valid, error_message, converted_value)
        """
        # Check if parameter type is supported
        if param_type not in ValidationUtils.RANGES:
            return False, f"Unknown parameter type: {param_type}", None
        
        # Convert to string and strip whitespace
        if value is None:
            return False, f"{param_type.capitalize()} cannot be empty", None
        
        value_str = str(value).strip()
        
        if not value_str:
            return False, f"{param_type.capitalize()} cannot be empty", None
        
        # Try to convert to float
        try:
            numeric_value = float(value_str)
        except ValueError:
            return False, f"{param_type.capitalize()} must be a valid number", None
        
        # Check range
        range_info = ValidationUtils.RANGES[param_type]
        min_val = range_info['min']
        max_val = range_info['max']
        unit = range_info['unit']
        
        if numeric_value < min_val:
            return False, f"{param_type.capitalize()} must be at least {min_val} {unit}", None
        
        if numeric_value > max_val:
            return False, f"{param_type.capitalize()} must be at most {max_val} {unit}", None
        
        return True, "", numeric_value
    
    @staticmethod
    def validate_reference_data(ref_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validate complete reference data structure
        
        Args:
            ref_data: Reference data dictionary
            
        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        try:
            # Check required structure
            if not isinstance(ref_data, dict):
                return False, "Reference data must be a dictionary"
            
            if 'parameters' not in ref_data:
                return False, "Reference data must contain 'parameters' section"
            
            parameters = ref_data['parameters']
            if not isinstance(parameters, dict):
                return False, "Parameters must be a dictionary"
            
            # Required parameters
            required_params = ['position', 'target_pressure', 'inspection_time']
            
            for param in required_params:
                if param not in parameters:
                    return False, f"Missing required parameter: {param}"
            
            # Validate each parameter
            param_mapping = {
                'position': 'position',
                'target_pressure': 'pressure',
                'inspection_time': 'time'
            }
            
            for param_key, validation_type in param_mapping.items():
                value = parameters[param_key]
                is_valid, error_msg, _ = ValidationUtils.validate_numeric_input(value, validation_type)
                
                if not is_valid:
                    return False, f"{param_key}: {error_msg}"
            
            return True, ""
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    @staticmethod
    def validate_password(password: str, min_length: int = 6) -> Tuple[bool, str]:
        """
        Validate password strength
        
        Args:
            password: Password to validate
            min_length: Minimum password length
            
        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        if not password:
            return False, "Password cannot be empty"
        
        if len(password) < min_length:
            return False, f"Password must be at least {min_length} characters long"
        
        # Check for at least one letter and one number
        has_letter = any(c.isalpha() for c in password)
        has_number = any(c.isdigit() for c in password)
        
        if not has_letter:
            return False, "Password must contain at least one letter"
        
        if not has_number:
            return False, "Password must contain at least one number"
        
        return True, ""
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitize filename for safe file operations
        
        Args:
            filename: Original filename
            
        Returns:
            str: Sanitized filename
        """
        # Remove or replace invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
        # Remove leading/trailing whitespace and dots
        filename = filename.strip(' .')
        
        # Limit length
        if len(filename) > 255:
            filename = filename[:255]
        
        # Ensure not empty
        if not filename:
            filename = "untitled"
        
        return filename
    
    @staticmethod
    def validate_json_data(data: str) -> Tuple[bool, str, Optional[Dict]]:
        """
        Validate JSON data format
        
        Args:
            data: JSON string to validate
            
        Returns:
            Tuple[bool, str, dict]: (is_valid, error_message, parsed_data)
        """
        try:
            import json
            parsed_data = json.loads(data)
            return True, "", parsed_data
        except json.JSONDecodeError as e:
            return False, f"Invalid JSON format: {str(e)}", None
        except Exception as e:
            return False, f"JSON validation error: {str(e)}", None
    
    @staticmethod
    def validate_ip_address(ip: str) -> Tuple[bool, str]:
        """
        Validate IP address format
        
        Args:
            ip: IP address string
            
        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        try:
            import socket
            socket.inet_aton(ip)
            parts = ip.split('.')
            if len(parts) != 4:
                return False, "IP address must have 4 parts"
            
            for part in parts:
                if not 0 <= int(part) <= 255:
                    return False, "IP address parts must be between 0 and 255"
            
            return True, ""
            
        except socket.error:
            return False, "Invalid IP address format"
        except ValueError:
            return False, "IP address parts must be numeric"
    
    @staticmethod
    def validate_port(port: Any) -> Tuple[bool, str, Optional[int]]:
        """
        Validate network port number
        
        Args:
            port: Port number to validate
            
        Returns:
            Tuple[bool, str, int]: (is_valid, error_message, port_number)
        """
        try:
            port_num = int(port)
            if not 1 <= port_num <= 65535:
                return False, "Port must be between 1 and 65535", None
            return True, "", port_num
        except (ValueError, TypeError):
            return False, "Port must be a valid number", None
    
    @staticmethod
    def validate_file_path(file_path: str, must_exist: bool = False) -> Tuple[bool, str]:
        """
        Validate file path
        
        Args:
            file_path: File path to validate
            must_exist: Whether file must already exist
            
        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        import os
        
        if not file_path:
            return False, "File path cannot be empty"
        
        if must_exist and not os.path.exists(file_path):
            return False, "File does not exist"
        
        # Check if parent directory exists (for new files)
        if not must_exist:
            parent_dir = os.path.dirname(file_path)
            if parent_dir and not os.path.exists(parent_dir):
                return False, "Parent directory does not exist"
        
        # Check for invalid characters in filename
        filename = os.path.basename(file_path)
        if not filename:
            return False, "Invalid filename"
        
        sanitized = ValidationUtils.sanitize_filename(filename)
        if sanitized != filename:
            return False, "Filename contains invalid characters"
        
        return True, ""
    
    @staticmethod
    def format_validation_error(field_name: str, error_message: str) -> str:
        """
        Format validation error message
        
        Args:
            field_name: Name of the field with error
            error_message: Error message
            
        Returns:
            str: Formatted error message
        """
        return f"{field_name}: {error_message}"
    
    @staticmethod
    def get_validation_ranges() -> Dict[str, Dict[str, Any]]:
        """
        Get all validation ranges
        
        Returns:
            Dict: Validation ranges for all parameters
        """
        return ValidationUtils.RANGES.copy()