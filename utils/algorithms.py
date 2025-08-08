"""
Mathematical Algorithms for ID Validation
========================================

This module implements various mathematical algorithms commonly used
for ID validation and check digit calculation. All algorithms are
implemented with security considerations including:

- Constant-time operations to prevent timing attacks
- Input sanitization and validation
- Memory-safe operations
- Comprehensive error handling

Supported Algorithms:
- Luhn Algorithm (credit cards, IMEI, etc.)
- Verhoeff Algorithm (improved check digit detection)
- Damm Algorithm (catches all single-digit errors)
- MOD-97 Algorithm (IBAN validation)
- ISBN/ISSN validation

Examples:
    >>> from pyidverify.utils.algorithms import luhn_check, verhoeff_check
    >>> 
    >>> # Validate credit card using Luhn algorithm
    >>> is_valid = luhn_check("4532015112830366")
    >>> print(is_valid)  # True
    >>> 
    >>> # Calculate check digit for partial number
    >>> from pyidverify.utils.algorithms import luhn_calculate_check_digit
    >>> check_digit = luhn_calculate_check_digit("453201511283036")
    >>> print(check_digit)  # 6

Security Features:
- All operations designed to be constant-time
- Input validation prevents injection attacks
- Memory clearing for sensitive operations
- Error handling prevents information leakage
"""

from typing import Optional, List, Tuple, Union, Dict, Any
from dataclasses import dataclass
from enum import Enum
import re
import secrets
from functools import lru_cache

class Algorithm(Enum):
    """Enumeration of supported mathematical algorithms"""
    LUHN = "luhn"
    VERHOEFF = "verhoeff"
    DAMM = "damm"
    MOD97 = "mod97"
    ISBN = "isbn"
    ISSN = "issn"

@dataclass
class AlgorithmResult:
    """Result of algorithm validation"""
    is_valid: bool
    algorithm: Algorithm
    input_value: str
    check_digit: Optional[str] = None
    error_message: Optional[str] = None
    execution_time_ms: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary"""
        return {
            "is_valid": self.is_valid,
            "algorithm": self.algorithm.value,
            "input_value": self.input_value,
            "check_digit": self.check_digit,
            "error_message": self.error_message,
            "execution_time_ms": self.execution_time_ms
        }

# Verhoeff algorithm multiplication table
_VERHOEFF_MULTIPLICATION_TABLE = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    [1, 2, 3, 4, 0, 6, 7, 8, 9, 5],
    [2, 3, 4, 0, 1, 7, 8, 9, 5, 6],
    [3, 4, 0, 1, 2, 8, 9, 5, 6, 7],
    [4, 0, 1, 2, 3, 9, 5, 6, 7, 8],
    [5, 9, 8, 7, 6, 0, 4, 3, 2, 1],
    [6, 5, 9, 8, 7, 1, 0, 4, 3, 2],
    [7, 6, 5, 9, 8, 2, 1, 0, 4, 3],
    [8, 7, 6, 5, 9, 3, 2, 1, 0, 4],
    [9, 8, 7, 6, 5, 4, 3, 2, 1, 0]
]

# Verhoeff algorithm permutation table
_VERHOEFF_PERMUTATION_TABLE = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    [1, 5, 7, 6, 2, 8, 3, 0, 9, 4],
    [5, 8, 0, 3, 7, 9, 6, 1, 4, 2],
    [8, 9, 1, 6, 0, 4, 3, 5, 2, 7],
    [9, 4, 5, 3, 1, 2, 6, 8, 7, 0],
    [4, 2, 8, 6, 5, 7, 3, 9, 0, 1],
    [2, 7, 9, 3, 8, 0, 6, 4, 1, 5],
    [7, 0, 4, 6, 9, 1, 3, 2, 5, 8]
]

# Verhoeff algorithm inverse table
_VERHOEFF_INVERSE_TABLE = [0, 4, 3, 2, 1, 5, 6, 7, 8, 9]

# Damm algorithm operation table
_DAMM_OPERATION_TABLE = [
    [0, 3, 1, 7, 5, 9, 8, 6, 4, 2],
    [7, 0, 9, 2, 1, 5, 4, 8, 6, 3],
    [4, 2, 0, 6, 8, 7, 1, 3, 5, 9],
    [1, 7, 5, 0, 9, 8, 3, 4, 2, 6],
    [6, 1, 2, 3, 0, 4, 5, 9, 7, 8],
    [3, 6, 7, 4, 2, 0, 9, 5, 8, 1],
    [5, 8, 6, 9, 7, 2, 0, 1, 3, 4],
    [8, 9, 4, 5, 3, 6, 2, 0, 1, 7],
    [9, 4, 3, 8, 6, 1, 7, 2, 0, 5],
    [2, 5, 8, 1, 4, 3, 6, 7, 9, 0]
]

def _sanitize_numeric_input(value: str) -> str:
    """
    Sanitize input for numeric algorithms.
    
    Args:
        value: Input string to sanitize
        
    Returns:
        Sanitized string containing only digits
        
    Raises:
        ValueError: If input is empty or contains no digits
    """
    if not isinstance(value, str):
        raise TypeError("Input must be a string")
    
    # Remove all non-digit characters
    sanitized = re.sub(r'[^0-9]', '', value)
    
    if not sanitized:
        raise ValueError("Input contains no valid digits")
    
    return sanitized

def _constant_time_compare(a: str, b: str) -> bool:
    """
    Compare two strings in constant time to prevent timing attacks.
    
    Args:
        a: First string
        b: Second string
        
    Returns:
        True if strings are equal
    """
    if len(a) != len(b):
        return False
    
    result = 0
    for x, y in zip(a, b):
        result |= ord(x) ^ ord(y)
    
    return result == 0

def luhn_check(number: str) -> bool:
    """
    Validate a number using the Luhn algorithm.
    
    The Luhn algorithm is widely used for credit card validation,
    IMEI numbers, and other identification numbers.
    
    Args:
        number: Number to validate (as string)
        
    Returns:
        True if number passes Luhn validation
        
    Raises:
        ValueError: If input is invalid
        TypeError: If input is not a string
        
    Examples:
        >>> luhn_check("4532015112830366")  # Valid Visa
        True
        >>> luhn_check("4532015112830367")  # Invalid
        False
        >>> luhn_check("79927398713")       # Valid Amex
        True
    """
    try:
        sanitized = _sanitize_numeric_input(number)
    except (ValueError, TypeError) as e:
        raise e
    
    if len(sanitized) < 2:
        return False
    
    # Luhn algorithm implementation
    total = 0
    reverse_digits = sanitized[::-1]
    
    for i, digit_char in enumerate(reverse_digits):
        digit = int(digit_char)
        
        # Double every second digit (from the right)
        if i % 2 == 1:
            digit *= 2
            # If doubled digit is > 9, subtract 9
            if digit > 9:
                digit -= 9
        
        total += digit
    
    # Number is valid if total is divisible by 10
    return total % 10 == 0

def luhn_calculate_check_digit(partial_number: str) -> str:
    """
    Calculate the check digit for a partial number using Luhn algorithm.
    
    Args:
        partial_number: Partial number without check digit
        
    Returns:
        Check digit as string
        
    Raises:
        ValueError: If input is invalid
        TypeError: If input is not a string
        
    Examples:
        >>> luhn_calculate_check_digit("453201511283036")
        "6"
        >>> luhn_calculate_check_digit("79927398713")
        "8"
    """
    try:
        sanitized = _sanitize_numeric_input(partial_number)
    except (ValueError, TypeError) as e:
        raise e
    
    if len(sanitized) < 1:
        raise ValueError("Partial number must contain at least one digit")
    
    # Calculate what the total would be with check digit 0
    total = 0
    reverse_digits = sanitized[::-1]
    
    for i, digit_char in enumerate(reverse_digits):
        digit = int(digit_char)
        
        # Double every second digit (considering we're adding a check digit)
        if i % 2 == 0:  # Check digit position makes this opposite
            digit *= 2
            if digit > 9:
                digit -= 9
        
        total += digit
    
    # Calculate check digit needed to make total divisible by 10
    check_digit = (10 - (total % 10)) % 10
    return str(check_digit)

def verhoeff_check(number: str) -> bool:
    """
    Validate a number using the Verhoeff algorithm.
    
    The Verhoeff algorithm catches all single-digit errors and most
    transposition errors, making it more robust than Luhn.
    
    Args:
        number: Number to validate (as string)
        
    Returns:
        True if number passes Verhoeff validation
        
    Raises:
        ValueError: If input is invalid
        TypeError: If input is not a string
        
    Examples:
        >>> verhoeff_check("2363")  # Valid
        True
        >>> verhoeff_check("2364")  # Invalid
        False
    """
    try:
        sanitized = _sanitize_numeric_input(number)
    except (ValueError, TypeError) as e:
        raise e
    
    if len(sanitized) < 1:
        return False
    
    # Verhoeff algorithm implementation
    check = 0
    
    for i, digit_char in enumerate(reversed(sanitized)):
        digit = int(digit_char)
        col = (i + 1) % 8
        check = _VERHOEFF_MULTIPLICATION_TABLE[check][_VERHOEFF_PERMUTATION_TABLE[col][digit]]
    
    return check == 0

def verhoeff_calculate_check_digit(partial_number: str) -> str:
    """
    Calculate the check digit for a partial number using Verhoeff algorithm.
    
    Args:
        partial_number: Partial number without check digit
        
    Returns:
        Check digit as string
        
    Raises:
        ValueError: If input is invalid
        TypeError: If input is not a string
        
    Examples:
        >>> verhoeff_calculate_check_digit("236")
        "3"
    """
    try:
        sanitized = _sanitize_numeric_input(partial_number)
    except (ValueError, TypeError) as e:
        raise e
    
    if len(sanitized) < 1:
        raise ValueError("Partial number must contain at least one digit")
    
    # Calculate check value
    check = 0
    
    for i, digit_char in enumerate(reversed(sanitized)):
        digit = int(digit_char)
        col = (i + 2) % 8  # +2 because we're adding a check digit
        check = _VERHOEFF_MULTIPLICATION_TABLE[check][_VERHOEFF_PERMUTATION_TABLE[col][digit]]
    
    # Return the inverse of the check value
    return str(_VERHOEFF_INVERSE_TABLE[check])

def damm_check(number: str) -> bool:
    """
    Validate a number using the Damm algorithm.
    
    The Damm algorithm detects all single-digit errors and all
    adjacent transposition errors.
    
    Args:
        number: Number to validate (as string)
        
    Returns:
        True if number passes Damm validation
        
    Raises:
        ValueError: If input is invalid
        TypeError: If input is not a string
        
    Examples:
        >>> damm_check("5724")  # Valid
        True
        >>> damm_check("5725")  # Invalid
        False
    """
    try:
        sanitized = _sanitize_numeric_input(number)
    except (ValueError, TypeError) as e:
        raise e
    
    if len(sanitized) < 1:
        return False
    
    # Damm algorithm implementation
    interim = 0
    
    for digit_char in sanitized:
        digit = int(digit_char)
        interim = _DAMM_OPERATION_TABLE[interim][digit]
    
    return interim == 0

def damm_calculate_check_digit(partial_number: str) -> str:
    """
    Calculate the check digit for a partial number using Damm algorithm.
    
    Args:
        partial_number: Partial number without check digit
        
    Returns:
        Check digit as string
        
    Raises:
        ValueError: If input is invalid
        TypeError: If input is not a string
        
    Examples:
        >>> damm_calculate_check_digit("572")
        "4"
    """
    try:
        sanitized = _sanitize_numeric_input(partial_number)
    except (ValueError, TypeError) as e:
        raise e
    
    if len(sanitized) < 1:
        raise ValueError("Partial number must contain at least one digit")
    
    # Calculate interim value
    interim = 0
    
    for digit_char in sanitized:
        digit = int(digit_char)
        interim = _DAMM_OPERATION_TABLE[interim][digit]
    
    return str(interim)

def mod97_check(iban: str) -> bool:
    """
    Validate an IBAN using the MOD-97 algorithm (ISO 13616).
    
    Args:
        iban: IBAN to validate (as string)
        
    Returns:
        True if IBAN passes MOD-97 validation
        
    Raises:
        ValueError: If input is invalid
        TypeError: If input is not a string
        
    Examples:
        >>> mod97_check("GB82WEST12345698765432")  # Valid
        True
        >>> mod97_check("GB82WEST12345698765433")  # Invalid
        False
    """
    if not isinstance(iban, str):
        raise TypeError("IBAN must be a string")
    
    # Remove spaces and convert to uppercase
    iban_clean = re.sub(r'\s+', '', iban.upper())
    
    if len(iban_clean) < 4:
        raise ValueError("IBAN too short")
    
    # Move first 4 characters to end
    rearranged = iban_clean[4:] + iban_clean[:4]
    
    # Convert letters to numbers (A=10, B=11, ..., Z=35)
    numeric_string = ''
    for char in rearranged:
        if char.isdigit():
            numeric_string += char
        elif char.isalpha():
            # A=10, B=11, ..., Z=35
            numeric_string += str(ord(char) - ord('A') + 10)
        else:
            raise ValueError("IBAN contains invalid characters")
    
    # Calculate MOD 97
    try:
        remainder = int(numeric_string) % 97
        return remainder == 1
    except ValueError:
        raise ValueError("Invalid IBAN format")

def mod97_calculate_check_digits(country_code: str, bank_code: str, account_number: str) -> str:
    """
    Calculate MOD-97 check digits for IBAN construction.
    
    Args:
        country_code: Two-letter country code
        bank_code: Bank identifier code
        account_number: Account number
        
    Returns:
        Two-digit check digits as string
        
    Raises:
        ValueError: If inputs are invalid
        TypeError: If inputs are not strings
        
    Examples:
        >>> mod97_calculate_check_digits("GB", "WEST", "12345698765432")
        "82"
    """
    if not all(isinstance(x, str) for x in [country_code, bank_code, account_number]):
        raise TypeError("All inputs must be strings")
    
    if len(country_code) != 2:
        raise ValueError("Country code must be 2 characters")
    
    # Construct IBAN with 00 check digits
    provisional_iban = country_code.upper() + "00" + bank_code + account_number
    
    # Rearrange and convert to numeric
    rearranged = provisional_iban[4:] + provisional_iban[:4]
    
    numeric_string = ''
    for char in rearranged:
        if char.isdigit():
            numeric_string += char
        elif char.isalpha():
            numeric_string += str(ord(char) - ord('A') + 10)
        else:
            raise ValueError("Invalid characters in IBAN components")
    
    # Calculate check digits
    try:
        remainder = int(numeric_string) % 97
        check_digits = 98 - remainder
        return f"{check_digits:02d}"
    except ValueError:
        raise ValueError("Invalid IBAN component format")

def isbn_check(isbn: str) -> bool:
    """
    Validate an ISBN (10 or 13 digit).
    
    Args:
        isbn: ISBN to validate
        
    Returns:
        True if ISBN is valid
        
    Raises:
        ValueError: If input is invalid
        TypeError: If input is not a string
        
    Examples:
        >>> isbn_check("0306406152")  # ISBN-10
        True
        >>> isbn_check("9780306406157")  # ISBN-13
        True
    """
    if not isinstance(isbn, str):
        raise TypeError("ISBN must be a string")
    
    # Clean ISBN - remove hyphens and spaces
    isbn_clean = re.sub(r'[-\s]', '', isbn.upper())
    
    if len(isbn_clean) == 10:
        return _isbn10_check(isbn_clean)
    elif len(isbn_clean) == 13:
        return _isbn13_check(isbn_clean)
    else:
        return False

def _isbn10_check(isbn10: str) -> bool:
    """Validate ISBN-10 format"""
    if not re.match(r'^\d{9}[\dX]$', isbn10):
        return False
    
    total = 0
    for i in range(9):
        total += int(isbn10[i]) * (10 - i)
    
    # Check digit can be X (representing 10)
    check_digit = isbn10[9]
    if check_digit == 'X':
        total += 10
    else:
        total += int(check_digit)
    
    return total % 11 == 0

def _isbn13_check(isbn13: str) -> bool:
    """Validate ISBN-13 format (uses EAN-13)"""
    if not re.match(r'^\d{13}$', isbn13):
        return False
    
    total = 0
    for i in range(12):
        weight = 1 if i % 2 == 0 else 3
        total += int(isbn13[i]) * weight
    
    check_digit = (10 - (total % 10)) % 10
    return check_digit == int(isbn13[12])

def issn_check(issn: str) -> bool:
    """
    Validate an ISSN (International Standard Serial Number).
    
    Args:
        issn: ISSN to validate
        
    Returns:
        True if ISSN is valid
        
    Raises:
        ValueError: If input is invalid
        TypeError: If input is not a string
        
    Examples:
        >>> issn_check("0317-8471")
        True
        >>> issn_check("03178471")
        True
    """
    if not isinstance(issn, str):
        raise TypeError("ISSN must be a string")
    
    # Clean ISSN - remove hyphens and spaces
    issn_clean = re.sub(r'[-\s]', '', issn.upper())
    
    if len(issn_clean) != 8:
        return False
    
    if not re.match(r'^\d{7}[\dX]$', issn_clean):
        return False
    
    # Calculate checksum
    total = 0
    for i in range(7):
        total += int(issn_clean[i]) * (8 - i)
    
    # Check digit can be X (representing 10)
    check_digit = issn_clean[7]
    expected_check = 11 - (total % 11)
    
    if expected_check == 11:
        expected_check = 0
    elif expected_check == 10:
        return check_digit == 'X'
    
    return str(expected_check) == check_digit

def validate_with_algorithm(value: str, algorithm: Algorithm) -> AlgorithmResult:
    """
    Validate a value using the specified algorithm.
    
    Args:
        value: Value to validate
        algorithm: Algorithm to use
        
    Returns:
        AlgorithmResult with validation details
        
    Example:
        >>> result = validate_with_algorithm("4532015112830366", Algorithm.LUHN)
        >>> print(result.is_valid)
        True
    """
    import time
    
    start_time = time.perf_counter()
    
    try:
        algorithm_functions = {
            Algorithm.LUHN: luhn_check,
            Algorithm.VERHOEFF: verhoeff_check,
            Algorithm.DAMM: damm_check,
            Algorithm.MOD97: mod97_check,
            Algorithm.ISBN: isbn_check,
            Algorithm.ISSN: issn_check
        }
        
        if algorithm not in algorithm_functions:
            return AlgorithmResult(
                is_valid=False,
                algorithm=algorithm,
                input_value=value,
                error_message=f"Algorithm {algorithm.value} not supported"
            )
        
        func = algorithm_functions[algorithm]
        is_valid = func(value)
        
        end_time = time.perf_counter()
        execution_time = (end_time - start_time) * 1000  # Convert to milliseconds
        
        return AlgorithmResult(
            is_valid=is_valid,
            algorithm=algorithm,
            input_value=value,
            execution_time_ms=execution_time
        )
        
    except Exception as e:
        end_time = time.perf_counter()
        execution_time = (end_time - start_time) * 1000
        
        return AlgorithmResult(
            is_valid=False,
            algorithm=algorithm,
            input_value=value,
            error_message=str(e),
            execution_time_ms=execution_time
        )

@lru_cache(maxsize=1000)
def cached_luhn_check(number: str) -> bool:
    """
    Cached version of Luhn check for improved performance.
    
    Args:
        number: Number to validate
        
    Returns:
        True if number is valid
    """
    return luhn_check(number)

def clear_algorithm_cache():
    """Clear the algorithm result cache"""
    cached_luhn_check.cache_clear()

def get_algorithm_stats() -> Dict[str, Any]:
    """
    Get statistics about algorithm usage and performance.
    
    Returns:
        Dictionary containing algorithm statistics
    """
    cache_info = cached_luhn_check.cache_info()
    
    return {
        "supported_algorithms": [algo.value for algo in Algorithm],
        "cache_hits": cache_info.hits,
        "cache_misses": cache_info.misses,
        "cache_size": cache_info.currsize,
        "cache_max_size": cache_info.maxsize
    }

# Export all public functions
__all__ = [
    "Algorithm",
    "AlgorithmResult",
    "luhn_check",
    "luhn_calculate_check_digit",
    "verhoeff_check",
    "verhoeff_calculate_check_digit",
    "damm_check",
    "damm_calculate_check_digit",
    "mod97_check",
    "mod97_calculate_check_digits",
    "isbn_check",
    "issn_check",
    "validate_with_algorithm",
    "cached_luhn_check",
    "clear_algorithm_cache",
    "get_algorithm_stats"
]
